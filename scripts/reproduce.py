"""Regenerate every result, table and figure from scratch (cross-platform `make reproduce`).

  python scripts/reproduce.py            # full protocol (calibration, E0-E16, paper assets)
  python scripts/reproduce.py --smoke    # 3-seed shortened versions (CI)
  python scripts/reproduce.py --only e2,e3 / --skip e4
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STEPS = [
    ("calibration", ["-m", "experiments.calibrate_sg"]),   # must run first: E2-E10 read its output
    ("e0", ["-m", "experiments.exp_e0_oracle_gap"]),
    ("e1", ["-m", "experiments.exp_e1_tdp_collapse"]),
    ("e2", ["-m", "experiments.exp_e2_sleeperguard"]),
    ("e3", ["-m", "experiments.exp_e3_ablation"]),
    ("e4", ["-m", "experiments.exp_he"]),
    ("e4band", ["-m", "experiments.exp_he_band"]),
    ("e5", ["-m", "experiments.exp_e5_scale"]),
    ("e6", ["-m", "experiments.exp_e6_audit_budget"]),
    ("e7", ["-m", "experiments.exp_e7_false_positives"]),
    ("e8", ["-m", "experiments.exp_e8_privacy"]),
    ("e9", ["-m", "experiments.exp_e9_learning", "--epochs", "10"]),
    ("e10", ["-m", "experiments.exp_e10_safety"]),
    ("e11", ["-m", "experiments.exp_e11_adaptive"]),
    ("e12", ["-m", "experiments.exp_e12_lierate"]),
    ("e13", ["-m", "experiments.exp_e13_preprint_protocol"]),
    ("e14", ["-m", "experiments.exp_e14_baselines"]),
    ("e14mech", ["-m", "experiments.diag_e14_mechanism"]),
    ("e15", ["-m", "experiments.exp_e15_weight_recovery"]),
    ("e16", ["-m", "experiments.exp_e16_imperfect_audits"]),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--skip", default="")
    ap.add_argument("--no-assets", action="store_true")
    a = ap.parse_args()
    only = {s for s in a.only.split(",") if s}
    skip = {s for s in a.skip.split(",") if s}
    for name, cmd in STEPS:
        if (only and name not in only) or name in skip:
            continue
        full = [sys.executable, *cmd] + (["--smoke"] if a.smoke else [])
        if a.smoke and name == "e9":
            full = [x for x in full if x not in ("--epochs", "10")]
        t0 = time.time()
        print(f"=== {name}: {' '.join(full[1:])}", flush=True)
        subprocess.run(full, cwd=ROOT, check=True)
        print(f"=== {name} done in {time.time() - t0:.0f}s", flush=True)
    if not a.no_assets and not a.smoke:
        subprocess.run([sys.executable, "paper/make_assets.py"], cwd=ROOT, check=True)
    elif a.smoke and not a.no_assets:
        print("smoke mode: paper assets not regenerated (they are built from full results only)")


if __name__ == "__main__":
    main()
