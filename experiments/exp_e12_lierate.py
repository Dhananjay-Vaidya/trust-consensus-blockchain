"""E12: detection vs lie rate, with the honest false-quarantine rate on the same axes.

SleeperGuard with CUSUM slack/alarm calibrated on seeds 20-29 only (experiments/calibrate_sg.py),
coalition 5 of 16 lying (inverting, coordinated) at rate r in 0.05..1.0 from step 0, honest fault 0.05,
evaluation seeds 100-129.  Legacy Beta is run alongside for reference.
"""
from __future__ import annotations

import itertools
import time

from experiments.common import base_parser, out_dir, parse_seeds, run_parallel, write
from experiments.runner import calibrated_sg, run_one

RATES = (0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.75, 1.0)


def main() -> None:
    args = base_parser("E12 lie-rate curve", "100-129").parse_args()
    seeds, steps, rates = parse_seeds(args.seeds), 600, RATES
    if args.smoke:
        seeds, steps, rates = seeds[:3], 150, (0.1, 1.0)
    t0 = time.time()
    jobs = []
    for be, r, s in itertools.product(("sleeper_guard", "legacy_beta"), rates, seeds):
        tb = dict(trust_backend="sleeper_guard", **calibrated_sg(0.05)) if be == "sleeper_guard" else dict(trust_backend="legacy_beta")
        jobs.append({"cfg": dict(tb, seed=s, steps=steps, attack="mda", attack_target="both", attack_intensity=r,
                                 malicious_fraction=5 / 16, honest_fault_rate=0.05),
                     "tags": dict(backend=be, lie_rate=r)})
    write("e12_lierate", out_dir("e12_lierate", args), run_parallel(run_one, jobs, args.workers), args, t0=t0)


if __name__ == "__main__":
    main()
