"""SleeperGuard: oracle-free trust with fast/slow memory, change detection and bounded influence.

Evidence per node per step: e in {0, 1}; 1 = the node's vote disagreed with the audited outcome.
Nothing here reads ground-truth labels.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

import numpy as np


@dataclass
class SleeperGuardConfig:
    lam_fast: float = 0.90        # ~10-step memory
    lam_slow: float = 0.995       # ~200-step memory
    prior: float = 1.0            # Beta(prior, prior) for each timescale
    baseline_floor: float = 0.02  # assumed honest fault rate; lower bound on mu0 in CUSUM
    cusum_slack: float = 0.15     # k: tolerated excess disagreement rate
    cusum_alarm: float = 3.0      # h: alarm threshold
    quarantine_steps: int = 50
    probation_steps: int = 30
    probation_weight: float = 0.25
    cap_factor: float = 2.0       # per-delegate weight share is capped at cap_factor / committee_size (>= 1)
    use_two_timescale: bool = True
    use_cusum: bool = True
    use_share_cap: bool = True


class SleeperGuard:
    def __init__(self, nodes: Iterable[str], cfg: SleeperGuardConfig | None = None) -> None:
        self.cfg = cfg or SleeperGuardConfig()
        self.nodes: List[str] = list(nodes)
        z = lambda: {n: 0.0 for n in self.nodes}  # noqa: E731
        self.a_fast, self.b_fast, self.a_slow, self.b_slow = z(), z(), z(), z()
        self.cusum = z()
        self.quarantine_left = {n: 0 for n in self.nodes}
        self.probation_left = {n: 0 for n in self.nodes}
        self.alarms: Dict[str, int] = {n: 0 for n in self.nodes}

    # -- evidence ---------------------------------------------------------------------------
    def observe(self, node: str, inconsistent: bool) -> bool:
        """Feed one audited observation. Returns True if this observation raised a change alarm."""
        c, e = self.cfg, float(inconsistent)
        self.a_fast[node] = c.lam_fast * self.a_fast[node] + (1.0 - e)
        self.b_fast[node] = c.lam_fast * self.b_fast[node] + e
        self.a_slow[node] = c.lam_slow * self.a_slow[node] + (1.0 - e)
        self.b_slow[node] = c.lam_slow * self.b_slow[node] + e

        if self.quarantine_left[node] > 0:
            self.quarantine_left[node] -= 1
            if self.quarantine_left[node] == 0:
                self.probation_left[node] = c.probation_steps
            return False
        if self.probation_left[node] > 0:
            self.probation_left[node] -= 1

        if not c.use_cusum:
            return False
        mu0 = max(c.baseline_floor, 1.0 - self._mean(self.a_slow[node], self.b_slow[node]))
        self.cusum[node] = max(0.0, self.cusum[node] + e - (mu0 + c.cusum_slack))
        if self.cusum[node] > c.cusum_alarm:
            self.cusum[node] = 0.0
            self.quarantine_left[node] = c.quarantine_steps
            self.alarms[node] += 1
            return True
        return False

    def _mean(self, a: float, b: float) -> float:
        p = self.cfg.prior
        return (a + p) / (a + b + 2.0 * p)

    # -- weights ----------------------------------------------------------------------------
    def trust(self, node: str) -> float:
        fast = self._mean(self.a_fast[node], self.b_fast[node])
        if not self.cfg.use_two_timescale:
            return self._mean(self.a_slow[node], self.b_slow[node])
        return min(fast, self._mean(self.a_slow[node], self.b_slow[node]))  # pessimistic

    def is_quarantined(self, node: str) -> bool:
        return self.quarantine_left[node] > 0

    def weights(self, committee: List[str]) -> np.ndarray:
        w = np.array([0.0 if self.is_quarantined(n) else self.trust(n)
                      * (self.cfg.probation_weight if self.probation_left[n] > 0 else 1.0)
                      for n in committee], dtype=float)
        if self.cfg.use_share_cap and len(committee) > 0:
            w = cap_shares(w, self.cfg.cap_factor / len(committee))
        return w


def cap_shares(w: np.ndarray, max_share: float, iters: int = 20) -> np.ndarray:
    """Water-filling: clip any weight above max_share * sum(w) and redistribute to the rest."""
    w = w.astype(float).copy()
    if w.sum() <= 0 or max_share * len(w) < 1.0:   # infeasible cap: leave unchanged
        return w
    for _ in range(iters):
        total = w.sum()
        cap = max_share * total
        over = w > cap + 1e-12
        if not over.any():
            break
        excess = (w[over] - cap).sum()
        w[over] = cap
        free = ~over & (w > 0)
        if not free.any():
            break
        w[free] += excess * w[free] / w[free].sum()
    return w
