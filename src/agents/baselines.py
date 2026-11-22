"""Baseline protocols as RunConfig presets on the *same* environment, seeds and audit budget.

Every baseline gets identical audit evidence; the non-trust baselines simply ignore it.
"""
from __future__ import annotations

from typing import Dict

from src.config.run_config import RunConfig

# name -> overrides applied on top of the experiment's base RunConfig
BASELINES: Dict[str, Dict[str, object]] = {
    # one-node-one-vote over all nodes, 2/3 quorum
    "pbft": dict(trust_backend="none", weighted=False, selection="all", theta=2 / 3),
    # fixed committee chosen once at genesis ("stake" snapshot), 2/3 of the committee
    "static_dpos": dict(trust_backend="none", weighted=False, selection="fixed", committee_size=8, theta=2 / 3),
    # all nodes, simple majority
    "majority": dict(trust_backend="none", weighted=False, selection="all", theta=0.5),
    # fresh uniformly random committee every step, 2/3 quorum
    "random_delegates": dict(trust_backend="none", weighted=False, selection="random", committee_size=8, theta=2 / 3),
    # base protocol: trust-weighted tally with legacy Beta trust (oracle-free)
    "legacy_beta": dict(trust_backend="legacy_beta", weighted=True, selection="trust_softmax"),
    # proposed
    "sleeper_guard": dict(trust_backend="sleeper_guard", weighted=True, selection="trust_softmax"),
}


def baseline_config(name: str, base: RunConfig) -> RunConfig:
    return base.with_overrides(**BASELINES[name])
