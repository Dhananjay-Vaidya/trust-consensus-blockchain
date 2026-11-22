"""Grid experiments on the honest environment (all evaluation seeds 100-129 by default).

  e1  Does the TDP collapse reproduce without the oracle?   legacy Beta; TDP vs always-on CRA;
      honest fault 0.02/0.05/0.10.
  e2  Does SleeperGuard fix it?   legacy vs SleeperGuard (calibrated); coalition 0.1-0.4;
      t_switch {150,300,450}; attack intensity {0.25, 1.0}; honest fault 0.05.
  e3  Ablation: full / no-CUSUM / no-two-timescale / no-cap / none; TDP x {0.25, 1.0}, AAA, CRA.
  e6  Audit budget: audit_rate 0.05-1.0, legacy vs SleeperGuard, TDP x {0.25, 1.0}.
  e7  False-positive cost: honest fault 0-0.20 under attack none and TDP; SleeperGuard calibrated
      for the true rate vs fixed at the 0.05 calibration (misspecified); plus a CUSUM-alarm sweep
      (detection-delay vs false-quarantine trade-off curve).
Usage: python -m experiments.grid e2  (or the thin wrappers exp_e1_*.py, exp_e2_*.py, ...) [--seeds 100-129] [--smoke]
"""
from __future__ import annotations

import itertools
import sys
import time
from typing import Any, Dict, List

from experiments.common import base_parser, out_dir, parse_seeds, run_parallel, write
from experiments.runner import calibrated_sg, run_one

COALITIONS = (0.125, 0.1875, 0.25, 0.3125, 0.375)   # 2..6 of 16 nodes (0.1-0.4 range)
ABLATIONS = {
    "full": {},
    "no_cusum": {"sg_use_cusum": False},
    "no_two_timescale": {"sg_use_two_timescale": False},
    "no_cap": {"sg_use_share_cap": False},
    "none": {"sg_use_cusum": False, "sg_use_two_timescale": False, "sg_use_share_cap": False},
}


def _sg(f: float) -> Dict[str, Any]:
    return dict(trust_backend="sleeper_guard", **calibrated_sg(f))


def jobs_for(exp: str, seeds: List[int], steps: int) -> List[Dict[str, Any]]:
    J: List[Dict[str, Any]] = []
    half = steps // 2

    def add(cfg: Dict[str, Any], tags: Dict[str, Any]) -> None:
        base = dict(steps=steps, t_switch=half)
        base.update(cfg)
        for s in seeds:
            J.append({"cfg": dict(base, seed=s), "tags": tags})

    if exp == "e1":
        for f, atk in itertools.product((0.02, 0.05, 0.10), ("tdp", "cra")):
            add(dict(trust_backend="legacy_beta", honest_fault_rate=f, attack=atk),
                dict(backend="legacy_beta", fault=f, attack=atk))
    elif exp == "e2":
        for mf, ts, inten in itertools.product(COALITIONS, (0.25, 0.5, 0.75), (0.25, 1.0)):
            t_switch = int(steps * ts)
            for be in ("legacy_beta", "sleeper_guard"):
                cfg = dict(malicious_fraction=mf, t_switch=t_switch, attack="tdp", attack_intensity=inten)
                cfg.update(_sg(0.05) if be == "sleeper_guard" else dict(trust_backend="legacy_beta"))
                add(cfg, dict(backend=be, coalition=mf, t_switch=t_switch, intensity=inten))
    elif exp == "e3":
        for (atk, inten), (name, ov) in itertools.product(
                (("tdp", 0.25), ("tdp", 1.0), ("aaa", 0.3), ("cra", 1.0)), ABLATIONS.items()):
            cfg = dict(_sg(0.05), attack=atk, attack_intensity=inten, malicious_fraction=0.3125)
            cfg.update(ov)
            add(cfg, dict(variant=name, attack=atk, intensity=inten))
    elif exp == "e6":
        for ar, be, inten in itertools.product((0.05, 0.1, 0.2, 0.4, 0.7, 1.0), ("legacy_beta", "sleeper_guard"),
                                               (0.25, 1.0)):
            cfg = dict(audit_rate=ar, attack="tdp", attack_intensity=inten)
            cfg.update(_sg(0.05) if be == "sleeper_guard" else dict(trust_backend="legacy_beta"))
            add(cfg, dict(backend=be, audit_rate=ar, intensity=inten))
    elif exp == "e7":
        for f, atk, cal in itertools.product((0.0, 0.02, 0.05, 0.10, 0.15, 0.20), ("none", "tdp"),
                                             ("matched", "fixed_0.05")):
            sg = _sg(max(f, 0.02)) if cal == "matched" else _sg(0.05)
            add(dict(sg, honest_fault_rate=f, attack=atk, attack_intensity=0.25),
                dict(fault=f, attack=atk, calibration=cal, alarm=sg.get("sg_cusum_alarm", 3.0), sweep=False))
        for al, atk in itertools.product((1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0), ("none", "tdp")):
            add(dict(_sg(0.05), sg_cusum_alarm=al, honest_fault_rate=0.05, attack=atk, attack_intensity=0.25),
                dict(fault=0.05, attack=atk, calibration="sweep", alarm=al, sweep=True))
    else:
        raise SystemExit(f"unknown experiment {exp}")
    return J


def main() -> None:
    exp = sys.argv.pop(1) if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "e1"
    args = base_parser(f"{exp}", "100-129").parse_args()
    seeds = parse_seeds(args.seeds)
    steps = 600
    if args.smoke:
        seeds, steps = seeds[:3], 200
    t0 = time.time()
    jobs = jobs_for(exp, seeds, steps)
    print(f"[{exp}] {len(jobs)} runs")
    rows = run_parallel(run_one, jobs, args.workers)
    names = {"e1": "e1_tdp_collapse", "e2": "e2_sleeperguard", "e3": "e3_ablation", "e6": "e6_audit_budget",
             "e7": "e7_false_positives"}
    write(names[exp], out_dir(names[exp], args), rows, args, t0=t0)


if __name__ == "__main__":
    main()
