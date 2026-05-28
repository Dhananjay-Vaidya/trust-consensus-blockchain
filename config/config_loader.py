from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any
import yaml


@dataclass
class SimConfig:
    # network
    num_nodes: int = 16
    malicious_fraction: float = 0.30
    batch_size: int = 256

    # trust
    decay_rate: float = 0.95
    consensus_threshold: float = 0.6
    min_trust: float = 0.01
    max_trust: float = 1.0
    threshold: float = 0.45
    noise_level: float = 0.08
    initial_variance: float = 0.12
    valid_boost: float = 3.0
    invalid_penalty: float = 2.0
    malicious_penalty: float = 4.0
    malicious_alpha_decay: float = 0.92
    ground_truth_update_interval: int = 15

    # training
    episodes: int = 50
    steps_per_episode: int = 100
    training_batch_size: int = 64
    gamma: float = 0.99
    lr: float = 0.001
    action_space_size: int = 27

    # attacks
    cra_intensity: float = 0.85
    cra_attack_frequency: int = 2
    tdp_activation_episode: int = 25
    tdp_attack_intensity: float = 0.75

    # mining
    mine_every_n_steps: int = 5

    # fhe
    fhe_enabled: bool = False

    # rewards
    f1_reward_weight: float = 0.7
    step_reward_weight: float = 0.3
    fn_penalty_weight: float = 3.0

    # normalization
    chain_norm: float = 100.0
    consensus_norm: float = 20.0


def _flatten(d: Dict[str, Any], parent_key: str = "") -> Dict[str, Any]:
    """Flatten nested YAML dict into a single-level dict."""
    items: Dict[str, Any] = {}
    for k, v in d.items():
        if isinstance(v, dict):
            items.update(_flatten(v, k))
        else:
            items[k] = v
    return items


def load_config(path: str, overrides: Dict[str, Any] | None = None) -> SimConfig:
    """Load YAML config and apply CLI override dict on top."""
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    flat = _flatten(raw)
    if overrides:
        flat.update({k: v for k, v in overrides.items() if v is not None})

    cfg = SimConfig()
    for key, value in flat.items():
        if hasattr(cfg, key):
            setattr(cfg, key, value)
    return cfg
