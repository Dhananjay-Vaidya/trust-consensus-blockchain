from __future__ import annotations

from typing import Dict, Set

import numpy as np
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class RewardSystem:
    def __init__(self) -> None:
        pass

    def calculate_rewards(
        self,
        trust_values: Dict[str, float],
        true_malicious_nodes: Set[str] | None = None,
        true_honest_nodes: Set[str] | None = None,
    ) -> Dict[str, float]:
        trust_tensor = torch.tensor(list(trust_values.values()), dtype=torch.float32, device=device)
        baseline_rewards = (trust_tensor - 0.3) * 30
        rewards: Dict[str, float] = {
            node: reward.item()
            for node, reward in zip(trust_values.keys(), baseline_rewards)
        }

        if true_malicious_nodes and true_honest_nodes:
            honest_trusts = [trust_values[n] for n in true_honest_nodes]
            malicious_trusts = [trust_values[n] for n in true_malicious_nodes]
            separation = float(np.mean(honest_trusts)) - float(np.mean(malicious_trusts))
            separation_bonus = separation * 100

            for node in trust_values:
                node_trust = trust_values[node]
                if node in true_malicious_nodes:
                    rewards[node] += (1.0 - node_trust) * 50
                else:
                    rewards[node] += node_trust * 40
                rewards[node] += separation_bonus / len(trust_values)

        trust_variance = float(torch.var(trust_tensor).item())
        variance_bonus = trust_variance * 50
        for node in rewards:
            rewards[node] += variance_bonus / len(rewards)

        return rewards

    def calculate_shaped_rewards(
        self,
        trust_values: Dict[str, float],
        previous_trust: Dict[str, float],
        true_malicious_nodes: Set[str],
        true_honest_nodes: Set[str],
        gamma: float = 0.99,
    ) -> Dict[str, float]:
        def potential(trust_dict: Dict[str, float]) -> float:
            honest_avg = float(np.mean([trust_dict.get(n, 0.5) for n in true_honest_nodes]))
            malicious_avg = float(np.mean([trust_dict.get(n, 0.5) for n in true_malicious_nodes]))
            return (honest_avg - malicious_avg) * 100

        current_potential = potential(trust_values)
        previous_potential = potential(previous_trust)
        shaping_bonus = gamma * current_potential - previous_potential

        base_rewards = self.calculate_rewards(trust_values, true_malicious_nodes, true_honest_nodes)
        shaped_rewards: Dict[str, float] = {
            node: base_rewards[node] + (shaping_bonus / len(trust_values))
            for node in trust_values
        }
        return shaped_rewards
