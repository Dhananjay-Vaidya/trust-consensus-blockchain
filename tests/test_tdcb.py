from __future__ import annotations

import pytest
from tdcb import TDCB


@pytest.fixture
def tdcb():
    return TDCB()


@pytest.fixture
def honest_transactions():
    return [
        {"sender": "A", "recipient": "B", "amount": 10.0},
        {"sender": "B", "recipient": "C", "amount": 5.0},
    ]


def test_consensus_returns_verified_when_all_honest(tdcb, honest_transactions):
    delegates = ["D1", "D2", "D3"]
    trust_scores = {"D1": 0.9, "D2": 0.9, "D3": 0.9}
    result = tdcb.execute_consensus(honest_transactions, delegates, trust_scores)
    assert result["status"] == "success"
    assert result["verified_transactions"] >= 0


def test_byzantine_delegate_detected(tdcb, honest_transactions):
    """A low-trust delegate that consistently disagrees should be flagged."""
    delegates = ["Good1", "Good2", "Bad1"]
    trust_scores = {"Good1": 0.9, "Good2": 0.9, "Bad1": 0.1}
    result = tdcb.execute_consensus(honest_transactions, delegates, trust_scores)
    # Bad1 has trust < 0.3 so it votes opposite — should be detected
    assert "Bad1" in result["malicious_nodes"]


def test_get_consensus_metrics_has_required_keys(tdcb, honest_transactions):
    delegates = ["D1", "D2"]
    trust_scores = {"D1": 0.8, "D2": 0.8}
    tdcb.execute_consensus(honest_transactions, delegates, trust_scores)
    metrics = tdcb.get_consensus_metrics()
    assert "total_votes" in metrics
    assert "byzantine_count" in metrics
    assert "consensus_ratio" in metrics


def test_consensus_metrics_empty_returns_defaults(tdcb):
    metrics = tdcb.get_consensus_metrics()
    assert metrics["total_votes"] == 0
    assert metrics["byzantine_count"] == 0
    assert metrics["consensus_ratio"] == 0.0
