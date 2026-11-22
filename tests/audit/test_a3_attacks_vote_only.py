"""A3: attacks act only through votes and timing; they hold no trust handle."""
from __future__ import annotations

import inspect

import src.env.attacks as attacks


def test_attack_module_never_touches_trust():
    src = inspect.getsource(attacks)
    for bad in ("update_trust", "adjust_trust", "trust_manager", "beta_param", "SleeperGuard", "TrustBackend"):
        assert bad not in src, bad


def test_attack_policy_signature_has_no_trust_argument():
    for cls in (attacks.NMA, attacks.CRA, attacks.TDP, attacks.AAA, attacks.BFI, attacks.MaxDamage):
        params = inspect.signature(cls.coalition_votes).parameters
        assert set(params) == {"self", "step", "validity", "honest_votes", "rng"}
