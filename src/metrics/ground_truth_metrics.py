"""Post-hoc metrics. The ONLY module of the defended system allowed to read ground truth.

It reads ``env._world.ground_truth_record()`` after (or between) steps and never feeds anything
back into the environment, the trust backend or a controller.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.metrics import f1_score, matthews_corrcoef, precision_score, recall_score

from src.env.honest_env import HonestEnv


def _prf(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """zero_division=0 (A7): no positives predicted => precision 0, never a free 1."""
    if y_true.size == 0:
        return {"precision": math.nan, "recall": math.nan, "f1": math.nan, "mcc": math.nan}
    return {
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "mcc": float(matthews_corrcoef(y_true, y_pred)) if len(np.unique(y_true)) > 1 or len(np.unique(y_pred)) > 1 else 0.0,
    }


def node_labels(env: HonestEnv, step: int) -> np.ndarray:
    """(N,) bool: node is adversary-controlled AND its attack is active at ``step``."""
    rec = env._world.ground_truth_record()[step]
    if not rec.coalition_active:
        return np.zeros(len(env.nodes), dtype=bool)
    return np.array([n in rec.coalition for n in env.nodes], dtype=bool)


def display_labels(env: HonestEnv) -> Dict[str, bool]:
    """For the dashboard only (post-hoc visualisation)."""
    co = env._world.coalition
    return {n: (n in co) for n in env.nodes}


def eval_window_start(env: HonestEnv, burn_in: int = 50) -> int:
    c = env.cfg
    if c.attack == "tdp":
        return c.t_switch
    return min(burn_in, max(0, c.steps - 1))


def summarize(env: HonestEnv, window_start: Optional[int] = None, window_end: Optional[int] = None) -> Dict[str, Any]:
    c = env.cfg
    truth = env._world.ground_truth_record()
    recs = env.records
    s0 = eval_window_start(env) if window_start is None else window_start
    s1 = len(recs) if window_end is None else min(window_end, len(recs))
    win = range(s0, s1)

    # ---- node-level detection over node-steps in the window --------------------------------
    y_t, y_p = [], []
    for s in win:
        y_t.append(node_labels(env, s))
        y_p.append(recs[s].flagged)
    yt = np.concatenate(y_t) if y_t else np.zeros(0, bool)
    yp = np.concatenate(y_p) if y_p else np.zeros(0, bool)
    det = _prf(yt.astype(int), yp.astype(int))

    # final-step snapshot (comparable to the preprint's end-of-run F1)
    last = len(recs) - 1
    fin = _prf(node_labels(env, last).astype(int), recs[last].flagged.astype(int)) if last >= s0 else _prf(np.zeros(0), np.zeros(0))

    # ---- detection delay per adversary node (first flag at/after attack onset) ---------------
    coalition = sorted(truth[-1].coalition) if truth else []
    onset: Dict[str, int] = {}
    for n in coalition:
        b = env._world.bribed_at.get(n)
        onset[n] = b if b is not None else (c.t_switch if c.attack == "tdp" else 0)
    delays: List[float] = []
    censored = 0
    for n in coalition:
        i = env.node_idx[n]
        hit = next((s for s in range(onset[n], len(recs)) if recs[s].flagged[i]), None)
        if hit is None:
            censored += 1
            delays.append(float(len(recs) - onset[n]))
        else:
            delays.append(float(hit - onset[n]))

    # ---- honest false quarantines ------------------------------------------------------------
    honest = [i for i, n in enumerate(env.nodes) if n not in truth[-1].coalition] if truth else []
    hon_alarms = sum(1 for r in recs for a in r.alarms if a in set(honest))
    node_steps = max(1, len(honest) * len(recs))
    hon_flag_frac = float(np.mean([r.flagged[honest].mean() for r in recs[s0:s1]])) if honest and s1 > s0 else math.nan

    # ---- transaction level -----------------------------------------------------------------
    inv_tot = inv_com = val_tot = val_rej = 0
    for s in win:
        v = truth[s].validity
        a = recs[s].accept
        inv_tot += int((~v).sum())
        inv_com += int((a & ~v).sum())
        val_tot += int(v.sum())
        val_rej += int((~a & v).sum())
    committed_valid = sum(int((recs[s].accept & truth[s].validity).sum()) for s in win)
    lat = np.array([recs[s].latency_ms for s in win]) if s1 > s0 else np.array([math.nan])
    wall = np.array([recs[s].wall_ms for s in win]) if s1 > s0 else np.array([math.nan])
    he = np.array([recs[s].he_ms for s in win]) if s1 > s0 else np.array([0.0])

    return {
        "window_start": s0, "window_end": s1,
        "det_precision": det["precision"], "det_recall": det["recall"], "det_f1": det["f1"], "det_mcc": det["mcc"],
        "final_f1": fin["f1"], "final_precision": fin["precision"], "final_recall": fin["recall"], "final_mcc": fin["mcc"],
        "delay_mean": float(np.mean(delays)) if delays else math.nan,
        "delay_median": float(np.median(delays)) if delays else math.nan,
        "delay_censored": censored, "n_adversary": len(coalition),
        "honest_quarantines_per_1000": 1000.0 * hon_alarms / node_steps,
        "honest_flagged_frac": hon_flag_frac,
        "invalid_commit_rate": inv_com / inv_tot if inv_tot else math.nan,
        "valid_reject_rate": val_rej / val_tot if val_tot else math.nan,
        "abort_rate": float(np.mean([recs[s].aborted for s in win])) if s1 > s0 else math.nan,
        "throughput_tps": committed_valid / max(1e-9, float(np.nansum(lat)) / 1e3),
        "latency_p50_ms": float(np.nanpercentile(lat, 50)),
        "latency_p95_ms": float(np.nanpercentile(lat, 95)),
        "latency_p99_ms": float(np.nanpercentile(lat, 99)),
        "wall_ms_per_step": float(np.nanmean(wall)),
        "he_ms_per_step": float(np.mean(he)),
        "he_flips": int(sum(recs[s].he_flips for s in win)),
        "mean_reward": float(np.mean([recs[s].reward for s in win])) if s1 > s0 else math.nan,
    }
