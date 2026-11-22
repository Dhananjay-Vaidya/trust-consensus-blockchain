"""Controller protocol, seed splits and the train / calibrate / evaluate loop (A8).

A controller maps the public :class:`Observation` to :class:`Knobs` every ``control_every`` steps.
Learning controllers are trained on TRAIN_SEEDS only, tuned on CALIB_SEEDS, and evaluated with a
frozen greedy policy on EVAL_SEEDS.  No ground truth reaches a controller: the reward is
``StepRecord.reward`` (audited agreement, latency and audit cost).
"""
from __future__ import annotations

from typing import Callable, Iterable, List, Optional

import numpy as np

from src.config.run_config import RunConfig
from src.env.honest_env import HonestEnv, Knobs, Observation

TRAIN_SEEDS = tuple(range(0, 20))
CALIB_SEEDS = tuple(range(20, 30))
EVAL_SEEDS = tuple(range(100, 130))
TRAIN_ATTACKS = ("tdp", "cra", "aaa", "nma", "bfi", "none")


class Controller:
    name = "fixed"
    control_every = 10

    def act(self, obs: Observation, explore: bool = False) -> Knobs:
        return Knobs()

    # learning hooks (no-ops for non-learning controllers)
    def observe_transition(self, obs: Observation, action: Knobs, reward: float,
                           next_obs: Observation, done: bool) -> None:
        return None

    def freeze(self) -> None:
        return None


def run_episode(cfg: RunConfig, ctrl: Controller, learn: bool = False,
                env_factory: Optional[Callable[[RunConfig], HonestEnv]] = None) -> HonestEnv:
    env = (env_factory or HonestEnv)(cfg)
    obs = env.observation()
    knobs = ctrl.act(obs, explore=learn)
    acc: List[float] = []
    while not env.done:
        rec = env.step(knobs)
        acc.append(rec.reward)
        if env.t % ctrl.control_every == 0 or env.done:
            nobs = env.observation()
            if learn:
                ctrl.observe_transition(obs, knobs, float(np.mean(acc)), nobs, env.done)
            acc = []
            obs = nobs
            if not env.done:
                knobs = ctrl.act(obs, explore=learn)
    return env


def train(ctrl: Controller, base: RunConfig, seeds: Iterable[int] = TRAIN_SEEDS, epochs: int = 3,
          attacks: Iterable[str] = TRAIN_ATTACKS) -> None:
    atk = list(attacks)
    for ep in range(epochs):
        for i, s in enumerate(seeds):
            run_episode(base.with_overrides(seed=s, attack=atk[(i + ep) % len(atk)]), ctrl, learn=True)
    ctrl.freeze()
