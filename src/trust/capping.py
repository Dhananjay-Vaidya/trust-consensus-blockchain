"""Exact per-delegate share cap (water-filling).

The provided ``sleeper_guard.cap_shares`` redistributes excess proportionally to *all* non-over
nodes, including nodes already sitting at the cap, so it only converges geometrically. After its
20-iteration limit a share can still exceed the cap by up to ~2x (tests/test_capping.py;
results/raw/e10_safety). That function is kept byte-for-byte for the ablation
(``cap_method="verified_iterative"``). This module computes the exact solution in at most k rounds:

    w'_i = min(C, alpha * w_i),  C = max_share * sum(w),  alpha chosen so that sum(w') = sum(w).

The cap is feasible iff at least ceil(1 / max_share) entries are positive. If it is infeasible the
input is returned unchanged, and the TDCB tally aborts the round (DECISIONS D9).
"""
from __future__ import annotations

import numpy as np


def cap_shares_exact(w: np.ndarray, max_share: float) -> np.ndarray:
    w = np.asarray(w, dtype=float).copy()
    total = w.sum()
    pos = w > 0
    if total <= 0 or max_share * pos.sum() < 1.0 - 1e-12:
        return w
    cap = max_share * total
    capped = np.zeros(len(w), dtype=bool)
    for _ in range(len(w) + 1):
        free = pos & ~capped
        if not free.any():
            break
        alpha = (total - cap * capped.sum()) / w[free].sum()
        new = free & (alpha * w > cap * (1 + 1e-12))
        if not new.any():
            break
        capped |= new
    free = pos & ~capped
    out = np.zeros_like(w)
    out[capped] = cap
    if free.any():
        out[free] = w[free] * (total - cap * capped.sum()) / w[free].sum()
    return out
