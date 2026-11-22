"""E8: privacy-as-defence (hypothesis H3).

H3: if the trust weights are hidden (encrypted tally), an adaptive briber cannot target the
highest-weight delegates, so bribery is less effective than when weights are public.

Design (paired on seeds): a static colluding coalition (CRA, 3 of 16 nodes) plus an adaptive briber
that, at t_bribe = 300, corrupts B honest nodes, after which they vote with the coalition.
  * condition "plaintext": briber ranks nodes by the last public weights;
  * condition "encrypted": weights hidden; briber ranks by a public-ledger proxy (vote-outcome
    agreement x committee presence);
  * control "random": random targets.
The HE tally is decision-equivalent to the plaintext tally outside the CKKS guard band (E4), so the
"encrypted" condition is simulated with the plaintext backend and weights withheld from the briber
(HE is ~10^3x slower; see DECISIONS D19).  Outcome metrics in the 40-step window after t_bribe:
invalid-commit rate, valid-reject rate, and the bribed nodes' summed weight share at t_bribe.
Trust backends: legacy Beta (unequal weights) and SleeperGuard (capped weights).
"""
from __future__ import annotations

import itertools
import time
from typing import Any, Dict

import numpy as np

from experiments.common import base_parser, out_dir, parse_seeds, run_parallel, write
from experiments.runner import calibrated_sg
from src.config.run_config import RunConfig
from src.env.attacks import AdaptiveBriber
from src.env.honest_env import HonestEnv
from src.metrics.ground_truth_metrics import summarize

WINDOW = 40


def _run(job: Dict[str, Any]) -> Dict[str, Any]:
    cfg = RunConfig().with_overrides(**job["cfg"])
    tg = job["tags"]
    briber = AdaptiveBriber(tg["strategy"], tg["budget"], tg["t_bribe"], [f"Node_{i}" for i in range(cfg.num_nodes)])
    env = HonestEnv(cfg, briber=briber)
    env.run()
    pre = env.records[tg["t_bribe"] - 1]
    share = 0.0
    chosen = set(briber.chosen)
    if pre.weights.sum() > 0:
        com = [env.nodes[i] for i in pre.committee_idx]
        share = float(sum(w for n, w in zip(com, pre.weights) if n in chosen) / pre.weights.sum())
    row = dict(tg, seed=cfg.seed, bribed_weight_share=share)
    m = summarize(env, window_start=tg["t_bribe"], window_end=tg["t_bribe"] + WINDOW)
    row.update({k: m[k] for k in ("invalid_commit_rate", "valid_reject_rate", "abort_rate", "det_f1",
                                  "delay_mean", "delay_censored")})
    row["any_invalid_commit"] = float(m["invalid_commit_rate"] > 0)
    return row


def main() -> None:
    args = base_parser("E8 privacy-as-defence", "100-129").parse_args()
    seeds = parse_seeds(args.seeds)
    steps, t_bribe = 600, 300
    if args.smoke:
        seeds, steps, t_bribe = seeds[:3], 200, 100
    t0 = time.time()
    jobs = []
    for be, budget, strat, s in itertools.product(("legacy_beta", "sleeper_guard"), (2, 3, 4),
                                                  ("weights", "votes", "random"), seeds):
        tb = dict(trust_backend="legacy_beta") if be == "legacy_beta" else calibrated_sg(0.05) | {"trust_backend": "sleeper_guard"}
        jobs.append({"cfg": dict(seed=s, steps=steps, attack="cra", malicious_fraction=0.1875,
                                 committee_size=8, selection_temperature=0.05, **tb),
                     "tags": dict(backend=be, budget=budget, strategy=strat, t_bribe=t_bribe)})
    rows = run_parallel(_run, jobs, args.workers)
    write("e8_privacy", out_dir("e8_privacy", args), rows, args, t0=t0)
    _ = np  # keep numpy import for type checkers


if __name__ == "__main__":
    main()
