"""E14 change-detection baselines: no label access, closed-form statistics, SleeperGuard's quarantine timing."""
from __future__ import annotations

import inspect
import re

import numpy as np
import pytest

import src.trust.detectors as det_mod
from src.config.run_config import RunConfig
from src.env.honest_env import HonestEnv
from src.trust.detectors import ChangeDetector, DetectorConfig
from src.trust.sleeper_guard import SleeperGuard, SleeperGuardConfig

TOY = [0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 1, 1]


def test_detectors_never_read_labels():
    src = inspect.getsource(det_mod)
    for pat in (r"\b_world\b", r"\bcoalition\b", r"\bvalidity\b", r"ground_truth", r"true_malicious", r"bribed_at"):
        assert not re.search(pat, src), pat
    # the only evidence entry point is observe(node, inconsistent)
    assert list(inspect.signature(ChangeDetector.observe).parameters) == ["self", "node", "inconsistent"]


@pytest.mark.parametrize("backend", ["cusum", "ewma", "window"])
def test_backend_runs_in_env_and_is_deterministic(backend):
    cfg = RunConfig(seed=5, steps=150, t_switch=75, attack="tdp", trust_backend=backend)
    a, b = HonestEnv(cfg).run(), HonestEnv(cfg).run()
    assert all(np.array_equal(x.trust, y.trust) and x.alarms == y.alarms for x, y in zip(a.records, b.records))


def test_cusum_matches_closed_form():
    r, h = 0.3, 1.5
    d = ChangeDetector(["n"], "cusum", DetectorConfig(reference=r, threshold=h))
    s, expect_alarm = 0.0, None
    for i, e in enumerate(TOY):
        s = max(0.0, s + e - r)
        if s > h:
            expect_alarm = i
            break
    got = next(i for i, e in enumerate(TOY) if d.observe("n", bool(e)))
    assert got == expect_alarm
    # before the alarm the statistic equals the recursion
    d2 = ChangeDetector(["n"], "cusum", DetectorConfig(reference=r, threshold=1e9))
    s = 0.0
    for e in TOY:
        d2.observe("n", bool(e))
        s = max(0.0, s + e - r)
        assert d2.stat["n"] == pytest.approx(s)


def test_ewma_matches_closed_form():
    lam = 0.8
    d = ChangeDetector(["n"], "ewma", DetectorConfig(lam=lam, threshold=1e9))
    for t, _ in enumerate(TOY, start=1):
        d.observe("n", bool(TOY[t - 1]))
        closed = (1 - lam) * sum(lam ** (t - i) * TOY[i - 1] for i in range(1, t + 1))
        assert d.stat["n"] == pytest.approx(closed)


def test_window_mean_and_alarm_only_when_full():
    d = ChangeDetector(["n"], "window", DetectorConfig(window=4, threshold=0.6))
    alarms = [d.observe("n", bool(e)) for e in [1, 1, 1]]
    assert alarms == [False, False, False]          # window not yet full
    assert d.observe("n", True) is True             # 4/4 > 0.6


def _q_profile(obj, seq):
    """(observations quarantined after the first alarm, observations on probation after that)."""
    alarm_i = next(i for i, e in enumerate(seq) if obj.observe("n", bool(e)))
    q = p = 0
    for _ in range(200):
        quar = obj.is_quarantined("n")
        prob = obj.probation_left["n"] > 0
        obj.observe("n", False)
        q += quar
        p += (not quar) and prob
    return alarm_i, q, p


@pytest.mark.parametrize("method,cfg", [("cusum", DetectorConfig(reference=0.2, threshold=2.0)),
                                        ("ewma", DetectorConfig(lam=0.8, threshold=0.5)),
                                        ("window", DetectorConfig(window=5, threshold=0.5))])
def test_quarantine_timing_equals_sleeperguard(method, cfg):
    seq = [0] * 40 + [1] * 40
    _, q_sg, p_sg = _q_profile(SleeperGuard(["n"], SleeperGuardConfig()), seq)
    _, q_d, p_d = _q_profile(ChangeDetector(["n"], method, cfg), seq)
    assert (q_d, p_d) == (q_sg, p_sg) == (50, 30)
    w = ChangeDetector(["n"], method, cfg)
    for e in seq:
        if w.observe("n", bool(e)):
            break
    assert w.weights(["n"])[0] == 0.0               # quarantined -> zero weight, no cap applied
