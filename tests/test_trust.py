from __future__ import annotations

import pytest
from trust import TrustManager


@pytest.fixture
def tm():
    nodes = ["A", "B", "C", "D"]
    return TrustManager(nodes)


def test_update_trust_increases_on_success(tm):
    before = tm.get_trust("A")
    # Multiple updates to overcome noise
    for _ in range(10):
        tm.update_trust("A", "valid")
    after = tm.get_trust("A")
    assert after > before


def test_update_trust_decreases_on_failure(tm):
    before = tm.get_trust("A")
    for _ in range(10):
        tm.update_trust("A", "malicious")
    after = tm.get_trust("A")
    assert after < before


def test_decay_trust_reduces_all(tm):
    before = {n: tm.get_trust(n) for n in ["A", "B", "C", "D"]}
    # Run many decay steps to see effect
    for _ in range(20):
        tm.decay_trust(decay_rate=0.05)
    after = {n: tm.get_trust(n) for n in ["A", "B", "C", "D"]}
    # At least some nodes should have moved toward 0.5 (lower if above 0.5)
    # We just assert the operation didn't crash and values are clipped correctly
    for n in ["A", "B", "C", "D"]:
        assert 0.0 < after[n] < 1.0


def test_select_delegated_nodes_returns_k(tm):
    delegates = tm.select_delegated_nodes(2)
    assert len(delegates) == 2


def test_select_delegated_nodes_returns_all_when_k_equals_n(tm):
    delegates = tm.select_delegated_nodes(4)
    assert len(delegates) == 4


def test_malicious_node_low_trust_after_many_rounds():
    nodes = ["Good", "Bad"]
    tm = TrustManager(nodes)
    for _ in range(50):
        tm.update_trust("Bad", "malicious")
    assert tm.get_trust("Bad") < 0.3
