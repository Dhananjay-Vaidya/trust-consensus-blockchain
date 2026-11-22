from __future__ import annotations

import sys
import os

# Ensure the project root is on the path when running tests from within tests/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest


@pytest.fixture
def node_list() -> list:
    return [f"Node_{i}" for i in range(4)]


@pytest.fixture
def trust_manager(node_list):
    from src.trust.trust import TrustManager
    return TrustManager(node_list)


@pytest.fixture
def blockchain():
    from src.blockchain.blockchain import Blockchain
    bc = Blockchain(difficulty=1)  # low difficulty for speed
    return bc
