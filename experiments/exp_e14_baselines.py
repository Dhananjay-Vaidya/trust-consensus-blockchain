"""E14: standalone change-detection baselines vs legacy Beta and SleeperGuard.

Methods (all see only the audit indicator e; src/trust/detectors.py):
  legacy_beta   legacy Beta, flag if trust < 0.5 (the E2 reference, not tuned)
  legacy_thr    legacy Beta with a calibrated flag threshold (control)
  sg_full       SleeperGuard as in E2 (calibration of results/raw/calibration, same 25-point grid)
  sg_no_cap     SleeperGuard without the share cap, calibrated on its own (control)
  cusum         CUSUM-only + SleeperGuard's quarantine/probation, single-timescale Beta, no cap
  ewma          EWMA-only, same quarantine/probation, no cap
  window        sliding-window disagreement rate, same quarantine/probation, no cap

Phase 0  calibration, seeds 20-29 only.  For each fault rate f in {0.02, 0.05, 0.10} every tuned method gets
         the same 25-point grid (SleeperGuard's budget); constraint <= 1 honest false quarantine per 1000
         node-steps without attack (legacy_thr: honest *flagged* node-steps, it has no quarantine); objective
         smallest mean detection delay against the stealthy sleeper (TDP 0.25), ties -> fewer false alarms.
Phase 1  evaluation, seeds 100-129 (30 paired seeds), E2 environment (16 nodes, 600 steps, t_switch 300):
         sleeper at coalition {0.125, 0.25, 0.375} x intensity {0.25, 1.0} plus no attack, at
         f = 0.05 (matched), f = 0.02 / 0.10 (matched) and f = 0.02 / 0.10 run with the 0.05 calibration;
         CRA / NMA / BFI sanity check at f = 0.05.
Phase 2  E11 damage-maximising search per method on seeds 30-39 (lie rate x coalition x target), best
         configuration evaluated on seeds 100-129.
Outputs: results/raw/e14_baselines/{calib_grid.csv, calibration.csv, runs.csv, search.csv, best.json, meta.json}
"""
from __future__ import annotations

import itertools
import json
import time
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from experiments.common import RAW, base_parser, out_dir, parse_seeds, run_parallel, write
from experiments.exp_e11_adaptive import COALITIONS as E11_COALITIONS
from experiments.exp_e11_adaptive import LIE_RATES, TARGETS
from experiments.runner import calibrated_sg, run_one

FAULTS = (0.02, 0.05, 0.10)
BUDGET = 1.0
SLACK = (0.05, 0.1, 0.15, 0.2, 0.3)          # SleeperGuard's calibration grid (experiments/calibrate_sg.py)
ALARM = (2.0, 3.0, 4.0, 6.0, 8.0)
LAMS = (0.8, 0.9, 0.95, 0.98, 0.99)
WINDOWS = (10, 20, 40, 80, 160)
DELTAS = (0.05, 0.1, 0.15, 0.2, 0.3)          # EWMA / window alarm level = f + delta
THRESHOLDS = tuple(float(x) for x in np.round(np.linspace(0.20, 0.68, 25), 2))
TUNED = ("legacy_thr", "sg_no_cap", "cusum", "ewma", "window")
METHODS = ("legacy_beta", "legacy_thr", "sg_full", "sg_no_cap", "cusum", "ewma", "window")
COALITIONS = (0.125, 0.25, 0.375)
INTENSITIES = (0.25, 1.0)
CONDITIONS = ((0.05, "matched"), (0.02, "matched"), (0.02, "fixed_0.05"), (0.10, "matched"), (0.10, "fixed_0.05"))


def grid(method: str, f: float) -> List[Dict[str, Any]]:
    """25 candidate parameter sets for one tuned method at nominal fault rate f."""
    if method == "legacy_thr":
        return [dict(flag_threshold=t) for t in THRESHOLDS]
    if method == "sg_no_cap":
        return [dict(sg_baseline_floor=f, sg_cusum_slack=s, sg_cusum_alarm=a) for s, a in itertools.product(SLACK, ALARM)]
    if method == "cusum":
        return [dict(det_reference=round(f + s, 4), det_threshold=a) for s, a in itertools.product(SLACK, ALARM)]
    if method == "ewma":
        return [dict(det_lam=lam, det_threshold=round(f + d, 4)) for lam, d in itertools.product(LAMS, DELTAS)]
    if method == "window":
        return [dict(det_window=w, det_threshold=round(f + d, 4)) for w, d in itertools.product(WINDOWS, DELTAS)]
    raise ValueError(method)


def base(method: str) -> Dict[str, Any]:
    if method in ("legacy_beta", "legacy_thr"):
        return dict(trust_backend="legacy_beta")
    if method == "sg_full":
        return dict(trust_backend="sleeper_guard")
    if method == "sg_no_cap":
        return dict(trust_backend="sleeper_guard", sg_use_share_cap=False)
    return dict(trust_backend=method)


def params_for(method: str, f_cal: float, chosen: Dict[Tuple[str, float], Dict[str, Any]]) -> Dict[str, Any]:
    if method == "legacy_beta":
        return {}
    if method == "sg_full":
        return calibrated_sg(f_cal)
    return dict(chosen[(method, round(f_cal, 2))])


def calibrate(seeds: List[int], steps: int, workers: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
    jobs = []
    for m, f in itertools.product(TUNED, FAULTS):
        for gi, p in enumerate(grid(m, f)):
            for atk, s in itertools.product(("none", "tdp"), seeds):
                jobs.append({"cfg": dict(base(m), **p, seed=s, steps=steps, t_switch=steps // 2, honest_fault_rate=f,
                                         attack=atk, attack_intensity=0.25),
                             "tags": dict(method=m, fault=f, grid_id=gi, params=json.dumps(p, sort_keys=True),
                                          attack=atk)})
    df = pd.DataFrame(run_parallel(run_one, jobs, workers))
    sel = []
    for (m, f), g in df.groupby(["method", "fault"]):
        none = g[g.attack == "none"]
        metric = (1000.0 * none.honest_flagged_frac) if m == "legacy_thr" else none.honest_quarantines_per_1000
        fp = metric.groupby(none.grid_id).mean()
        dl = g[g.attack == "tdp"].groupby("grid_id").delay_mean.mean()
        tab = pd.DataFrame({"fp": fp, "delay": dl}).reset_index()
        # tie-break: fewer false alarms, then grid order.  legacy_thr's grid is ascending thresholds and its delay is
        # often fully censored (all ties), so among equal delays it takes the HIGHEST feasible threshold, i.e. the
        # most aggressive flag rule that still meets the budget (fewest-false-alarms would pick the threshold that
        # flags nothing, which is not a calibration).
        tab["tie"] = -tab.grid_id if m == "legacy_thr" else tab.grid_id
        ok = tab[tab.fp <= BUDGET]
        best = (ok.sort_values(["delay", "tie"] if m == "legacy_thr" else ["delay", "fp", "tie"]) if len(ok)
                else tab.sort_values(["fp", "delay", "tie"])).iloc[0]
        p = json.loads(g[g.grid_id == best.grid_id].params.iloc[0])
        sel.append(dict(method=m, fault=f, grid_points=int(len(tab)), budget_met=bool(len(ok)),
                        feasible_points=int(len(ok)), calib_fp_per_1000=float(best.fp),
                        calib_delay=float(best.delay), params=json.dumps(p, sort_keys=True), **p))
    sg = json.loads((RAW / "calibration" / "selected.json").read_text())
    for f in FAULTS:
        p = {f"sg_{k}": v for k, v in sg[f"{f:.2f}"].items()}
        sel.append(dict(method="sg_full", fault=f, grid_points=25, budget_met=True, feasible_points=np.nan,
                        calib_fp_per_1000=np.nan, calib_delay=np.nan, params=json.dumps(p, sort_keys=True), **p))
    return df, pd.DataFrame(sel)


def main() -> None:
    p = base_parser("E14 change-detection baselines", "100-129")
    p.add_argument("--calib-seeds", default="20-29")
    p.add_argument("--search-seeds", default="30-39")
    args = p.parse_args()
    seeds, cseeds, sseeds = parse_seeds(args.seeds), parse_seeds(args.calib_seeds), parse_seeds(args.search_seeds)
    steps, rates, coal = 600, LIE_RATES, E11_COALITIONS
    if args.smoke:
        seeds, cseeds, sseeds, steps, rates, coal = seeds[:3], cseeds[:2], sseeds[:2], 200, (0.1, 1.0), (4, 6)
    d = out_dir("e14_baselines", args)
    t0 = time.time()

    calib_grid, chosen_df = calibrate(cseeds, steps, args.workers)
    write("e14_baselines", d, calib_grid.to_dict("records"), args, name="calib_grid.csv", t0=t0)
    write("e14_baselines", d, chosen_df.to_dict("records"), args, name="calibration.csv")
    chosen = {(r.method, round(r.fault, 2)): json.loads(r.params) for r in chosen_df.itertuples()
              if r.method in TUNED}
    print(f"[e14] calibration done ({time.time() - t0:.0f}s)", flush=True)

    jobs: List[Dict[str, Any]] = []

    def add(m: str, cfg: Dict[str, Any], tags: Dict[str, Any], seed_list: List[int]) -> None:
        for s in seed_list:
            jobs.append({"cfg": dict(cfg, seed=s, steps=steps, t_switch=steps // 2), "tags": dict(tags, method=m)})

    for m, (f, cal) in itertools.product(METHODS, CONDITIONS):
        f_cal = f if cal == "matched" else 0.05
        pm = dict(base(m), **params_for(m, f_cal, chosen), honest_fault_rate=f)
        tags = dict(phase="sleeper", fault=f, calibration=cal)
        for mf, it in itertools.product(COALITIONS, INTENSITIES):
            add(m, dict(pm, attack="tdp", attack_intensity=it, malicious_fraction=mf),
                dict(tags, attack="tdp", coalition=mf, intensity=it), seeds)
        add(m, dict(pm, attack="none"), dict(tags, attack="none", coalition=0.0, intensity=0.0), seeds)
    for m, atk in itertools.product(METHODS, ("cra", "nma", "bfi")):
        pm = dict(base(m), **params_for(m, 0.05, chosen), honest_fault_rate=0.05)
        add(m, dict(pm, attack=atk, malicious_fraction=0.3125),
            dict(phase="sanity", fault=0.05, calibration="matched", attack=atk, coalition=0.3125, intensity=1.0), seeds)
    rows = run_parallel(run_one, jobs, args.workers)
    print(f"[e14] evaluation done ({time.time() - t0:.0f}s, {len(rows)} runs)", flush=True)

    # ---- Phase 2: E11 damage-maximising search per method ------------------------------------
    sjobs = []
    for m, r, b, tg in itertools.product(METHODS, rates, coal, TARGETS):
        pm = dict(base(m), **params_for(m, 0.05, chosen), honest_fault_rate=0.05)
        for s in sseeds:
            sjobs.append({"cfg": dict(pm, seed=s, steps=steps, attack="mda", attack_intensity=r, attack_target=tg,
                                      malicious_fraction=b / 16),
                          "tags": dict(method=m, lie_rate=r, b=b, target=tg)})
    srows = run_parallel(run_one, sjobs, args.workers)
    write("e14_baselines", d, srows, args, name="search.csv")
    g = pd.DataFrame(srows).groupby(["method", "lie_rate", "b", "target"])[
        ["invalid_commit_rate", "valid_reject_rate"]].mean().reset_index()
    best: Dict[str, Dict[str, Any]] = {}
    for m, h in g.groupby("method"):
        top = h.sort_values(["invalid_commit_rate", "valid_reject_rate", "b", "lie_rate"],
                            ascending=[False, False, True, True]).iloc[0]
        best[m] = dict(lie_rate=float(top.lie_rate), b=int(top.b), target=str(top.target),
                       search_invalid_commit=float(top.invalid_commit_rate),
                       search_valid_reject=float(top.valid_reject_rate))
    (d / "best.json").write_text(json.dumps(best, indent=2))
    ajobs = []
    for m in METHODS:
        bc = best[m]
        pm = dict(base(m), **params_for(m, 0.05, chosen), honest_fault_rate=0.05)
        for s in seeds:
            ajobs.append({"cfg": dict(pm, seed=s, steps=steps, attack="mda", attack_intensity=bc["lie_rate"],
                                      attack_target=bc["target"], malicious_fraction=bc["b"] / 16),
                          "tags": dict(method=m, phase="adaptive", fault=0.05, calibration="matched", attack="mda",
                                       coalition=bc["b"] / 16, intensity=bc["lie_rate"])})
    rows += run_parallel(run_one, ajobs, args.workers)
    write("e14_baselines", d, rows, args, name="runs.csv", t0=t0,
          extra_meta={"protocol": dict(methods=list(METHODS), tuned=list(TUNED), faults=list(FAULTS),
                                       budget_per_1000=BUDGET, grid_points_per_method=25, calib_seeds=cseeds,
                                       search_seeds=sseeds, eval_seeds=seeds, coalitions=list(COALITIONS),
                                       intensities=list(INTENSITIES), conditions=[list(c) for c in CONDITIONS],
                                       grids=dict(slack=list(SLACK), alarm=list(ALARM), lam=list(LAMS),
                                                  window=list(WINDOWS), delta=list(DELTAS),
                                                  legacy_thresholds=list(THRESHOLDS)))})


if __name__ == "__main__":
    main()
