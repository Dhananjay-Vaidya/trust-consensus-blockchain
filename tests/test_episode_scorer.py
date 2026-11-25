"""episode_snapshot_scores: defaults reproduce the environment's flag rule; new parameters behave."""
from __future__ import annotations

from src.config.run_config import RunConfig
from src.env.honest_env import HonestEnv
from src.metrics.ground_truth_metrics import _prf, episode_snapshot_scores


def _env(tb: str) -> HonestEnv:
    return HonestEnv(RunConfig(seed=4, steps=400, t_switch=200, attack="tdp", trust_backend=tb)).run()


def test_defaults_equal_recorded_flags():
    env = _env("sleeper_guard")
    co = env._world.coalition
    y = [int(n in co) for n in env.nodes]
    got = episode_snapshot_scores(env, 100)
    for row, end in zip(got, range(99, 400, 100)):
        assert row["f1"] == _prf(__import__("numpy").array(y), env.records[end].flagged.astype(int))["f1"]


def test_threshold_and_quarantine_switches():
    env = _env("sleeper_guard")
    strict = episode_snapshot_scores(env, 100, flag_threshold=0.0, count_quarantine_as_flag=False)
    assert all(r["f1"] == 0.0 for r in strict)          # nothing can be flagged
    loose = episode_snapshot_scores(env, 100, flag_threshold=1.01, count_quarantine_as_flag=False)
    assert all(r["recall"] == 1.0 for r in loose)        # everything flagged
