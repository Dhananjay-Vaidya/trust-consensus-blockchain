"""A8: disjoint seed splits, fresh env per episode, frozen deterministic evaluation."""
from __future__ import annotations

import pytest

from src.agents.d3p import D3PController
from src.agents.protocol import CALIB_SEEDS, EVAL_SEEDS, TRAIN_SEEDS, run_episode
from src.env.honest_env import HonestEnv
from tests.audit._util import small


def test_seed_sets_disjoint():
    assert not set(TRAIN_SEEDS) & set(CALIB_SEEDS)
    assert not set(TRAIN_SEEDS) & set(EVAL_SEEDS)
    assert not set(CALIB_SEEDS) & set(EVAL_SEEDS)
    assert len(EVAL_SEEDS) == 30


def test_env_cannot_continue_past_episode_end():
    env = HonestEnv(small(steps=5))
    env.run()
    with pytest.raises(RuntimeError):
        env.step()


def test_frozen_d3p_is_deterministic():
    c = D3PController(seed=0)
    run_episode(small(steps=60), c, learn=True)
    c.freeze()
    a = [r.knobs for r in run_episode(small(steps=40, seed=101), c).records]
    b = [r.knobs for r in run_episode(small(steps=40, seed=101), c).records]
    assert a == b
