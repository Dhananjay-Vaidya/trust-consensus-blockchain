"""Trust backends.

``TrustManager`` is the legacy Beta-reputation model of the base protocol, kept unchanged in its
update rules for the ablation (``trust_backend="legacy_beta"``) but made reproducible: every source
of randomness is an injected ``random.Random``.  ``make_trust_backend`` returns either it or
``SleeperGuard`` behind one interface.  No backend reads ground truth: the only input is audit
evidence (``observe(node, inconsistent)``).
"""
from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

import numpy as np
from scipy.stats import beta as beta_dist


class TrustManager:
    """
    Bayesian Trust Manager using Beta distribution for trust estimation.
    """

    def __init__(self, nodes: List[str], config: Optional[Dict[str, Any]] = None,
                 rng: Optional[random.Random] = None) -> None:
        self._rng = rng if rng is not None else random.Random(0)
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
            noise = self._rng.uniform(-4, 4)
            self.alpha[node] = base_alpha + noise
            self.beta_param[node] = base_beta - noise

            extra_variance = self._rng.uniform(-2, 2)
            self.alpha[node] += extra_variance
            self.beta_param[node] += abs(extra_variance) * 0.5

            total = self.alpha[node] + self.beta_param[node]
            self.trust_scores[node] = self.alpha[node] / total
            self.uncertainty[node] = self._calculate_uncertainty(node)


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
        noise = self._rng.gauss(0, self.config["noise_level"])

        if outcome == "valid":
            boost = max(0.5, self.config["valid_boost"] + noise)
            self.alpha[node_id] += boost
        elif outcome == "invalid":
            penalty = max(0.5, self.config["invalid_penalty"] + noise)
            self.beta_param[node_id] += penalty
        elif outcome == "malicious":
            penalty = max(1.0, self.config["malicious_penalty"] + noise)
            self.beta_param[node_id] += penalty
            decay = float(np.clip(self.config["malicious_alpha_decay"] + self._rng.gauss(0, 0.02), 0.85, 0.98))
            self.alpha[node_id] *= decay

        self._recalculate_trust(node_id)

    def adjust_trust(self, node_id: str, amount: float) -> None:
        if node_id not in self.trust_scores:
            return
        scale_factor = 15.0
        noise = self._rng.gauss(0, 0.5)
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
            noise = self._rng.gauss(0, 0.1)
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
            samples[node_id] = float(self._rng.betavariate(a, b))
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

    def reset(self) -> None:
        for node_id in self.trust_scores:
            noise = self._rng.uniform(-4, 4)
            self.alpha[node_id] = self.config["initial_alpha"] + noise
            self.beta_param[node_id] = self.config["initial_beta"] - noise
            total = self.alpha[node_id] + self.beta_param[node_id]
            self.trust_scores[node_id] = self.alpha[node_id] / total
            self.update_counts[node_id] = 0
            self.uncertainty[node_id] = self._calculate_uncertainty(node_id)


# ---------------------------------------------------------------------------------------------
#  Unified backend interface
# ---------------------------------------------------------------------------------------------
class TrustBackend:
    """Interface used by the environment. Implementations see audit evidence only."""

    name = "abstract"

    def observe(self, node: str, inconsistent: bool) -> bool:  # returns True on a change alarm
        raise NotImplementedError

    def trust(self, node: str) -> float:
        raise NotImplementedError

    def is_quarantined(self, node: str) -> bool:
        return False

    def weights(self, committee: List[str]) -> np.ndarray:
        raise NotImplementedError

    def end_step(self, step: int) -> None:
        return None


class LegacyBetaBackend(TrustBackend):
    """Legacy Beta trust fed by audit evidence instead of ground truth.

    Mapping: consistent audited vote -> ``update_trust(node, "valid")``;
    inconsistent -> ``update_trust(node, "invalid")``.  The legacy periodic decay
    (rate 0.003 every 5 steps) is kept.  Weights are the raw trust scores (no cap).
    """

    name = "legacy_beta"

    def __init__(self, nodes: List[str], rng: random.Random) -> None:
        self.tm = TrustManager(nodes, rng=rng)

    def observe(self, node: str, inconsistent: bool) -> bool:
        self.tm.update_trust(node, "invalid" if inconsistent else "valid")
        return False

    def trust(self, node: str) -> float:
        return self.tm.get_trust(node)

    def weights(self, committee: List[str]) -> np.ndarray:
        return np.array([self.tm.get_trust(n) for n in committee], dtype=float)

    def end_step(self, step: int) -> None:
        if step % 5 == 0:
            self.tm.decay_trust(decay_rate=0.003)


class SleeperGuardBackend(TrustBackend):
    """SleeperGuard with a selectable share-cap implementation.

    cap_method="exact"              : SleeperGuard computes uncapped weights, then
                                      ``capping.cap_shares_exact`` applies the cap (default).
    cap_method="verified_iterative" : SleeperGuard's own ``cap_shares`` (as provided; may overshoot).
    """

    name = "sleeper_guard"

    def __init__(self, nodes: List[str], cfg: Any, cap_method: str = "exact") -> None:
        import dataclasses

        from src.trust.sleeper_guard import SleeperGuard, SleeperGuardConfig

        cfg = cfg or SleeperGuardConfig()
        if cap_method not in ("exact", "verified_iterative"):
            raise ValueError(f"unknown cap_method {cap_method!r}")
        self.cap_method = cap_method
        self.cap_on = cfg.use_share_cap
        self.cap_factor = cfg.cap_factor
        inner = dataclasses.replace(cfg, use_share_cap=False) if cap_method == "exact" else cfg
        self.sg = SleeperGuard(nodes, inner)

    def observe(self, node: str, inconsistent: bool) -> bool:
        return self.sg.observe(node, inconsistent)

    def trust(self, node: str) -> float:
        return self.sg.trust(node)

    def is_quarantined(self, node: str) -> bool:
        return self.sg.is_quarantined(node)

    def weights(self, committee: List[str]) -> np.ndarray:
        w = self.sg.weights(committee)
        if self.cap_method == "exact" and self.cap_on and committee:
            from src.trust.capping import cap_shares_exact
            w = cap_shares_exact(w, self.cap_factor / len(committee))
        return w


class NoTrustBackend(TrustBackend):
    """Uniform weights; used by PBFT / DPoS / majority / random baselines."""

    name = "none"

    def __init__(self, nodes: List[str]) -> None:
        self.nodes = list(nodes)

    def observe(self, node: str, inconsistent: bool) -> bool:
        return False

    def trust(self, node: str) -> float:
        return 1.0

    def weights(self, committee: List[str]) -> np.ndarray:
        return np.ones(len(committee), dtype=float)


def make_trust_backend(name: str, nodes: List[str], sg_cfg: Any, rng: random.Random,
                       cap_method: str = "exact") -> TrustBackend:
    if name == "sleeper_guard":
        return SleeperGuardBackend(nodes, sg_cfg, cap_method)
    if name == "legacy_beta":
        return LegacyBetaBackend(nodes, rng)
    if name == "none":
        return NoTrustBackend(nodes)
    raise ValueError(f"unknown trust_backend {name!r}")
