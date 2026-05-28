from __future__ import annotations

# trust.py - BALANCED Trust Manager with Realistic Detection Difficulty
"""
Trust Manager tuned for realistic detection scenarios.
"""

import random
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
from scipy.stats import beta as beta_dist

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class TrustManager:
    """
    Bayesian Trust Manager using Beta distribution for trust estimation.
    """

    def __init__(self, nodes: List[str], config: Optional[Dict[str, Any]] = None) -> None:
        self.config: Dict[str, Any] = config or {
            "initial_alpha": 8.0,
            "initial_beta": 8.0,
            "valid_boost": 3.0,
            "invalid_penalty": 2.0,
            "malicious_penalty": 4.0,
            "malicious_alpha_decay": 0.92,
            "decay_rate": 0.005,
            "min_trust": 0.01,
            "max_trust": 0.99,
            "min_alpha": 1.0,
            "min_beta": 1.0,
            "noise_level": 0.08,
            "attack_resistance": 0.7,
        }

        self.alpha: Dict[str, float] = {}
        self.beta_param: Dict[str, float] = {}
        self.trust_scores: Dict[str, float] = {}
        self.update_counts: Dict[str, int] = {node: 0 for node in nodes}
        self.uncertainty: Dict[str, float] = {}

        base_alpha = self.config["initial_alpha"]
        base_beta = self.config["initial_beta"]

        for node in nodes:
            noise = random.uniform(-4, 4)
            self.alpha[node] = base_alpha + noise
            self.beta_param[node] = base_beta - noise

            extra_variance = random.uniform(-2, 2)
            self.alpha[node] += extra_variance
            self.beta_param[node] += abs(extra_variance) * 0.5

            total = self.alpha[node] + self.beta_param[node]
            self.trust_scores[node] = self.alpha[node] / total
            self.uncertainty[node] = self._calculate_uncertainty(node)

        from src.utils.logger import get_logger
        _log = get_logger(__name__)
        _log.info(f"Initialized {len(nodes)} nodes with HIGH-VARIANCE Bayesian trust")

    def _calculate_uncertainty(self, node_id: str) -> float:
        a = self.alpha.get(node_id, self.config["initial_alpha"])
        b = self.beta_param.get(node_id, self.config["initial_beta"])
        variance = (a * b) / ((a + b) ** 2 * (a + b + 1))
        return variance

    def _recalculate_trust(self, node_id: str) -> None:
        a = max(self.config["min_alpha"], self.alpha[node_id])
        b = max(self.config["min_beta"], self.beta_param[node_id])
        self.alpha[node_id] = a
        self.beta_param[node_id] = b
        total = a + b
        self.trust_scores[node_id] = float(np.clip(a / total, self.config["min_trust"], self.config["max_trust"]))
        self.uncertainty[node_id] = self._calculate_uncertainty(node_id)

    def update_trust(self, node_id: str, outcome: str) -> None:
        if node_id not in self.alpha:
            return
        self.update_counts[node_id] += 1
        noise = random.gauss(0, self.config["noise_level"])

        if outcome == "valid":
            boost = max(0.5, self.config["valid_boost"] + noise)
            self.alpha[node_id] += boost
        elif outcome == "invalid":
            penalty = max(0.5, self.config["invalid_penalty"] + noise)
            self.beta_param[node_id] += penalty
        elif outcome == "malicious":
            penalty = max(1.0, self.config["malicious_penalty"] + noise)
            self.beta_param[node_id] += penalty
            decay = float(np.clip(self.config["malicious_alpha_decay"] + random.gauss(0, 0.02), 0.85, 0.98))
            self.alpha[node_id] *= decay

        self._recalculate_trust(node_id)

    def adjust_trust(self, node_id: str, amount: float) -> None:
        if node_id not in self.trust_scores:
            return
        scale_factor = 15.0
        noise = random.gauss(0, 0.5)
        if amount > 0:
            adjustment = (amount * scale_factor) + noise
            self.alpha[node_id] += max(0.0, adjustment)
        else:
            adjustment = (abs(amount) * scale_factor) + noise
            self.beta_param[node_id] += max(0.0, adjustment)
        self._recalculate_trust(node_id)

    def decay_trust(self, decay_rate: Optional[float] = None) -> None:
        if decay_rate is None:
            decay_rate = self.config["decay_rate"]
        if decay_rate <= 0:
            return
        for node_id in self.alpha:
            self.alpha[node_id] *= 1.0 - decay_rate
            self.beta_param[node_id] *= 1.0 - decay_rate
            noise = random.gauss(0, 0.1)
            self.alpha[node_id] += noise
            self.beta_param[node_id] -= noise * 0.5
            self.alpha[node_id] = max(self.config["min_alpha"], self.alpha[node_id])
            self.beta_param[node_id] = max(self.config["min_beta"], self.beta_param[node_id])
            self._recalculate_trust(node_id)

    def get_trust(self, node_id: str) -> float:
        return self.trust_scores.get(node_id, 0.5)

    def get_trust_with_uncertainty(self, node_id: str) -> Dict[str, float]:
        a = max(self.config["min_alpha"], self.alpha.get(node_id, self.config["initial_alpha"]))
        b = max(self.config["min_beta"], self.beta_param.get(node_id, self.config["initial_beta"]))
        try:
            lower = float(beta_dist.ppf(0.025, a, b))
            upper = float(beta_dist.ppf(0.975, a, b))
        except Exception:
            lower, upper = 0.0, 1.0
        return {
            "trust": self.trust_scores.get(node_id, 0.5),
            "lower_bound": lower,
            "upper_bound": upper,
            "uncertainty": self.uncertainty.get(node_id, 0.1),
        }

    def select_delegated_nodes(self, num_delegates: int) -> List[str]:
        samples: Dict[str, float] = {}
        for node_id in self.trust_scores:
            a = max(self.config["min_alpha"], self.alpha[node_id])
            b = max(self.config["min_beta"], self.beta_param[node_id])
            samples[node_id] = float(np.random.beta(a, b))
        import heapq
        top_nodes = heapq.nlargest(num_delegates, samples.items(), key=lambda item: item[1])
        return [node_id for node_id, _ in top_nodes]

    def select_delegates_ucb(self, num_delegates: int, exploration_weight: float = 1.0) -> List[str]:
        ucb_scores: Dict[str, float] = {}
        for node_id in self.trust_scores:
            trust = self.trust_scores[node_id]
            uncertainty = self.uncertainty.get(node_id, 0.1)
            ucb_scores[node_id] = trust + exploration_weight * float(np.sqrt(uncertainty))
        import heapq
        top_nodes = heapq.nlargest(num_delegates, ucb_scores.items(), key=lambda item: item[1])
        return [node_id for node_id, _ in top_nodes]

    def calculate_trust_snapshot(self, nodes: List[str]) -> Dict[str, float]:
        return {node: self.get_trust(node) for node in nodes}

    def get_reputation_metrics(self, node_id: str) -> Dict[str, Any]:
        a = self.alpha.get(node_id, self.config["initial_alpha"])
        b = self.beta_param.get(node_id, self.config["initial_beta"])
        return {
            "trust_score": self.trust_scores.get(node_id, 0.5),
            "alpha": a,
            "beta": b,
            "variance": self._calculate_uncertainty(node_id),
            "total_evidence": a + b,
            "update_count": self.update_counts.get(node_id, 0),
        }

    def get_statistics(self) -> Dict[str, Any]:
        trusts = list(self.trust_scores.values())
        return {
            "mean_trust": float(np.mean(trusts)),
            "std_trust": float(np.std(trusts)),
            "min_trust": float(np.min(trusts)),
            "max_trust": float(np.max(trusts)),
            "median_trust": float(np.median(trusts)),
            "total_updates": sum(self.update_counts.values()),
            "num_nodes": len(trusts),
        }

    def get_trust_distribution(self) -> Dict[str, List]:
        return {
            "scores": list(self.trust_scores.values()),
            "alphas": list(self.alpha.values()),
            "betas": list(self.beta_param.values()),
            "node_ids": list(self.trust_scores.keys()),
        }

    def get_encrypted_trust_snapshot(self, fhe: Any) -> Any:
        """Encrypt the current trust score vector using FHE."""
        scores = list(self.trust_scores.values())
        return fhe.encrypt_vector(scores)

    def get_decrypted_trust_snapshot(self, fhe: Any, encrypted: Any) -> List[float]:
        """Decrypt an encrypted trust score vector."""
        return fhe.decrypt_vector(encrypted)

    def reset(self) -> None:
        for node_id in self.trust_scores:
            noise = random.uniform(-4, 4)
            self.alpha[node_id] = self.config["initial_alpha"] + noise
            self.beta_param[node_id] = self.config["initial_beta"] - noise
            total = self.alpha[node_id] + self.beta_param[node_id]
            self.trust_scores[node_id] = self.alpha[node_id] / total
            self.update_counts[node_id] = 0
            self.uncertainty[node_id] = self._calculate_uncertainty(node_id)
