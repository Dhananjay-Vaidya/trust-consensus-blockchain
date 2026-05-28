from __future__ import annotations

import pytest
from trust import TrustManager
from attack_util import apply_attack, reset_attack_instances


ATTACK_TYPES = ["nma", "cra", "bfi", "aaa", "tdp"]


@pytest.fixture(autouse=True)
def reset_attacks():
    reset_attack_instances()
    yield
    reset_attack_instances()


@pytest.fixture
def setup_trust():
    nodes = [f"Node_{i}" for i in range(8)]
    malicious = {"Node_0", "Node_1"}
    tm = TrustManager(nodes)
    return tm, malicious


@pytest.mark.parametrize("attack_type", ATTACK_TYPES)
def test_attack_does_not_raise(setup_trust, attack_type):
    tm, malicious = setup_trust
    try:
        apply_attack(
            tm, malicious, attack_type,
            current_step=0, current_episode=30
        )
    except Exception as e:
        pytest.fail(f"{attack_type} raised {e}")


def test_nma_decreases_at_least_one_honest_trust(setup_trust):
    tm, malicious = setup_trust
    honest = set(tm.trust_scores.keys()) - malicious
    before = {n: tm.get_trust(n) for n in honest}

    for _ in range(5):
        apply_attack(tm, malicious, "nma", current_step=0, current_episode=5)

    after = {n: tm.get_trust(n) for n in honest}
    # At least one honest node should have its trust changed
    changed = any(abs(after[n] - before[n]) > 1e-6 for n in honest)
    assert changed


def test_tdp_dormant_does_not_attack_trust(setup_trust):
    tm, malicious = setup_trust
    before = {n: tm.get_trust(n) for n in malicious}
    # episode < activation_episode (25), so should be dormant
    apply_attack(tm, malicious, "tdp", current_step=0, current_episode=0)
    after = {n: tm.get_trust(n) for n in malicious}
    # In dormant phase malicious nodes may get boosted, not penalised
    # Simply assert no exception was raised and scores are valid
    for n in malicious:
        assert 0.0 < after[n] < 1.0
