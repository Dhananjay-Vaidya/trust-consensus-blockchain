# cra_attack.py - Collusive Rumor Attack

import random
import numpy as np
from typing import Dict, Set, Tuple
from collections import deque


class CollusiveRumorAttack:
    """
    Sophisticated Collusive Rumor Attack (CRA) implementation.
    
    Attack Strategy:
    - Malicious nodes collude to boost each other's trust
    - Target high-trust honest nodes for suppression
    - Use stealth tactics to avoid detection patterns
    """
    
    def __init__(self, malicious_nodes: Set[str], 
                 intensity: float = 0.7,
                 stealth_mode: bool = True,
                 attack_frequency: int = 3):  # Attack every N rounds
        """
        Initialize sophisticated CRA with adaptive parameters.
        
        Args:
            malicious_nodes: Set of malicious node IDs
            intensity: Attack aggressiveness [0.0-1.0]
            stealth_mode: If True, use camouflage tactics
            attack_frequency: Execute attack every N rounds (default: 3)
        """
        self.malicious_nodes = malicious_nodes
        self.intensity = intensity
        self.stealth_mode = stealth_mode
        self.attack_frequency = attack_frequency
        
        # Attack state tracking
        self.attack_history = deque(maxlen=100)
        self.target_history = {}
        self.round_count = 0
        self.successful_attacks = 0
        
        # Attack parameters (tuned for effectiveness)
        self.base_boost = 0.15 * intensity
        self.base_penalty = 0.25 * intensity
        self.noise_std = 0.02 if stealth_mode else 0.0
        
        print(f"\n[CRA] Initialized Collusive Rumor Attack")
        print(f"[CRA] Malicious nodes: {len(malicious_nodes)}")
        print(f"[CRA] Intensity: {intensity}, Stealth: {stealth_mode}")
        print(f"[CRA] Attack frequency: every {attack_frequency} rounds\n")
        
    def execute(self, trust_manager, honest_nodes: Set[str]) -> Dict:
        """
        Execute one round of sophisticated CRA.
        
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
            'boosted_nodes': 0,
            'suppressed_nodes': 0,
            'avg_malicious_trust_gain': 0.0,
            'avg_honest_trust_loss': 0.0,
            'attack_intensity': 0.0
        }
        
        # FIXED: Attack every N rounds instead of only when round_count % 10 == 0
        if self.round_count % self.attack_frequency != 0:
            return metrics  # Silent round (evasion)
        
        metrics['attacked_this_round'] = True
        metrics['attack_intensity'] = self.intensity
        self.successful_attacks += 1
        
        # Phase 1: Strategic Trust Boosting (Collusive Reputation Inflation)
        boost_gains = self._execute_trust_boosting(trust_manager)
        metrics['boosted_nodes'] = len(boost_gains)
        metrics['avg_malicious_trust_gain'] = np.mean(boost_gains) if boost_gains else 0.0
        
        # Phase 2: Targeted Honest Node Suppression
        suppression_losses = self._execute_suppression(trust_manager, honest_nodes)
        metrics['suppressed_nodes'] = len(suppression_losses)
        metrics['avg_honest_trust_loss'] = np.mean(suppression_losses) if suppression_losses else 0.0
        
        # Phase 3: Camouflage (if stealth mode)
        if self.stealth_mode:
            self._apply_noise_camouflage(trust_manager, honest_nodes)
        
        self.attack_history.append(metrics)
        
        # Debug logging
        if self.round_count % 30 == 0:
            print(f"[CRA] Round {self.round_count}: {self.successful_attacks} attacks executed, "
                  f"avg boost: {metrics['avg_malicious_trust_gain']:.4f}, "
                  f"avg suppress: {metrics['avg_honest_trust_loss']:.4f}")
        
        return metrics
    
    def _execute_trust_boosting(self, trust_manager) -> list:
        """
        Phase 1: Malicious nodes boost each other's trust.
        """
        boost_gains = []
        
        for attacker in self.malicious_nodes:
            old_trust = trust_manager.get_trust(attacker)
            
            # Adaptive boost: higher for low-trust malicious nodes
            current_boost = self._calculate_adaptive_boost(old_trust)
            
            # Apply boost through reputation manipulation
            # Simulates malicious nodes giving positive feedback to each other
            trust_manager.update_trust(attacker, "valid")
            
            # Stealth: occasionally inject "invalid" to appear legitimate
            if self.stealth_mode and random.random() < 0.2:
                trust_manager.update_trust(attacker, "invalid")
            
            new_trust = trust_manager.get_trust(attacker)
            boost_gains.append(new_trust - old_trust)
        
        return boost_gains
    
    def _execute_suppression(self, trust_manager, honest_nodes: Set[str]) -> list:
        """
        Phase 2: Target and suppress high-trust honest nodes.
        """
        suppression_losses = []
        
        # Select high-value targets
        targets = self._select_high_value_targets(trust_manager, honest_nodes)
        
        for target in targets:
            old_trust = trust_manager.get_trust(target)
            
            # Strategic suppression: multiple malicious signals
            penalty_strength = self._calculate_penalty_strength(old_trust)
            num_attacks = max(1, int(penalty_strength * len(self.malicious_nodes) / 2))
            
            for _ in range(num_attacks):
                trust_manager.update_trust(target, "malicious")  # False accusation
            
            new_trust = trust_manager.get_trust(target)
            suppression_losses.append(old_trust - new_trust)
            
            # Track targeting for adaptive behavior
            self.target_history[target] = self.target_history.get(target, 0) + 1
        
        return suppression_losses
    
    def _calculate_adaptive_boost(self, current_trust: float) -> float:
        """
        Calculate boost amount based on current trust.
        Higher boost for low-trust nodes to recover quickly.
        """
        if current_trust < 0.3:
            return self.base_boost * 1.5  # Aggressive recovery
        elif current_trust < 0.5:
            return self.base_boost
        else:
            return self.base_boost * 0.5  # Maintain high trust
    
    def _calculate_penalty_strength(self, target_trust: float) -> float:
        """
        Calculate attack strength based on target's trust.
        Focus on high-trust honest nodes (high-value targets).
        """
        if target_trust > 0.7:
            return self.intensity * 3.0  # Priority target
        elif target_trust > 0.5:
            return self.intensity * 2.0
        else:
            return self.intensity  # Low-value target
    
    def _select_high_value_targets(self, trust_manager, honest_nodes: Set[str]) -> list:
        """
        Select honest nodes to attack based on strategic value.
        Prioritize: high trust, less frequently attacked.
        """
        if not honest_nodes:
            return []
        
        # Get trust scores for all honest nodes
        honest_trust = [(node, trust_manager.get_trust(node)) for node in honest_nodes]
        
        # Sort by trust (descending) - attack highest trust nodes first
        honest_trust.sort(key=lambda x: x[1], reverse=True)
        
        # Target top 30% of honest nodes
        target_count = max(1, int(len(honest_nodes) * 0.3))
        
        if self.stealth_mode:
            # Mix high-trust and random targets to avoid patterns
            high_value_count = max(1, target_count // 2)
            random_count = target_count - high_value_count
            
            high_value = [node for node, _ in honest_trust[:high_value_count]]
            
            # Avoid nodes that have been attacked too often
            remaining = [node for node, _ in honest_trust[high_value_count:]]
            if remaining and random_count > 0:
                random_targets = random.sample(remaining, min(random_count, len(remaining)))
            else:
                random_targets = []
            
            return high_value + random_targets
        else:
            return [node for node, _ in honest_trust[:target_count]]
    
    def _apply_noise_camouflage(self, trust_manager, honest_nodes: Set[str]):
        """
        Add noise to avoid detection patterns.
        Occasionally boost some honest nodes to appear benign.
        """
        if not honest_nodes:
            return
        
        if random.random() < 0.15:  # 15% chance
            random_honest = random.choice(list(honest_nodes))
            trust_manager.update_trust(random_honest, "valid")
    
    def get_attack_success_rate(self, trust_manager, threshold: float = 0.5) -> float:
        """
        Calculate attack success: fraction of malicious nodes with trust > threshold.
        """
        successful_malicious = sum(
            1 for node in self.malicious_nodes 
            if trust_manager.get_trust(node) > threshold
        )
        return successful_malicious / len(self.malicious_nodes) if self.malicious_nodes else 0.0
    
    def get_attack_metrics(self) -> Dict:
        """Return comprehensive attack statistics."""
        return {
            'total_rounds': self.round_count,
            'successful_attacks': self.successful_attacks,
            'attack_rate': self.successful_attacks / max(1, self.round_count),
            'most_targeted_nodes': sorted(
                self.target_history.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            'recent_history': list(self.attack_history)[-10:]
        }


# Backward compatibility function - FIXED to use persistent instance
_cra_instance = None

def simulate_cra_attack(trust_manager, malicious_nodes, boost_amount=0.15, penalty_amount=0.25):
    """
    Legacy interface for CRA attack.
    
    FIXED: Now uses a persistent instance to maintain round_count state.
    """
    global _cra_instance
    
    # Create instance only once
    if _cra_instance is None:
        _cra_instance = CollusiveRumorAttack(
            malicious_nodes=set(malicious_nodes),
            intensity=0.7,
            stealth_mode=True,
            attack_frequency=10  # Attack every 3 rounds for more frequent attacks
        )
    
    honest_nodes = set(trust_manager.trust_scores.keys()) - set(malicious_nodes)
    return _cra_instance.execute(trust_manager, honest_nodes)


def reset_cra_instance():
    """Reset the CRA instance. Call between simulations."""
    global _cra_instance
    _cra_instance = None
