from __future__ import annotations

import numpy as np

from src.stats.paired import bootstrap_ci, cliffs_delta, holm, paired_compare
from src.trust.sleeper_guard import SleeperGuard, SleeperGuardConfig, cap_shares


def test_cap_shares_infeasible_is_left_unchanged():
    w = np.array([1.0, 1.0, 0.0, 0.0])
    assert np.array_equal(cap_shares(w, 0.1), w)


def test_sleeper_switch_triggers_quarantine_and_honest_does_not():
    sg = SleeperGuard(["h", "s"], SleeperGuardConfig())
    rng = np.random.default_rng(0)
    for _ in range(300):
        sg.observe("h", rng.random() < 0.02)
        sg.observe("s", rng.random() < 0.02)
    for i in range(20):
        sg.observe("h", rng.random() < 0.02)
        if sg.observe("s", True):
            break
    assert sg.is_quarantined("s") and i < 10
    assert sg.alarms["h"] == 0
    w = sg.weights(["h", "s"])
    assert w[1] == 0.0


def test_ablation_flags_are_respected():
    sg = SleeperGuard(["a"], SleeperGuardConfig(use_cusum=False))
    for _ in range(50):
        assert not sg.observe("a", True)


def test_stats_helpers():
    x = np.arange(30, dtype=float)
    y = x - 1.0
    r = paired_compare("m", "x", x, "y", y)
    assert r.median_diff == 1.0 and r.p_value < 0.001 and r.cliffs_delta > 0
    holm([r])
    assert r.significant
    lo, hi = bootstrap_ci(x)
    assert lo < np.median(x) < hi
    assert cliffs_delta([1, 2], [1, 2]) == 0.0
