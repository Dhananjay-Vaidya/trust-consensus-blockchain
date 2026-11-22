"""Calibrate SleeperGuard's CUSUM on CALIBRATION seeds (20-29) only.

For each nominal honest fault rate f in {0.02, 0.05, 0.10}:
  * baseline_floor := f (the operator's nominal fault rate);
  * grid over cusum_slack x cusum_alarm;
  * constraint: honest false quarantines under attack 'none' <= BUDGET per 1000 node-steps (mean
    over calibration seeds);
  * objective: smallest mean detection delay against a *stealthy* sleeper (TDP, intensity 0.25);
    ties broken by fewer false quarantines.
If no grid point meets the budget, the point with the fewest false quarantines is chosen and the
violation is recorded.  Output: results/raw/calibration/{grid.csv, selected.json}.
"""
from __future__ import annotations

import itertools
import json
import time

import pandas as pd

from experiments.common import base_parser, out_dir, parse_seeds, run_parallel, write
from experiments.runner import run_one

FAULTS = (0.02, 0.05, 0.10)
SLACK = (0.05, 0.1, 0.15, 0.2, 0.3)
ALARM = (2.0, 3.0, 4.0, 6.0, 8.0)
BUDGET = 1.0


def main() -> None:
    args = base_parser("calibrate SleeperGuard", "20-29").parse_args()
    seeds = parse_seeds(args.seeds)
    steps = 600
    if args.smoke:
        seeds, steps = seeds[:3], 200
    t0 = time.time()
    jobs = []
    for f, sl, al, atk in itertools.product(FAULTS, SLACK, ALARM, ("none", "tdp")):
        for s in seeds:
            jobs.append({"cfg": dict(seed=s, steps=steps, t_switch=steps // 2, honest_fault_rate=f,
                                     attack=atk, attack_intensity=0.25, trust_backend="sleeper_guard",
                                     sg_baseline_floor=f, sg_cusum_slack=sl, sg_cusum_alarm=al),
                         "tags": dict(fault=f, slack=sl, alarm=al, attack=atk)})
    d = out_dir("calibration", args)
    rows = run_parallel(run_one, jobs, args.workers)
    write("calibration", d, rows, args, t0=t0, name="grid.csv")
    df = pd.DataFrame(rows)
    sel, notes = {}, {}
    for f in FAULTS:
        g = df[df.fault == f]
        fp = g[g.attack == "none"].groupby(["slack", "alarm"]).honest_quarantines_per_1000.mean()
        dl = g[g.attack == "tdp"].groupby(["slack", "alarm"]).delay_mean.mean()
        tab = pd.DataFrame({"fp": fp, "delay": dl}).reset_index()
        ok = tab[tab.fp <= BUDGET]
        if len(ok):
            best = ok.sort_values(["delay", "fp"]).iloc[0]
            notes[f"{f:.2f}"] = "budget met"
        else:
            best = tab.sort_values(["fp", "delay"]).iloc[0]
            notes[f"{f:.2f}"] = f"BUDGET VIOLATED: min fp={best.fp:.3f}"
        sel[f"{f:.2f}"] = {"baseline_floor": f, "cusum_slack": float(best.slack), "cusum_alarm": float(best.alarm)}
        print(f"fault={f}: slack={best.slack} alarm={best.alarm} fp={best.fp:.3f} delay={best.delay:.2f} ({notes[f'{f:.2f}']})")
    (d / "selected.json").write_text(json.dumps(sel, indent=2))
    (d / "selection_notes.json").write_text(json.dumps({"budget_per_1000": BUDGET, "notes": notes}, indent=2))


if __name__ == "__main__":
    main()
