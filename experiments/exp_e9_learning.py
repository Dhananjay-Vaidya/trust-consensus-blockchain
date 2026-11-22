"""E9: learning controllers vs a hand-tuned rule vs fixed baselines.

Protocol (A8):
  * train D3P, factored independent learners and tabular Q on TRAIN seeds 0-19 (attack cycled over
    tdp/cra/aaa/nma/bfi/none), `--epochs` passes;
  * tune the rule controller's two thresholds on CALIB seeds 20-29 (grid, objective = mean reward);
  * evaluate every controller FROZEN on EVAL seeds 100-129 for every attack.
All controllers act on the SleeperGuard (calibrated) system; the protocol baselines (PBFT, static
DPoS, majority, random delegates, legacy Beta) run with their fixed configuration.
Objective reported first: mean reward (audited agreement - latency - audit cost; all observable).
Ground-truth metrics are reported alongside but were never visible to any controller.
"""
from __future__ import annotations

import itertools
import time
from typing import Any, Dict, List

import torch

from experiments.common import base_parser, out_dir, parse_seeds, run_parallel, write
from experiments.runner import calibrated_sg, run_one
from src.agents.baselines import BASELINES
from src.agents.d3p import D3PController
from src.agents.factored import FactoredController
from src.agents.protocol import CALIB_SEEDS, TRAIN_SEEDS, Controller, run_episode, train
from src.agents.simple import RuleController, TabularQController
from src.config.run_config import RunConfig
from src.metrics.ground_truth_metrics import summarize

ATTACKS = ("tdp", "cra", "aaa", "nma", "bfi", "none")


def _eval(ctrl: Controller, base: RunConfig, seeds: List[int], name: str) -> List[Dict[str, Any]]:
    rows = []
    for atk, s in itertools.product(ATTACKS, seeds):
        env = run_episode(base.with_overrides(seed=s, attack=atk), ctrl, learn=False)
        r = dict(controller=name, attack=atk, seed=s)
        r.update(summarize(env))
        rows.append(r)
    return rows


def main() -> None:
    p = base_parser("E9 learning vs rules", "100-129")
    p.add_argument("--epochs", type=int, default=3)
    args = p.parse_args()
    torch.set_num_threads(1)
    seeds = parse_seeds(args.seeds)
    steps, train_seeds, calib_seeds, epochs = 600, list(TRAIN_SEEDS), list(CALIB_SEEDS), args.epochs
    if args.smoke:
        seeds, steps, train_seeds, calib_seeds, epochs = seeds[:3], 150, train_seeds[:3], calib_seeds[:2], 1
    t0 = time.time()
    base = RunConfig().with_overrides(steps=steps, t_switch=steps // 2, attack_intensity=0.5,
                                      **calibrated_sg(0.05))
    rows: List[Dict[str, Any]] = []
    train_log: Dict[str, float] = {}

    # ---- fixed SleeperGuard configuration and protocol baselines (no controller) -------------
    jobs = []
    for bname, atk, s in itertools.product(list(BASELINES) + ["sleeper_guard_fixed"], ATTACKS, seeds):
        ov = dict(BASELINES.get(bname, BASELINES["sleeper_guard"]))
        cfg = dict(steps=steps, t_switch=steps // 2, attack_intensity=0.5, seed=s, attack=atk, **ov)
        if ov.get("trust_backend") == "sleeper_guard":
            cfg.update(calibrated_sg(0.05))
        jobs.append({"cfg": cfg, "tags": dict(controller=bname, attack=atk)})
    rows += run_parallel(run_one, jobs, args.workers)

    # ---- rule controller tuned on calibration seeds ------------------------------------------
    best, best_score = (0.05, 0.01), -1e9
    for hi, lo in itertools.product((0.02, 0.05, 0.1), (0.0, 0.01, 0.02)):
        if lo >= hi:
            continue
        c = RuleController(hi, lo)
        sc = []
        for atk, s in itertools.product(ATTACKS, calib_seeds):
            env = run_episode(base.with_overrides(seed=s, attack=atk), c)
            sc.append(sum(x.reward for x in env.records) / len(env.records))
        score = sum(sc) / len(sc)
        if score > best_score:
            best, best_score = (hi, lo), score
    rows += _eval(RuleController(*best), base, seeds, "rule")
    train_log["rule_err_hi"], train_log["rule_err_lo"] = best

    # ---- learning controllers ------------------------------------------------------------------
    for name, mk in (("tabular_q", lambda: TabularQController(seed=0)),
                     ("d3p", lambda: D3PController(seed=0)),
                     ("marl_factored", lambda: FactoredController(seed=0))):
        t1 = time.time()
        ctrl = mk()
        train(ctrl, base, train_seeds, epochs)
        train_log[f"{name}_train_s"] = round(time.time() - t1, 1)
        rows += _eval(ctrl, base, seeds, name)
        print(f"[e9] {name} trained in {train_log[f'{name}_train_s']}s", flush=True)

    write("e9_learning", out_dir("e9_learning", args), rows, args, t0=t0,
          extra_meta={"train": train_log, "epochs": epochs, "train_seeds": train_seeds, "calib_seeds": calib_seeds})


if __name__ == "__main__":
    main()
