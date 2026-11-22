"""Non-deep controllers: a hand-tuned rule policy (strong non-learning baseline) and tabular Q."""
from __future__ import annotations

from typing import Dict, Tuple

import numpy as np

from src.agents.d3p import _knob_value
from src.agents.protocol import Controller
from src.env.honest_env import ACTIONS, KNOB_LEVELS, KNOB_NAMES, N_ACTIONS, Knobs, Observation


class RuleController(Controller):
    """Escalate on observable trouble, relax when quiet.

    trouble := recent audited decision error > err_hi, or any recent change alarm.
      trouble -> full committee, audit 0.4, low temperature, +0.05 threshold margin
      quiet   -> 75% committee, audit 0.1, temperature 0.2, no margin
      else    -> full committee, audit 0.2, temperature 0.2, no margin
    ``err_hi`` / ``err_lo`` are the only parameters; they are tuned on CALIB_SEEDS (exp E9).
    """

    name = "rule"

    def __init__(self, err_hi: float = 0.05, err_lo: float = 0.01) -> None:
        self.err_hi, self.err_lo = err_hi, err_lo

    def act(self, obs: Observation, explore: bool = False) -> Knobs:
        if obs.audited_err_recent > self.err_hi or obs.alarms_recent > 0:
            return Knobs(1.0, 0.4, 0.05, 0.05)
        if obs.audited_err_recent < self.err_lo and obs.step_frac > 0.05:
            return Knobs(0.75, 0.1, 0.2, 0.0)
        return Knobs(1.0, 0.2, 0.2, 0.0)


class TabularQController(Controller):
    """Q-learning on a coarse discretisation of (recent audited error, alarms, quarantined)."""

    name = "tabular_q"

    def __init__(self, seed: int = 0, alpha: float = 0.2, gamma: float = 0.9,
                 eps0: float = 0.5, eps_min: float = 0.05, eps_decay: float = 0.995) -> None:
        self.rng = np.random.default_rng(seed)
        self.q: Dict[Tuple[int, int, int], np.ndarray] = {}
        self.alpha, self.gamma = alpha, gamma
        self.eps, self.eps_min, self.eps_decay = eps0, eps_min, eps_decay
        self.frozen = False

    @staticmethod
    def _state(o: Observation) -> Tuple[int, int, int]:
        e = int(np.digitize(o.audited_err_recent, [0.01, 0.05, 0.15]))
        a = int(o.alarms_recent > 0)
        qn = int(np.digitize(o.frac_quarantined, [0.01, 0.2]))
        return (e, a, qn)

    def _row(self, s: Tuple[int, int, int]) -> np.ndarray:
        if s not in self.q:
            self.q[s] = np.zeros(N_ACTIONS)
        return self.q[s]

    def act(self, obs: Observation, explore: bool = False) -> Knobs:
        row = self._row(self._state(obs))
        if explore and not self.frozen and self.rng.random() < self.eps:
            a = int(self.rng.integers(N_ACTIONS))
        else:
            a = int(np.flatnonzero(row == row.max())[0])
        return Knobs.from_action(a)

    def observe_transition(self, obs, action, reward, next_obs, done) -> None:
        a = ACTIONS.index(tuple(KNOB_LEVELS[n].index(_knob_value(action, n)) for n in KNOB_NAMES))
        s, s2 = self._state(obs), self._state(next_obs)
        target = reward + (0.0 if done else self.gamma * self._row(s2).max())
        self._row(s)[a] += self.alpha * (target - self._row(s)[a])
        self.eps = max(self.eps_min, self.eps * self.eps_decay)

    def freeze(self) -> None:
        self.frozen = True
