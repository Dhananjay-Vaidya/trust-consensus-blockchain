"""E11: damage-maximising adaptive attacker vs each defence variant (replaces AAA in E2/E3).

Phase 1 (attacker search, seeds 30-39, disjoint from calibration 20-29 and evaluation 100-129):
  for each defence variant, grid over lie rate x coalition size x target and pick the config that
  maximises invalid-commit rate, then valid-reject rate (the attacker knows the defence's
  configuration and so can choose the lie rate just below its alarm).
Phase 2 (evaluation, seeds 100-129): run each variant against (a) its own best attacker config and
  (b) every coalition size at its best lie rate; report invalid-commit rate, valid-reject rate and F1.
Outputs: results/raw/e11_adaptive/{search.csv, best.json, runs.csv}
"""
from __future__ import annotations

import itertools
import json
import time
from typing import Any, Dict, List

import pandas as pd

from experiments.common import base_parser, out_dir, parse_seeds, run_parallel, write
from experiments.runner import calibrated_sg, run_one

LIE_RATES = (0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 0.75, 1.0)
COALITIONS = (2, 3, 4, 5, 6, 7, 8)          # of 16 nodes
TARGETS = ("invalid", "both")


def variants() -> Dict[str, Dict[str, Any]]:
    sg = dict(trust_backend="sleeper_guard", **calibrated_sg(0.05))
    return {
        "legacy_beta": dict(trust_backend="legacy_beta"),
        "sg_full": sg,
        "sg_no_cusum": dict(sg, sg_use_cusum=False),
        "sg_no_two_timescale": dict(sg, sg_use_two_timescale=False),
        "sg_no_cap": dict(sg, sg_use_share_cap=False),
        "sg_none": dict(sg, sg_use_cusum=False, sg_use_two_timescale=False, sg_use_share_cap=False),
    }


def main() -> None:
    p = base_parser("E11 adaptive attacker", "100-129")
    p.add_argument("--search-seeds", default="30-39")
    args = p.parse_args()
    seeds, sseeds, steps = parse_seeds(args.seeds), parse_seeds(args.search_seeds), 600
    rates, coal = LIE_RATES, COALITIONS
    if args.smoke:
        seeds, sseeds, steps, rates, coal = seeds[:3], sseeds[:2], 150, (0.1, 1.0), (4, 6)
    d = out_dir("e11_adaptive", args)
    V = variants()
    t0 = time.time()
    jobs: List[Dict[str, Any]] = []
    for (vn, vo), r, b, tg in itertools.product(V.items(), rates, coal, TARGETS):
        for s in sseeds:
            jobs.append({"cfg": dict(vo, seed=s, steps=steps, attack="mda", attack_intensity=r, attack_target=tg,
                                     malicious_fraction=b / 16),
                         "tags": dict(variant=vn, lie_rate=r, b=b, target=tg)})
    rows = run_parallel(run_one, jobs, args.workers)
    write("e11_adaptive", d, rows, args, name="search.csv", t0=t0)
    g = pd.DataFrame(rows).groupby(["variant", "lie_rate", "b", "target"])[["invalid_commit_rate", "valid_reject_rate"]].mean().reset_index()
    best = {}
    for vn, h in g.groupby("variant"):
        top = h.sort_values(["invalid_commit_rate", "valid_reject_rate"], ascending=False).iloc[0]
        best[vn] = dict(lie_rate=float(top.lie_rate), b=int(top.b), target=str(top.target),
                        search_invalid=float(top.invalid_commit_rate), search_reject=float(top.valid_reject_rate))
    (d / "best.json").write_text(json.dumps(best, indent=2))

    t1 = time.time()
    ev = []
    for vn, vo in V.items():
        bc = best[vn]
        for b in coal:
            for s in seeds:
                ev.append({"cfg": dict(vo, seed=s, steps=steps, attack="mda", attack_intensity=bc["lie_rate"],
                                       attack_target=bc["target"], malicious_fraction=b / 16),
                           "tags": dict(variant=vn, lie_rate=bc["lie_rate"], b=b, target=bc["target"],
                                        is_best=(b == bc["b"]))})
    write("e11_adaptive", d, run_parallel(run_one, ev, args.workers), args, name="runs.csv", t0=t1)


if __name__ == "__main__":
    main()
