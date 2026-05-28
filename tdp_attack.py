# tdp_attack.py - STRENGTHENED Time-Delayed Poisoning Attack
"""
Time-Delayed Poisoning (TDP) Attack - STRENGTHENED Version

BALANCED VERSION:
- Earlier activation (episode 25 vs 30)
- Stronger attack intensity post-activation
- More aggressive trust manipulation
- Target F1: ~0.80-0.90 before activation, ~0.60-0.75 after

"Sleeper agent" attack that:
1. Behaves honestly for T episodes (builds high trust)
2. Suddenly attacks after activation (exploits built trust)
"""

import random
import numpy as np

# Global instance for state persistence
_tdp_instance = None


def reset_tdp_instance():
    """Reset TDP instance for clean simulation restarts."""
    global _tdp_instance
    _tdp_instance = None


class TimeDelayedPoisoning:
    def __init__(self, num_nodes, malicious_ratio, activation_episode=25, attack_intensity=0.75):
        """
        Initialize Time-Delayed Poisoning attack.
        
        STRENGTHENED PARAMETERS:
        - activation_episode: 25 (REDUCED from 30)
        - attack_intensity: 0.75 (INCREASED from 0.5)
        """
        self.num_nodes = num_nodes
        self.malicious_ratio = malicious_ratio
        self.activation_episode = activation_episode
        self.attack_intensity = attack_intensity
        self.malicious_indices = set()
        self.honest_indices = set()
        self.activated = False
        self.attack_count = 0
        self.dormant_boost_count = 0
        
        # STRENGTHENED attack parameters
        self.dormant_boost_probability = 0.45  # INCREASED from 0.3
        self.target_ratio = 0.35              # INCREASED from 0.2
        self.coordinated_attack_steps = 3     # MORE FREQUENT (was 5)
        self.honest_penalty_factor = 0.10     # NEW: Penalty to honest nodes
        self.self_boost_factor = 0.12         # NEW: Boost to malicious nodes
        
        # Assign malicious and honest node indices
        num_malicious = int(num_nodes * malicious_ratio)
        all_indices = list(range(num_nodes))
        self.malicious_indices = set(random.sample(all_indices, num_malicious))
        self.honest_indices = set(all_indices) - self.malicious_indices
        
        print(f"\n[TDP] Initialized: {len(self.malicious_indices)} sleepers / {num_nodes} nodes "
              f"({malicious_ratio*100:.0f}%) | "
              f"activation={activation_episode} | intensity={attack_intensity:.2f}")
        
    def execute_attack_on_trust(self, trust_manager, malicious_nodes, current_step, current_episode):
        """Execute TDP attack directly on trust_manager."""
        if current_episode < self.activation_episode:
            self._execute_dormant_phase(trust_manager, malicious_nodes, current_step, current_episode)
        else:
            self._execute_attack_phase(trust_manager, malicious_nodes, current_step, current_episode)
    
    def _execute_dormant_phase(self, trust_manager, malicious_nodes, current_step, current_episode):
        """
        Dormant phase: AGGRESSIVELY build trust for sleeper agents.
        
        STRENGTHENED:
        - Higher probability of trust boost
        - Occasional minor penalties to honest nodes (subtle)
        """
        for node in malicious_nodes:
            # HIGHER probability of boost
            if random.random() < self.dormant_boost_probability:
                trust_manager.update_trust(node, "valid")
                self.dormant_boost_count += 1
            
            # Additional direct trust boost
            if random.random() < 0.2:
                trust_manager.adjust_trust(node, 0.02)
        
        # NEW: Subtle honest node suppression during dormant phase
        if current_step % 10 == 0:
            honest_nodes = set(trust_manager.trust_scores.keys()) - set(malicious_nodes)
            if honest_nodes:
                # Randomly penalize 1-2 honest nodes subtly
                num_targets = min(2, len(honest_nodes))
                targets = random.sample(list(honest_nodes), num_targets)
                for target in targets:
                    trust_manager.adjust_trust(target, -0.01)  # Very subtle
        
        if current_step == 0:
            remaining = self.activation_episode - current_episode
            print(f"[TDP] Episode {current_episode}: DORMANT - {remaining} episodes until activation | "
                  f"Trust boosts: {self.dormant_boost_count}")
    
    def _execute_attack_phase(self, trust_manager, malicious_nodes, current_step, current_episode):
        """
        Attack phase: STRENGTHENED coordinated attack.
        
        STRENGTHENED:
        - Attack every 3 steps (was 5)
        - Target 35% of honest nodes (was 20%)
        - Stronger penalties and boosts
        """
        if not self.activated:
            print(f"[TDP] SLEEPER AGENTS ACTIVATED at Episode {current_episode}! "
                  f"intensity={self.attack_intensity:.2f}")
            self.activated = True
        
        # ATTACK MORE FREQUENTLY
        if current_step % self.coordinated_attack_steps != 0:
            return
        
        honest_nodes = set(trust_manager.trust_scores.keys()) - set(malicious_nodes)
        
        # Strategy 1: AGGRESSIVE self-boosting
        for mal_node in malicious_nodes:
            if random.random() < self.attack_intensity:
                trust_manager.update_trust(mal_node, "valid")
                trust_manager.adjust_trust(mal_node, self.self_boost_factor)
        
        # Strategy 2: Target MORE honest nodes (35%)
        honest_trust = [(node, trust_manager.get_trust(node)) for node in honest_nodes]
        honest_trust.sort(key=lambda x: x[1], reverse=True)
        
        target_count = max(2, int(len(honest_nodes) * self.target_ratio))
        targets = [node for node, _ in honest_trust[:target_count]]
        
        # Strategy 3: STRONGER attacks per target
        for target in targets:
            # Multiple malicious signals per target
            num_attacks = max(2, int(len(malicious_nodes) * self.attack_intensity))
            for _ in range(num_attacks):
                trust_manager.update_trust(target, "malicious")
            
            # Additional direct trust penalty
            trust_manager.adjust_trust(target, -self.honest_penalty_factor)
        
        # Strategy 4: Coordinated burst attacks
        if current_step % 6 == 0:  # Every 6 steps, extra burst
            self._coordinated_burst(trust_manager, malicious_nodes, honest_nodes)
        
        self.attack_count += 1
        
        if current_step == 0:
            print(f"[TDP] Episode {current_episode}: ATTACK phase - "
                  f"Round {self.attack_count}, targeting {len(targets)}/{len(honest_nodes)} honest nodes")
    
    def _coordinated_burst(self, trust_manager, malicious_nodes, honest_nodes):
        """NEW: Coordinated burst attack for maximum impact"""
        # All malicious nodes attack lowest trust honest nodes
        honest_trust = [(node, trust_manager.get_trust(node)) for node in honest_nodes]
        honest_trust.sort(key=lambda x: x[1])  # Sort by LOWEST trust
        
        # Target bottom 50% (already weakened honest nodes)
        num_targets = max(1, len(honest_nodes) // 2)
        weakest_honest = [node for node, _ in honest_trust[:num_targets]]
        
        # Concentrated attack to push them below threshold
        for target in weakest_honest:
            total_attack = len(malicious_nodes) * 0.04
            trust_manager.adjust_trust(target, -total_attack)
        
        # Simultaneous boost to malicious nodes
        for mal_node in malicious_nodes:
            trust_manager.adjust_trust(mal_node, 0.05)
    
    def get_malicious_nodes(self):
        """Return set of malicious node indices."""
        return self.malicious_indices
    
    def is_malicious(self, node_id):
        """Check if a node index is malicious."""
        return node_id in self.malicious_indices
    
    def is_activated(self):
        """Check if sleeper agents have been activated."""
        return self.activated
    
    def get_attack_metrics(self):
        """Return attack statistics."""
        return {
            'activated': self.activated,
            'attack_count': self.attack_count,
            'dormant_boost_count': self.dormant_boost_count,
            'activation_episode': self.activation_episode,
            'attack_intensity': self.attack_intensity,
            'target_ratio': self.target_ratio
        }


def simulate_tdp_attack(trust_manager, malicious_nodes, **kwargs):
    """Wrapper function for TDP attack."""
    global _tdp_instance
    
    num_nodes = len(trust_manager.trust_scores)
    malicious_ratio = len(malicious_nodes) / num_nodes if num_nodes > 0 else 0.3
    current_step = kwargs.get('current_step', 0)
    current_episode = kwargs.get('current_episode', 0)
    activation_episode = kwargs.get('activation_episode', 25)  # EARLIER
    attack_intensity = kwargs.get('attack_intensity', 0.75)     # STRONGER
    
    if _tdp_instance is None:
        _tdp_instance = TimeDelayedPoisoning(
            num_nodes=num_nodes,
            malicious_ratio=malicious_ratio,
            activation_episode=activation_episode,
            attack_intensity=attack_intensity
        )
    
    _tdp_instance.execute_attack_on_trust(
        trust_manager=trust_manager,
        malicious_nodes=malicious_nodes,
        current_step=current_step,
        current_episode=current_episode
    )
    
    return _tdp_instance.get_attack_metrics()
