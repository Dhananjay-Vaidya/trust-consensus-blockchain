"""Imperfect audits (E16): defaults change nothing; error rate and delay behave as specified."""
from __future__ import annotations

import numpy as np
import pytest

from src.config.run_config import RunConfig
from src.env.honest_env import HonestEnv
from src.env.world import World


def _run(**kw) -> HonestEnv:
    return HonestEnv(RunConfig(seed=11, steps=120, t_switch=60, attack="tdp", **kw)).run()


def test_explicit_defaults_are_bit_identical():
    a, b = _run(), _run(audit_error_rate=0.0, audit_delay=0)
    for ra, rb in zip(a.records, b.records):
        assert np.array_equal(ra.accept, rb.accept) and np.array_equal(ra.trust, rb.trust)
        assert ra.alarms == rb.alarms


def test_audit_error_rate_flips_verdicts_at_the_stated_rate():
    rng = np.random.default_rng(0)
    w = World(["a"], set(), None, 0.3, 0.0, rng, audit_error_rate=0.1,  # type: ignore[arg-type]
              audit_rng=np.random.default_rng(1))
    flips = n = 0
    for _ in range(400):
        w.new_transactions(50)
        truth = w._validity.copy()
        out = w.audit(np.ones(50, dtype=bool))
        flips += int((out != truth).sum())
        n += 50
    assert 0.08 < flips / n < 0.12


def test_audit_error_needs_its_own_rng_and_is_validated():
    with pytest.raises(ValueError):
        RunConfig(audit_error_rate=0.5).validate()
    with pytest.raises(ValueError):
        RunConfig(audit_delay=-1).validate()
    noisy = _run(audit_error_rate=0.1)
    assert any(not np.array_equal(r.trust, q.trust) for r, q in zip(noisy.records, _run().records))


def test_audit_delay_holds_back_all_evidence():
    env = HonestEnv(RunConfig(seed=11, steps=120, t_switch=60, attack="tdp", audit_delay=10))
    for _ in range(10):
        r = env.step()
        # nothing audited has arrived yet: no per-delegate evidence, no audited error, no alarms
        assert env._dis_den.sum() == 0.0 and np.isnan(r.audited_err) and r.alarms == []
    r = env.step()                     # step 10 receives the verdicts audited at step 0
    assert env._dis_den.sum() > 0.0 and not np.isnan(r.audited_err)
    assert len(env._pending_audits) == 10
