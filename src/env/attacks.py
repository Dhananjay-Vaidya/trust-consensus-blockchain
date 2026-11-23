"""Adversary policies.  Part of the *simulated world*, not of the defended system.

Attacks act only through (a) the votes cast by coalition members, (b) timing, and (c) for the
adaptive briber, choosing which honest nodes to corrupt.  They receive no handle to any trust
backend (audit finding A3).  Like real Byzantine delegates they can verify transactions, so they
are given transaction validity; they observe the system only through ``PublicView``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np


@dataclass
class PublicView:
    """Everything a passive network observer sees after a step (signed votes are public)."""

    step: int
    committee: List[str]
    votes: np.ndarray                     # (T, k) public signed votes
    accept: np.ndarray                    # (T,) public commit decisions
    audited: np.ndarray                   # (T,) bool, which tx were audited (audit results are public)
    audit_outcome: np.ndarray             # (T,) audited validity (meaningless where not audited)
    weights: Optional[np.ndarray] = None  # only when the tally runs in plaintext (weights public)


class AttackPolicy:
    """Returns coalition votes; default = behave honestly."""

    name = "none"

    def __init__(self, intensity: float = 1.0) -> None:
        self.intensity = intensity

    def active(self, step: int) -> bool:
        return False

    def coalition_votes(self, step: int, validity: np.ndarray, honest_votes: np.ndarray,
                        rng: np.random.Generator) -> np.ndarray:
        """validity: (T,) bool; honest_votes: (T, m) what members would vote honestly."""
        return honest_votes

    def observe(self, view: PublicView, member_mask: np.ndarray) -> None:
        return None


def _inverted(validity: np.ndarray, honest_votes: np.ndarray, mask_t: np.ndarray) -> np.ndarray:
    """Coordinated inversion on the transactions selected by ``mask_t`` (T,)."""
    out = honest_votes.copy()
    out[mask_t, :] = (~validity[mask_t]).astype(float)[:, None]
    return out


class NMA(AttackPolicy):
    """Noise manipulation: each member votes a fair coin on a fraction ``intensity`` of tx."""

    name = "nma"

    def active(self, step: int) -> bool:
        return True

    def coalition_votes(self, step, validity, honest_votes, rng):
        noisy = rng.random(honest_votes.shape) < self.intensity
        coin = (rng.random(honest_votes.shape) < 0.5).astype(float)
        return np.where(noisy, coin, honest_votes)


class CRA(AttackPolicy):
    """Collusion: coordinated inversion (approve invalid, reject valid) on every step."""

    name = "cra"

    def active(self, step: int) -> bool:
        return True

    def coalition_votes(self, step, validity, honest_votes, rng):
        return _inverted(validity, honest_votes, rng.random(len(validity)) < self.intensity)


class TDP(AttackPolicy):
    """Trust-drift / sleeper: honest for ``t_switch`` steps, then coordinated inversion together."""

    name = "tdp"

    def __init__(self, t_switch: int, intensity: float = 1.0) -> None:
        super().__init__(intensity)
        self.t_switch = t_switch

    def active(self, step: int) -> bool:
        return step >= self.t_switch

    def coalition_votes(self, step, validity, honest_votes, rng):
        if not self.active(step):
            return honest_votes
        return _inverted(validity, honest_votes, rng.random(len(validity)) < self.intensity)


class AAA(AttackPolicy):
    """Adaptive on-off: attacks a fraction of tx; goes dormant for ``cooldown`` steps whenever a
    public audit shows a coalition member voting inconsistently (evades change detectors)."""

    name = "aaa"

    def __init__(self, intensity: float = 0.3, cooldown: int = 25) -> None:
        super().__init__(intensity)
        self.cooldown = cooldown
        self.sleep_until = -1
        self._step = 0

    def active(self, step: int) -> bool:
        return step >= self.sleep_until

    def coalition_votes(self, step, validity, honest_votes, rng):
        self._step = step
        if not self.active(step):
            return honest_votes
        return _inverted(validity, honest_votes, rng.random(len(validity)) < self.intensity)

    def observe(self, view: PublicView, member_mask: np.ndarray) -> None:
        if not member_mask.any() or not view.audited.any():
            return
        mv = view.votes[view.audited][:, member_mask]
        truth = view.audit_outcome[view.audited].astype(float)[:, None]
        if (mv != truth).any():
            self.sleep_until = view.step + 1 + self.cooldown


class BFI(AttackPolicy):
    """Byzantine fault injection: per step, w.p. ``intensity``, the coalition equivocates by
    approving everything (safety attack) or rejecting everything (liveness attack)."""

    name = "bfi"

    def active(self, step: int) -> bool:
        return True

    def coalition_votes(self, step, validity, honest_votes, rng):
        if rng.random() >= self.intensity:
            return honest_votes
        return np.full_like(honest_votes, 1.0 if rng.random() < 0.5 else 0.0)


class MaxDamage(AttackPolicy):
    """Damage-maximising coalition (replaces AAA in E2/E3).

    Every step, each transaction is selected with probability ``intensity`` (the lie rate) by ONE
    shared draw, so all coalition members lie on the SAME transactions (coordinated to reach the
    commit threshold).  target="invalid": approve selected invalid transactions only (safety attack;
    valid ones are voted honestly, which also minimises audit exposure).  target="both": invert
    selected transactions (safety + liveness).  The lie rate and coalition size are chosen by a
    search against each defence (experiments/exp_e11_adaptive.py), i.e. the attacker knows the
    defence's configuration (Kerckhoffs) and picks the rate just below its alarm.
    """

    name = "mda"

    def __init__(self, intensity: float = 0.1, target: str = "invalid") -> None:
        super().__init__(intensity)
        if target not in ("invalid", "both"):
            raise ValueError(target)
        self.target = target

    def active(self, step: int) -> bool:
        return True

    def coalition_votes(self, step, validity, honest_votes, rng):
        sel = rng.random(len(validity)) < self.intensity
        if self.target == "invalid":
            sel &= ~validity
        return _inverted(validity, honest_votes, sel)


def make_attack(name: str, t_switch: int, intensity: float, aaa_cooldown: int,
                target: str = "invalid") -> AttackPolicy:
    if name == "none":
        return AttackPolicy()
    if name == "nma":
        return NMA(intensity)
    if name == "cra":
        return CRA(intensity)
    if name == "tdp":
        return TDP(t_switch, intensity)
    if name == "aaa":
        return AAA(min(intensity, 0.3), aaa_cooldown)
    if name == "bfi":
        return BFI(intensity)
    if name == "mda":
        return MaxDamage(intensity, target)
    raise ValueError(f"unknown attack {name!r}")


# ---------------------------------------------------------------------------------------------
#  Adaptive briber (experiment E8, hypothesis H3)
# ---------------------------------------------------------------------------------------------
class AdaptiveBriber:
    """Chooses ``budget`` honest nodes to corrupt at ``t_bribe``.

    strategy="weights" : ranks nodes by the most recent public weights (plaintext tally only).
    strategy="votes"   : weights are hidden; ranks nodes by a public-data proxy: how often the
                         node's vote agreed with the committed outcome, times how often it sat on
                         the committee (both visible on the ledger).
    strategy="random"  : control.
    The briber never sees trust internals or ground truth beyond its own coalition membership.
    """

    def __init__(self, strategy: str, budget: int, t_bribe: int, nodes: Sequence[str]) -> None:
        if strategy not in ("weights", "votes", "random"):
            raise ValueError(strategy)
        self.strategy, self.budget, self.t_bribe = strategy, budget, t_bribe
        self.nodes = list(nodes)
        self.idx = {n: i for i, n in enumerate(self.nodes)}
        self.agree = np.zeros(len(self.nodes))
        self.seen = np.zeros(len(self.nodes))
        self.last_w = np.zeros(len(self.nodes))
        self.chosen: List[str] = []

    def observe(self, view: PublicView) -> None:
        ids = np.array([self.idx[n] for n in view.committee])
        agree = (view.votes == view.accept.astype(float)[:, None]).mean(axis=0)
        self.agree[ids] += agree
        self.seen[ids] += 1
        if view.weights is not None:
            self.last_w[:] = 0.0
            self.last_w[ids] = view.weights

    def choose(self, candidates: Sequence[str], rng: np.random.Generator) -> List[str]:
        cand = list(candidates)
        if self.strategy == "random":
            pick = rng.choice(len(cand), size=min(self.budget, len(cand)), replace=False)
            self.chosen = [cand[i] for i in pick]
            return self.chosen
        if self.strategy == "weights":
            score = np.array([self.last_w[self.idx[n]] for n in cand])
        else:
            score = np.array([self.agree[self.idx[n]] for n in cand])  # agreement x presence
        order = np.lexsort((rng.random(len(cand)), -score))           # random tie-break
        self.chosen = [cand[i] for i in order[: self.budget]]
        return self.chosen
