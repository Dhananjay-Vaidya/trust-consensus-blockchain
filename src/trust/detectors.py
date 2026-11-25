"""Standalone change-detection baselines (E14): CUSUM-only, EWMA-only, sliding-window mean.

Each baseline sees only the audit indicator e in {0, 1} per audited vote (1 = the node's vote
disagreed with the audit), exactly like SleeperGuard; nothing here reads ground truth.

Shared parts, deliberately identical to SleeperGuard so the comparison isolates the detector:
  * trust     = single-timescale discounted Beta mean (a + p) / (a + b + 2p), memory ``lam_beta``
                (SleeperGuard's slow timescale; SleeperGuard additionally takes the min with a fast one);
  * quarantine: an alarm quarantines the node for ``quarantine_steps`` audited observations (weight 0),
                then ``probation_steps`` observations at ``probation_weight`` x trust;
  * the detector statistic is frozen while quarantined and reset to its initial value on an alarm;
  * no share cap.
Detector statistics (per node, updated once per audited observation):
  cusum  : S <- max(0, S + e - reference);              alarm when S > threshold
  ewma   : z <- lam * z + (1 - lam) * e;  z0 = 0;        alarm when z > threshold
  window : mean of the last ``window`` observations;     alarm when full and mean > threshold
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, Iterable, List

import numpy as np

METHODS = ("cusum", "ewma", "window")


@dataclass(frozen=True)
class DetectorConfig:
    reference: float = 0.15       # CUSUM drift reference r (nominal fault rate + slack)
    threshold: float = 3.0        # CUSUM h; EWMA / window: alarm level on the disagreement rate
    lam: float = 0.9              # EWMA smoothing factor
    window: int = 40              # sliding-window length in audited observations
    lam_beta: float = 0.995       # memory of the single-timescale Beta trust
    prior: float = 1.0
    quarantine_steps: int = 50    # counted in audited observations, as in SleeperGuard
    probation_steps: int = 30
    probation_weight: float = 0.25


class ChangeDetector:
    def __init__(self, nodes: Iterable[str], method: str, cfg: DetectorConfig | None = None) -> None:
        if method not in METHODS:
            raise ValueError(f"unknown detector {method!r}")
        self.method = method
        self.cfg = cfg or DetectorConfig()
        self.nodes: List[str] = list(nodes)
        self.a: Dict[str, float] = {n: 0.0 for n in self.nodes}
        self.b: Dict[str, float] = {n: 0.0 for n in self.nodes}
        self.stat: Dict[str, float] = {n: 0.0 for n in self.nodes}
        self.buf: Dict[str, Deque[float]] = {n: deque(maxlen=max(1, self.cfg.window)) for n in self.nodes}
        self.quarantine_left: Dict[str, int] = {n: 0 for n in self.nodes}
        self.probation_left: Dict[str, int] = {n: 0 for n in self.nodes}
        self.alarms: Dict[str, int] = {n: 0 for n in self.nodes}

    def _update(self, node: str, e: float) -> bool:
        c = self.cfg
        if self.method == "cusum":
            self.stat[node] = max(0.0, self.stat[node] + e - c.reference)
            return self.stat[node] > c.threshold
        if self.method == "ewma":
            self.stat[node] = c.lam * self.stat[node] + (1.0 - c.lam) * e
            return self.stat[node] > c.threshold
        buf = self.buf[node]
        buf.append(e)
        self.stat[node] = sum(buf) / len(buf)
        return len(buf) == buf.maxlen and self.stat[node] > c.threshold

    def observe(self, node: str, inconsistent: bool) -> bool:
        """Feed one audited observation. Returns True if it raised an alarm (same order as SleeperGuard)."""
        c, e = self.cfg, float(inconsistent)
        self.a[node] = c.lam_beta * self.a[node] + (1.0 - e)
        self.b[node] = c.lam_beta * self.b[node] + e
        if self.quarantine_left[node] > 0:
            self.quarantine_left[node] -= 1
            if self.quarantine_left[node] == 0:
                self.probation_left[node] = c.probation_steps
            return False
        if self.probation_left[node] > 0:
            self.probation_left[node] -= 1
        if self._update(node, e):
            self.stat[node] = 0.0
            self.buf[node].clear()
            self.quarantine_left[node] = c.quarantine_steps
            self.alarms[node] += 1
            return True
        return False

    def trust(self, node: str) -> float:
        p = self.cfg.prior
        return (self.a[node] + p) / (self.a[node] + self.b[node] + 2.0 * p)

    def is_quarantined(self, node: str) -> bool:
        return self.quarantine_left[node] > 0

    def weights(self, committee: List[str]) -> np.ndarray:
        return np.array([0.0 if self.is_quarantined(n) else self.trust(n)
                         * (self.cfg.probation_weight if self.probation_left[n] > 0 else 1.0)
                         for n in committee], dtype=float)
