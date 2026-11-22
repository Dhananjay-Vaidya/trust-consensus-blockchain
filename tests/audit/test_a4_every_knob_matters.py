"""A4: every action knob changes a downstream quantity."""
from __future__ import annotations

import importlib

import numpy as np
import pytest

from src.env.honest_env import KNOB_LEVELS, KNOB_NAMES, N_ACTIONS, HonestEnv, Knobs
from tests.audit._util import small


def _run(kn: Knobs) -> HonestEnv:
    env = HonestEnv(small(committee_size=12, num_nodes=16, attack="cra"))
    while not env.done:
        env.step(kn)
    return env


def test_action_space_is_full_product():
    assert N_ACTIONS == 3 ** len(KNOB_NAMES) == 81


@pytest.mark.parametrize("knob", KNOB_NAMES)
def test_each_knob_changes_a_downstream_metric(knob):
    base = dict(committee_frac=0.75, audit_rate=0.2, temperature=0.2, theta_margin=0.0)
    outs = []
    for level in KNOB_LEVELS[knob]:
        kw = dict(base)
        kw[knob] = level
        env = _run(Knobs(**kw))
        outs.append((
            float(np.mean([len(r.committee_idx) for r in env.records])),
            int(np.sum([r.n_audited for r in env.records])),
            tuple(np.concatenate([r.committee_idx for r in env.records]).tolist()),
            int(np.sum([r.accept.sum() for r in env.records])),
        ))
    assert len(set(outs)) == 3, f"knob {knob} levels produced identical downstream outcomes"


def test_old_dead_knobs_are_gone():
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("parameters")
