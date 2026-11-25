"""E16: imperfect audits.  The E2 stealthy (intensity 0.25) and always-lie (intensity 1.0) sleeper,
coalition 5/16, t_switch 300 of 600, honest fault 0.05 (the E2 middle cell), with audits that are
  perfect      (as in E2),
  wrong w.p. 0.05 / 0.10   (RunConfig.audit_error_rate: each audited verdict flipped independently),
  delayed 10 steps         (RunConfig.audit_delay: verdicts reach trust 10 steps after the decision).
Legacy Beta vs SleeperGuard; SleeperGuard keeps its perfect-audit calibration for f = 0.05 (it is not
re-tuned for the audit noise, which is the realistic misspecification).  Seeds 100-129.
Outputs: results/raw/e16_imperfect_audits/{runs.csv, meta.json}
"""
from __future__ import annotations

import itertools
import time
from typing import Any, Dict, List

from experiments.common import base_parser, out_dir, parse_seeds, run_parallel, write
from experiments.runner import calibrated_sg, run_one

AUDITS = {
    "perfect": dict(audit_error_rate=0.0, audit_delay=0),
    "error_0.05": dict(audit_error_rate=0.05, audit_delay=0),
    "error_0.10": dict(audit_error_rate=0.10, audit_delay=0),
    "delay_10": dict(audit_error_rate=0.0, audit_delay=10),
}
INTENSITIES = {0.25: "stealthy", 1.0: "always_lie"}


def main() -> None:
    args = base_parser("E16 imperfect audits", "100-129").parse_args()
    seeds, steps = parse_seeds(args.seeds), 600
    if args.smoke:
        seeds, steps = seeds[:3], 200
    t0 = time.time()
    jobs: List[Dict[str, Any]] = []
    for (audit, ov), inten, be, s in itertools.product(AUDITS.items(), INTENSITIES, ("legacy_beta", "sleeper_guard"),
                                                       seeds):
        tb = dict(trust_backend="sleeper_guard", **calibrated_sg(0.05)) if be == "sleeper_guard" \
            else dict(trust_backend="legacy_beta")
        jobs.append({"cfg": dict(tb, **ov, seed=s, steps=steps, t_switch=steps // 2, attack="tdp",
                                 attack_intensity=inten, malicious_fraction=0.3125, honest_fault_rate=0.05),
                     "tags": dict(audit=audit, sleeper=INTENSITIES[inten], intensity=inten, backend=be,
                                  audit_error_rate=ov["audit_error_rate"], audit_delay=ov["audit_delay"])})
    print(f"[e16] {len(jobs)} runs")
    rows = run_parallel(run_one, jobs, args.workers)
    write("e16_imperfect_audits", out_dir("e16_imperfect_audits", args), rows, args, t0=t0,
          extra_meta={"audits": AUDITS, "sleeper_guard": calibrated_sg(0.05)})


if __name__ == "__main__":
    main()
