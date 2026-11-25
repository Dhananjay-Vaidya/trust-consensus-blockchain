"""Command-line entry point: run one oracle-free episode and print its summary.

    python main.py --attack tdp --steps 600 --seed 3
    python main.py --attack nma --nodes 8 --steps 50 --fhe     # CKKS tally (src/crypto/he_tally.py)

The simulation itself is ``src.env.honest_env.HonestEnv`` with a frozen ``RunConfig`` (audit A9).
Committed transactions are appended to a ``Blockchain`` ledger *outside* the environment and mined
every ``--mine-every`` steps; the ledger only records decisions and never feeds back into them, so it
cannot change any result (docs/DECISIONS.md D25).
"""
from __future__ import annotations

import argparse
import logging
import random
import time
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

from src.blockchain.blockchain import Blockchain
from src.config.run_config import ATTACKS, RunConfig
from src.env.honest_env import HonestEnv, StepRecord
from src.metrics.ground_truth_metrics import summarize
from src.utils.logger import get_logger

log = get_logger("main")


def set_global_seed(seed: int) -> None:
    """Seed the global generators. The environment itself uses its own seeded Generators."""
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
    except ImportError:  # torch is only needed by the learning agents, not by this entry point
        return
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run one oracle-free trust-consensus episode.")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING"], default="INFO")
    p.add_argument("--fhe", action="store_true",
                   help="tally votes on CKKS ciphertexts with HETally (needs tenseal) and log its overhead")
    p.add_argument("--attack", choices=ATTACKS, default="tdp")
    p.add_argument("--nodes", type=int, default=16)
    p.add_argument("--steps", type=int, default=600)
    p.add_argument("--t-switch", type=int, default=None, help="TDP activation step (default: steps // 2)")
    p.add_argument("--trust-backend", choices=["sleeper_guard", "legacy_beta", "none"], default="sleeper_guard")
    p.add_argument("--mine-every", type=int, default=5, help="mine pending ledger transactions every N steps")
    p.add_argument("--difficulty", type=int, default=2, help="proof-of-work difficulty of the ledger")
    return p


def make_config(args: argparse.Namespace) -> RunConfig:
    return RunConfig().with_overrides(
        seed=args.seed, num_nodes=args.nodes, committee_size=args.nodes, steps=args.steps,
        t_switch=args.t_switch if args.t_switch is not None else args.steps // 2,
        attack=args.attack, trust_backend=args.trust_backend,
        tally_backend="he" if args.fhe else "plain")


def run(args: argparse.Namespace) -> Dict[str, Any]:
    if args.mine_every < 1:
        raise SystemExit("--mine-every must be >= 1")
    cfg = make_config(args)
    env = HonestEnv(cfg)
    chain = Blockchain(difficulty=args.difficulty)
    he_ms: List[float] = []

    def on_step(rec: StepRecord) -> None:
        for i in np.flatnonzero(rec.accept):
            chain.add_transaction({"sender": f"step{rec.step}", "recipient": "ledger", "amount": 1,
                                   "tx": int(i)})
        if (rec.step + 1) % args.mine_every == 0 and chain.pending_transactions:
            chain.mine_pending_transactions(miner_address="system")
        if args.fhe:
            he_ms.append(rec.he_ms)
            log.debug("step %d: HE tally %.2f ms", rec.step, rec.he_ms)

    env.on_step = on_step
    t0 = time.perf_counter()
    env.run()
    wall_s = time.perf_counter() - t0
    m = summarize(env)
    out: Dict[str, Any] = {
        "seed": cfg.seed, "attack": cfg.attack, "nodes": cfg.num_nodes, "steps": cfg.steps,
        "trust_backend": cfg.trust_backend, "tally_backend": cfg.tally_backend,
        "det_f1": m["det_f1"], "final_f1": m["final_f1"], "det_mcc": m["det_mcc"],
        "invalid_commit_rate": m["invalid_commit_rate"], "valid_reject_rate": m["valid_reject_rate"],
        "confirmed_blocks": len(chain.chain) - 1,        # excludes the genesis block
        "pending_tx_count": len(chain.pending_transactions),
        "chain_valid": chain.is_chain_valid(), "wall_s": wall_s,
        "fhe_enabled": bool(args.fhe),
    }
    if args.fhe:
        out["fhe_avg_overhead_ms"] = float(np.mean(he_ms)) if he_ms else 0.0
        out["fhe_flips"] = m["he_flips"]
    return out


def main(argv: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    args = build_parser().parse_args(argv)
    set_global_seed(args.seed)
    log.setLevel(getattr(logging, args.log_level))
    res = run(args)
    log.info("seed=%d attack=%s nodes=%d steps=%d trust=%s tally=%s", res["seed"], res["attack"],
             res["nodes"], res["steps"], res["trust_backend"], res["tally_backend"])
    log.info("detection F1 (window) %.3f | final-step F1 %.3f | MCC %.3f",
             res["det_f1"], res["final_f1"], res["det_mcc"])
    log.info("invalid commit rate %.4f | valid reject rate %.4f",
             res["invalid_commit_rate"], res["valid_reject_rate"])
    log.info("ledger: %d confirmed blocks, %d pending transactions, chain valid=%s",
             res["confirmed_blocks"], res["pending_tx_count"], res["chain_valid"])
    if res["fhe_enabled"]:
        log.info("FHE overhead: %.2f ms/step average (HETally, CKKS); decisions differing from plaintext: %d",
                 res["fhe_avg_overhead_ms"], res["fhe_flips"])
    log.info("wall time %.1f s", res["wall_s"])
    return res


if __name__ == "__main__":
    main()
