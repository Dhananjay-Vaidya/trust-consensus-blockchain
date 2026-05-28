from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import random
import numpy as np
import torch
import pytest

import parameters as params
from attack_util import reset_attack_instances


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def test_smoke_simulation_completes():
    """Run a minimal simulation and assert key invariants."""
    set_seed(42)
    reset_attack_instances()

    # Override params for a tiny run
    params.TOTAL_NODES = 4
    params.EPISODES = 3
    params.STEPS_PER_EPISODE = 5
    params.MALICIOUS_RATIO = 0.25
    params.MINE_EVERY_N_STEPS = 2
    params.FHE_ENABLED = False
    params.FHE_OVERHEAD_LOG = []
    params.ACTION_SPACE_SIZE = 27
    params.ACTION_MAP = {}

    from simulation_manager import SimulationManager

    sim = SimulationManager(
        episodes=3,
        agent_type="drl",
        attack_mode="nma",
        seed=42,
    )

    f1_scores = []
    for ep in range(3):
        result = sim.run_episode(ep)
        f1_scores.append(result["f1_score"])

    # F1 must be a float in [0, 1]
    for f1 in f1_scores:
        assert isinstance(f1, float)
        assert 0.0 <= f1 <= 1.0

    # After mining at least once, chain should have > 1 block
    assert len(sim.blockchain.chain) >= 1
