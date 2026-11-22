"""Independent learners over a factored action space (replaces the old "MARL + attention", A11).

One dueling-double-DQN learner per knob (committee size, audit rate, selection temperature,
threshold margin), 3 actions each.  Each learner has its OWN observation: the shared public
features plus a one-hot of its own current knob level, and all share the team reward.  This is
cooperative independent Q-learning; we do not claim attention-based coordination.
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np

from src.agents.d3p import DQNLearner, _knob_value
from src.agents.protocol import Controller
from src.env.honest_env import KNOB_LEVELS, KNOB_NAMES, OBS_DIM, Knobs, Observation


class FactoredController(Controller):
    name = "marl_factored"

    def __init__(self, seed: int = 0) -> None:
        self.learners: Dict[str, DQNLearner] = {
            n: DQNLearner(OBS_DIM + 3, 3, seed * 31 + i) for i, n in enumerate(KNOB_NAMES)
        }
        self._levels: Dict[str, int] = {n: 1 for n in KNOB_NAMES}

    def agent_observation(self, obs: Observation, knob: str, level: int) -> np.ndarray:
        onehot = np.zeros(3, dtype=np.float32)
        onehot[level] = 1.0
        return np.concatenate([obs.vector(), onehot])

    def act(self, obs: Observation, explore: bool = False) -> Knobs:
        new: Dict[str, int] = {}
        for n, L in self.learners.items():
            new[n] = L.act(self.agent_observation(obs, n, self._levels[n]))
        self._prev_levels = dict(self._levels)
        self._levels = new
        return Knobs.from_levels([new[n] for n in KNOB_NAMES])

    def observe_transition(self, obs, action, reward, next_obs, done) -> None:
        for n, L in self.learners.items():
            a = KNOB_LEVELS[n].index(_knob_value(action, n))
            s = self.agent_observation(obs, n, self._prev_levels.get(n, 1))
            s2 = self.agent_observation(next_obs, n, a)
            L.push(s, a, reward, s2, done)

    def freeze(self) -> None:
        for L in self.learners.values():
            L.freeze()

    def observation_dims(self) -> List[int]:
        return [OBS_DIM + 3 for _ in self.learners]
