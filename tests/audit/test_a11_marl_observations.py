"""A11: each factored learner has its own observation; no fake attention."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from src.agents.factored import FactoredController
from src.env.honest_env import KNOB_NAMES, HonestEnv
from tests.audit._util import small

ROOT = Path(__file__).resolve().parents[2]


def test_per_agent_observations_differ():
    c = FactoredController(seed=0)
    obs = HonestEnv(small()).observation()
    vecs = [c.agent_observation(obs, n, i % 3) for i, n in enumerate(KNOB_NAMES)]
    assert len({v.tobytes() for v in vecs}) > 1
    assert len(c.learners) == len(KNOB_NAMES)


def test_no_attention_in_agents():
    for p in (ROOT / "src" / "agents").glob("*.py"):
        assert "MultiheadAttention" not in p.read_text(encoding="utf-8")


def test_each_learner_sets_its_own_knob():
    c = FactoredController(seed=1)
    obs = HonestEnv(small()).observation()
    k = c.act(obs)
    assert all(getattr(k, n) is not None for n in KNOB_NAMES)
    assert np.isfinite(obs.vector()).all()
