"""The simulated world: the ONLY place (besides ``src/metrics``) that holds ground truth.

``HonestEnv`` (the defended system) asks the world for transactions, votes and audit results.
It never reads transaction validity or node behaviour types directly.  Ground truth is exposed
to ``src/metrics/ground_truth_metrics.py`` through :meth:`World.ground_truth_record`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set

import numpy as np

from src.env.attacks import AttackPolicy, PublicView


@dataclass
class _StepTruth:
    validity: np.ndarray                  # (T,) bool
    coalition_active: bool
    coalition: Set[str]


@dataclass
class World:
    nodes: List[str]
    coalition: Set[str]                   # private behaviour type: adversary-controlled nodes
    attack: AttackPolicy
    invalid_tx_rate: float
    honest_fault_rate: float
    rng: np.random.Generator
    _truth: List[_StepTruth] = field(default_factory=list)
    _validity: Optional[np.ndarray] = None
    bribed_at: Dict[str, int] = field(default_factory=dict)

    # -- called by HonestEnv ---------------------------------------------------------------
    def new_transactions(self, t_count: int) -> int:
        """Generate this step's transactions; returns only their count (ids are 0..T-1)."""
        self._validity = self.rng.random(t_count) >= self.invalid_tx_rate
        return t_count

    def cast_votes(self, step: int, committee: Sequence[str]) -> np.ndarray:
        """Public signed votes (T, k): honest members vote on a noisy observation of validity;
        coalition members follow the attack policy.  Votes never depend on trust (A2)."""
        assert self._validity is not None
        val = self._validity
        k = len(committee)
        flips = self.rng.random((len(val), k)) < self.honest_fault_rate
        honest = (val[:, None] ^ flips).astype(float)
        member = np.array([n in self.coalition for n in committee], dtype=bool)
        if member.any():
            honest[:, member] = self.attack.coalition_votes(step, val, honest[:, member], self.rng)
        self._truth.append(_StepTruth(val.copy(), self.attack.active(step), set(self.coalition)))
        return honest

    def audit(self, audited: np.ndarray) -> np.ndarray:
        """Independent re-verification (signature / rule check) of the sampled transactions.
        Returns the audited validity; entries for non-audited tx are 0 and must be ignored."""
        assert self._validity is not None
        return np.where(audited, self._validity, False)

    def publish(self, view: PublicView) -> None:
        member = np.array([n in self.coalition for n in view.committee], dtype=bool)
        self.attack.observe(view, member)

    def corrupt(self, nodes: Sequence[str], step: int) -> None:
        for n in nodes:
            self.coalition.add(n)
            self.bribed_at[n] = step

    # -- called ONLY by src/metrics --------------------------------------------------------
    def ground_truth_record(self) -> List[_StepTruth]:
        return self._truth
