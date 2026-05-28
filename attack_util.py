from __future__ import annotations

# attack_util.py - BALANCED Attack Interface

from typing import Any, Dict, Optional, Set

from nma_attack import simulate_nma_attack
from cra_attack import simulate_cra_attack
from aaa_attack import simulate_aaa_attack
from bfi_attack import ByzantineFaultInjection
from tdp_attack import TimeDelayedPoisoning
from utils.logger import get_logger

logger = get_logger(__name__)

_attack_instances: Dict[str, Any] = {}


def apply_attack(
    trust_manager: Any,
    malicious_nodes: Any,
    attack_type: str,
    **kwargs: Any,
) -> Optional[Dict[str, Any]]:
    global _attack_instances

    if attack_type == "none":
        return None

    elif attack_type == "nma":
        if "nma" not in _attack_instances:
            from nma_attack import NoiseManipulationAttack
            _attack_instances["nma"] = NoiseManipulationAttack(
                malicious_nodes=set(malicious_nodes),
                noise_level=0.5,
                attack_budget=0.9,
            )
        honest_nodes = set(trust_manager.trust_scores.keys()) - set(malicious_nodes)
        return _attack_instances["nma"].execute(trust_manager, honest_nodes)

    elif attack_type == "cra":
        if "cra" not in _attack_instances:
            from cra_attack import CollusiveRumorAttack
            _attack_instances["cra"] = CollusiveRumorAttack(
                malicious_nodes=set(malicious_nodes),
                intensity=0.85,
                stealth_mode=True,
            )
        honest_nodes = set(trust_manager.trust_scores.keys()) - set(malicious_nodes)
        return _attack_instances["cra"].execute(trust_manager, honest_nodes)

    elif attack_type == "bfi":
        num_nodes = len(trust_manager.trust_scores)
        malicious_ratio = len(malicious_nodes) / num_nodes

        if "bfi" not in _attack_instances:
            bfi_config: Dict[str, Any] = {
                "equivocation_rate": 0.9,
                "sybil_amplification": 4,
                "eclipse_target_count": min(4, max(2, num_nodes // 4)),
                "trust_manipulation_factor": 0.15,
                "adaptive_threshold": 0.45,
                "coordination_window": 6,
                "honest_penalty_factor": 0.08,
            }
            _attack_instances["bfi"] = ByzantineFaultInjection(
                num_nodes=num_nodes,
                malicious_ratio=malicious_ratio,
                attack_config=bfi_config,
            )

        bfi_attack = _attack_instances["bfi"]
        bfi_attack.execute_attack_on_trust(
            trust_manager=trust_manager,
            malicious_nodes=malicious_nodes,
            current_step=kwargs.get("current_step", 0),
            current_episode=kwargs.get("current_episode", 0),
        )
        return bfi_attack.get_attack_metrics()

    elif attack_type == "aaa":
        return simulate_aaa_attack(trust_manager, malicious_nodes, **kwargs)

    elif attack_type == "tdp":
        num_nodes = len(trust_manager.trust_scores)
        malicious_ratio = len(malicious_nodes) / num_nodes
        current_step = kwargs.get("current_step", 0)
        current_episode = kwargs.get("current_episode", 0)
        activation_episode = kwargs.get("activation_episode", 25)
        attack_intensity = kwargs.get("attack_intensity", 0.75)

        if "tdp" not in _attack_instances:
            _attack_instances["tdp"] = TimeDelayedPoisoning(
                num_nodes=num_nodes,
                malicious_ratio=malicious_ratio,
                activation_episode=activation_episode,
                attack_intensity=attack_intensity,
            )

        tdp_attack = _attack_instances["tdp"]
        tdp_attack.execute_attack_on_trust(
            trust_manager=trust_manager,
            malicious_nodes=malicious_nodes,
            current_step=current_step,
            current_episode=current_episode,
        )
        return {
            "activated": tdp_attack.is_activated(),
            "attack_count": tdp_attack.attack_count,
        }

    else:
        raise ValueError(
            f"Unknown attack type: '{attack_type}'. "
            f"Valid options: 'none', 'nma', 'cra', 'bfi', 'aaa', 'tdp'"
        )


def reset_attack_instances() -> None:
    global _attack_instances
    _attack_instances = {}

    try:
        from aaa_attack import reset_aaa_instance
        reset_aaa_instance()
    except Exception:
        pass

    try:
        from tdp_attack import reset_tdp_instance
        reset_tdp_instance()
    except Exception:
        pass

    try:
        from bfi_attack import reset_bfi_instance
        reset_bfi_instance()
    except Exception:
        pass


def get_attack_description(attack_type: str) -> str:
    descriptions: Dict[str, str] = {
        "none": "No attack - baseline scenario",
        "nma": "Noise Manipulation Attack (Target F1: 0.85-0.95)",
        "cra": "Collusion Reputation Attack (Target F1: 0.75-0.85)",
        "bfi": "Byzantine Fault Injection (Target F1: 0.70-0.80)",
        "aaa": "Adaptive Adversarial Attack (Target F1: 0.75-0.85)",
        "tdp": "Time-Delayed Poisoning (Target F1: 0.60-0.75 post-activation)",
    }
    return descriptions.get(attack_type, f"Unknown attack type: {attack_type}")


def get_available_attacks() -> list:
    return ["none", "nma", "cra", "bfi", "aaa", "tdp"]


def is_valid_attack(attack_type: str) -> bool:
    return attack_type in get_available_attacks()


def get_expected_f1_ranges() -> Dict[str, tuple]:
    return {
        "none": (0.95, 1.00),
        "nma": (0.85, 0.95),
        "cra": (0.75, 0.85),
        "bfi": (0.70, 0.80),
        "aaa": (0.75, 0.85),
        "tdp": (0.60, 0.75),
    }
