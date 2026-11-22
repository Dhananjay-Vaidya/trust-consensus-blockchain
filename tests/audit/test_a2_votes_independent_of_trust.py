"""A2: votes must not be a function of trust."""
from __future__ import annotations

import inspect

import numpy as np

import src.consensus.tdcb as tdcb
from src.env.honest_env import HonestEnv
from tests.audit._util import small


def test_tdcb_does_not_generate_votes():
    src = inspect.getsource(tdcb)
    assert "_collect_votes" not in src and "trust_scores" not in src


def test_votes_identical_under_different_trust_backends():
    """Same seed, all nodes on the committee, different trust backends => identical votes."""
    votes = {}
    for tb in ("sleeper_guard", "legacy_beta", "none"):
        env = HonestEnv(small(trust_backend=tb, selection="all", attack="cra"))
        seen = []
        orig = env._world.cast_votes

        def spy(step, committee, _o=orig, _s=seen):
            v = _o(step, committee)
            _s.append(v.copy())
            return v

        env._world.cast_votes = spy
        env.run()
        votes[tb] = np.stack(seen)
    assert np.array_equal(votes["sleeper_guard"], votes["legacy_beta"])
    assert np.array_equal(votes["sleeper_guard"], votes["none"])
