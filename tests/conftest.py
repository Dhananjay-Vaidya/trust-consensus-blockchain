from __future__ import annotations

import sys
import os

# Ensure the project root is on the path when running tests from within tests/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from config.config_loader import SimConfig


@pytest.fixture
def small_config() -> SimConfig:
    """Minimal SimConfig for fast test runs."""
    cfg = SimConfig()
    cfg.num_nodes = 4
    cfg.episodes = 3
    cfg.steps_per_episode = 5
    cfg.malicious_fraction = 0.25
    cfg.mine_every_n_steps = 2
    cfg.fhe_enabled = False
    return cfg


@pytest.fixture
def node_list() -> list:
    return [f"Node_{i}" for i in range(4)]


@pytest.fixture
def trust_manager(node_list):
    from trust import TrustManager
    return TrustManager(node_list)


@pytest.fixture
def blockchain():
    from blockchain import Blockchain
    bc = Blockchain(difficulty=1)  # low difficulty for speed
    return bc
