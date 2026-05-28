# nma_attack.py - Naive Malicious Attack (Noise Manipulation Attack)

import random
import numpy as np
from typing import Dict, Set
from collections import defaultdict


class NoiseManipulationAttack:
    """
    Sophisticated Naive Malicious Attack (NMA) implementation.
    
    Unlike CRA, NMA is uncoordinated - each malicious node acts independently
    without explicit collusion. This represents less sophisticated attackers.
    
    Attack Strategy:
    - Random noise injection to disrupt trust evaluation
    - False flag operations against honest nodes
    - Self-destruct camouflage (malicious nodes occasionally harm themselves)
    """
    
    def __init__(self, malicious_nodes: Set[str],
                 noise_level: float = 0.4,
                 attack_budget: float = 0.8):
        """
        Initialize sophisticated NMA.
        
        Args:
            malicious_nodes: Set of malicious node IDs
            noise_level: Noise injection intensity [0.0-1.0]
            attack_budget: Fraction of rounds to attack [0.0-1.0]
        """
        self.malicious_nodes = malicious_nodes
        self.noise_level = noise_level
        self.attack_budget = attack_budget
        
        # Attack state
        self.round_count = 0
        self.attack_count = 0
        self.target_frequency = defaultdict(int)
        
        print(f"\n[NMA] Initialized Noise Manipulation Attack")
        print(f"[NMA] Malicious nodes: {len(malicious_nodes)}")
        print(f"[NMA] Noise level: {noise_level}, Budget: {attack_budget}\n")
        
    def execute(self, trust_manager, honest_nodes: Set[str]) -> Dict:
        """
        Execute one round of NMA with strategic behavior.
        
        Args:
            trust_manager: TrustManager instance to manipulate
            honest_nodes: Set of honest node IDs
            
        Returns:
            dict: Attack metrics for this round
        """
        self.round_count += 1
        
        metrics = {
            'round': self.round_count,
            'attacked_this_round': False,
            'malicious_nodes_affected': 0,
            'honest_nodes_affected': 0,
            'noise_magnitude': 0.0
        }
        
        # Strategic decision: attack or stay silent?
        # Add sinusoidal variation to make attack pattern less predictable
        attack_probability = self.attack_budget * (1.0 + 0.3 * np.sin(self.round_count / 10))
        
        if random.random() > attack_probability:
            return metrics  # Silent round (evasion)
        
        self.attack_count += 1
        metrics['attacked_this_round'] = True
        metrics['noise_magnitude'] = self.noise_level
        
        # Phase 1: Self-destruct camouflage
        # Malicious nodes inject noise to their OWN trust to appear "natural"
        for node in self.malicious_nodes:
            old_trust = trust_manager.get_trust(node)
            
            # Inject asymmetric noise
            noise = self._generate_strategic_noise(old_trust, is_malicious=True)
            
            # Apply noise through fake behavior signals
            if noise < 0:
                trust_manager.update_trust(node, "invalid")
            else:
                # Occasionally boost own trust
                if random.random() < 0.3:
                    trust_manager.update_trust(node, "valid")
            
            metrics['malicious_nodes_affected'] += 1
        
        # Phase 2: False flag operations
        # Frame high-trust honest nodes as unreliable
        targets = self._select_false_flag_targets(trust_manager, honest_nodes)
        
        for target in targets:
            old_trust = trust_manager.get_trust(target)
            
            # Inject strong negative signals
            attack_strength = self._calculate_attack_strength(old_trust)
            
            num_attacks = max(1, int(attack_strength * 2))
            for _ in range(num_attacks):
                trust_manager.update_trust(target, "malicious")  # False accusation
            
            self.target_frequency[target] += 1
            metrics['honest_nodes_affected'] += 1
        
        # Phase 3: Entropy injection (optional)
        # Add random noise to low-trust nodes to obscure patterns
        if random.random() < 0.3:
            self._inject_entropy(trust_manager, honest_nodes)
        
        # Debug logging
        if self.round_count % 30 == 0:
            print(f"[NMA] Round {self.round_count}: {self.attack_count} attacks, "
                  f"targeting {len(targets)} honest nodes")
        
        return metrics
    
    def _generate_strategic_noise(self, current_trust: float, is_malicious: bool) -> float:
        """Generate context-aware noise."""
        base_noise = np.random.normal(0, self.noise_level * 0.1)
        
        if is_malicious:
            # Malicious nodes: slight downward bias to appear humble
            return base_noise - 0.02
        else:
            # Honest nodes: stronger negative bias (attack)
            if current_trust > 0.6:
                return base_noise - self.noise_level * 0.3  # Attack high-trust
            else:
                return base_noise  # Leave low-trust alone
    
    def _select_false_flag_targets(self, trust_manager, honest_nodes: Set[str]) -> list:
        """Select honest nodes for false flag attacks."""
        if not honest_nodes:
            return []
        
        # Target nodes that haven't been attacked recently (avoid patterns)
        honest_trust = [
            (node, trust_manager.get_trust(node), self.target_frequency[node])
            for node in honest_nodes
        ]
        
        # Sort by: high trust, low attack frequency
        honest_trust.sort(key=lambda x: (x[1], -x[2]), reverse=True)
        
        # Target top 20%
        target_count = max(1, int(len(honest_nodes) * 0.2))
        return [node for node, _, _ in honest_trust[:target_count]]
    
    def _calculate_attack_strength(self, target_trust: float) -> float:
        """Calculate attack intensity based on target trust."""
        if target_trust > 0.7:
            return self.noise_level * 4.0  # Strong attack on high-trust
        elif target_trust > 0.5:
            return self.noise_level * 2.0
        else:
            return self.noise_level * 0.5  # Weak attack on low-trust
    
    def _inject_entropy(self, trust_manager, honest_nodes: Set[str]):
        """Add random noise to obscure attack patterns."""
        if not honest_nodes:
            return
        
        sample_size = min(3, len(honest_nodes))
        random_nodes = random.sample(list(honest_nodes), sample_size)
        
        for node in random_nodes:
            if random.random() < 0.5:
                trust_manager.update_trust(node, "invalid")
    
    def get_attack_metrics(self) -> Dict:
        """Return cumulative attack statistics."""
        return {
            'total_rounds': self.round_count,
            'attack_rounds': self.attack_count,
            'attack_rate': self.attack_count / max(1, self.round_count),
            'most_targeted_nodes': sorted(
                self.target_frequency.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }


# Persistent instance for state tracking
_nma_instance = None


def simulate_nma_attack(trust_manager, malicious_nodes, 
                        malicious_range=(0.1, 0.3),
                        honest_penalty=0.2,
                        honest_penalty_fraction=0.2):
    """
    Legacy NMA interface with persistent state.
    
    Parameters are kept for backward compatibility but the new
    NoiseManipulationAttack class uses different parameters internally.
    """
    global _nma_instance
    
    # Create instance only once to maintain state
    if _nma_instance is None:
        _nma_instance = NoiseManipulationAttack(
            malicious_nodes=set(malicious_nodes),
            noise_level=0.4,
            attack_budget=0.8
        )
    
    honest_nodes = set(trust_manager.trust_scores.keys()) - set(malicious_nodes)
    return _nma_instance.execute(trust_manager, honest_nodes)


def reset_nma_instance():
    """Reset the NMA instance. Call between simulations."""
    global _nma_instance
    _nma_instance = None
