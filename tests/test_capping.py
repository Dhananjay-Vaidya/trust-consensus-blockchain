"""Share cap: the exact water-filling always meets the cap; the provided iterative one may not."""
from __future__ import annotations

import numpy as np
import pytest

from src.config.run_config import RunConfig
from src.env.honest_env import HonestEnv
from src.trust.capping import cap_shares_exact
from src.trust.sleeper_guard import cap_shares


def _random_feasible(rng, k, c):
    while True:
        w = rng.random(k) ** rng.uniform(0.2, 8)
        if rng.random() < 0.3:
            w[rng.random(k) < 0.3] = 0.0
        if (w > 0).sum() * c / k >= 1:
            return w


@pytest.mark.parametrize("k,c", [(4, 1.25), (8, 2.0), (16, 1.5), (16, 2.0), (32, 2.0), (64, 3.0)])
def test_exact_cap_always_enforced_and_mass_preserved(k, c):
    rng = np.random.default_rng(k)
    for _ in range(500):
        w = _random_feasible(rng, k, c)
        o = cap_shares_exact(w, c / k)
        assert o.max() <= c / k * o.sum() * (1 + 1e-9)
        assert o.sum() == pytest.approx(w.sum())
        assert np.all(o[w == 0] == 0)
        # order-preserving and no node above the cap was left uncapped
        assert np.all(np.diff(o[np.argsort(w)]) >= -1e-12)


def test_exact_cap_is_identity_when_already_feasible():
    w = np.ones(8)
    assert np.allclose(cap_shares_exact(w, 2 / 8), w)


def test_exact_cap_infeasible_returns_input():
    w = np.array([1.0, 1.0, 0.0, 0.0])
    assert np.array_equal(cap_shares_exact(w, 0.25), w)


def test_provided_iterative_cap_can_overshoot():
    """Characterisation of a defect in the provided code (kept for the ablation)."""
    w = np.array([1.0, 1.0, 0.01, 1e-3])
    o = cap_shares(w, 1.25 / 4)
    assert o.max() / o.sum() > 1.25 / 4 + 1e-3


def test_env_cap_methods_selectable():
    for m in ("exact", "verified_iterative"):
        env = HonestEnv(RunConfig(seed=1, steps=30, t_switch=10, cap_method=m)).run()
        assert len(env.records) == 30
