"""A1: decisions and rewards must not depend on ground truth.

Runtime check: every ground-truth accessor of the world raises while the env steps.
The environment, trust backend, tally and reward must still run; only metrics may read labels.
"""
from __future__ import annotations

import importlib

import numpy as np
import pytest

from src.env.honest_env import HonestEnv
from src.metrics.ground_truth_metrics import summarize
from tests.audit._util import small


def test_env_runs_with_ground_truth_record_blocked(monkeypatch):
    env = HonestEnv(small())

    def boom(*a, **k):
        raise AssertionError("ground truth read during a decision step")

    monkeypatch.setattr(env._world, "ground_truth_record", boom)
    for _ in range(env.cfg.steps):
        env.step()
    monkeypatch.undo()
    assert summarize(env)["det_f1"] >= 0.0


def test_reward_and_decisions_invariant_to_hidden_labels_given_same_public_inputs():
    """Two worlds that produce identical votes and audits but label different nodes as adversarial
    must yield identical decisions, trust and rewards."""
    a = HonestEnv(small(attack="none"))
    b = HonestEnv(small(attack="none"))
    b._world.coalition = set(b.nodes[:3])   # labels differ; behaviour (attack 'none') identical
    a.run()
    b.run()
    for ra, rb in zip(a.records, b.records):
        assert ra.reward == rb.reward
        assert np.array_equal(ra.accept, rb.accept)
        assert np.array_equal(ra.trust, rb.trust)


def test_old_oracle_modules_are_gone():
    for mod in ["src.rewards.reward", "src.simulation.simulation_manager"]:
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(mod)
