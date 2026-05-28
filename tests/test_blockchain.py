from __future__ import annotations

import pytest
from blockchain import Blockchain


@pytest.fixture
def bc():
    return Blockchain(difficulty=1)


def test_add_transaction_increases_pending(bc):
    before = len(bc.pending_transactions)
    bc.add_transaction({"sender": "A", "recipient": "B", "amount": 5.0})
    assert len(bc.pending_transactions) == before + 1


def test_mine_pending_creates_block_and_clears_pool(bc):
    bc.add_transaction({"sender": "A", "recipient": "B", "amount": 1.0})
    bc.add_transaction({"sender": "B", "recipient": "C", "amount": 2.0})
    chain_len_before = len(bc.chain)
    bc.mine_pending_transactions(miner_address="miner")
    assert len(bc.chain) == chain_len_before + 1
    assert len(bc.pending_transactions) == 0


def test_is_chain_valid_fresh_chain(bc):
    bc.add_transaction({"sender": "X", "recipient": "Y", "amount": 3.0})
    bc.mine_pending_transactions(miner_address="miner")
    assert bc.is_chain_valid() is True


def test_is_chain_valid_tampered_returns_false(bc):
    bc.add_transaction({"sender": "X", "recipient": "Y", "amount": 3.0})
    bc.mine_pending_transactions(miner_address="miner")
    # Tamper with a block's transactions
    bc.chain[1].transactions = [{"sender": "HACKER", "recipient": "HACKER", "amount": 9999}]
    assert bc.is_chain_valid() is False


def test_invalid_transaction_not_added(bc):
    before = len(bc.pending_transactions)
    bc.add_transaction({"sender": "A"})  # Missing required fields
    assert len(bc.pending_transactions) == before
