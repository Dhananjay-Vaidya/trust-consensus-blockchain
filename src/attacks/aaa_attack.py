# aaa_attack.py - STRENGTHENED Adaptive Adversarial Attack
"""
Advanced Adaptive Adversarial Attack (AAA) for Blockchain Trust Systems

BALANCED VERSION:
- Stronger trust manipulation (0.12-0.15 vs 0.02-0.05)
- More frequent attacks
- Better coordination between strategies
- Target F1: 0.75-0.85 (instead of 1.0)

Research References:
- Tramèr et al. (2020): On Adaptive Attacks to Adversarial Example Defenses
- Fan et al. (2025): Adaptive Expert-Guided Adversarial Attack Against DRL
"""

import numpy as np
import random
from collections import deque

# Global instance for state persistence
_aaa_instance = None


def reset_aaa_instance():
    """Reset AAA instance for clean simulation restarts."""
    global _aaa_instance
    _aaa_instance = None


class AdaptiveAdversarialAttack:
    """
    Sophisticated AAA that learns and adapts to defense mechanisms.
    
    STRENGTHENED VERSION:
    - Higher trust manipulation factors
    - More aggressive coordination
    - Faster adaptation
    """
    
    def __init__(self, num_nodes, malicious_ratio=0.3):
        self.num_nodes = num_nodes
        self.malicious_ratio = malicious_ratio
        self.num_malicious = int(num_nodes * malicious_ratio)
        
        # Attack state tracking
        self.attack_history = deque(maxlen=100)
        self.trust_gradients = {}
        self.defense_patterns = {}
        self.attack_phase = 'exploration'
        
        # Performance metrics
        self.success_rate = 0.0
        self.detection_rate = 0.0
        self.phase_counter = 0
        
        # Attack strategies
        self.attack_strategies = [
            'gradient_exploitation',
            'slow_poisoning',
            'strategic_cooperation', 
            'mimicry_attack',
            'temporal_coordination'
        ]
        self.current_strategy_idx = 0
        self.strategy_performance = {s: [] for s in self.attack_strategies}
        
        # FASTER annealing (more exploitation)
        self.initial_epsilon = 0.8  # REDUCED from 1.0
        self.min_epsilon = 0.15     # INCREASED from 0.1
        self.epsilon_decay = 0.98   # SLOWER decay (was 0.995)
        self.epsilon = self.initial_epsilon
        
        # STRENGTHENED attack parameters
        self.trust_boost_factor = 0.12      # INCREASED from 0.05
        self.trust_penalty_factor = 0.10    # INCREASED from 0.02
        self.mimicry_convergence = 0.25     # INCREASED from 0.15
        self.coordination_interval = 8      # MORE FREQUENT (was 15)
        
        print(f"\n╔═══════════════════════════════════════════════════════════╗")
        print(f"║   🧠 ADAPTIVE ADVERSARIAL ATTACK (AAA) - STRENGTHENED 🧠  ║")
        print(f"╠═══════════════════════════════════════════════════════════╣")
        print(f"║  Malicious Nodes:  {self.num_malicious} / {num_nodes} ({malicious_ratio*100:.0f}%)                    ║")
        print(f"║  Trust Boost Factor: {self.trust_boost_factor} (INCREASED)              ║")
        print(f"║  Trust Penalty Factor: {self.trust_penalty_factor} (INCREASED)            ║")
        print(f"║  Coordination Interval: {self.coordination_interval} steps                    ║")
        print(f"║  Target F1: 0.75-0.85                                     ║")
        print(f"╚═══════════════════════════════════════════════════════════╝")
    
    def execute_attack(self, trust_manager, malicious_nodes, current_step, current_episode):
        """Execute adaptive attack based on learned patterns."""
        self._update_attack_phase(current_episode)
        strategy = self._select_attack_strategy()
        
        # Execute selected strategy with INCREASED intensity
        if strategy == 'gradient_exploitation':
            self._gradient_exploitation_attack(trust_manager, malicious_nodes)
        elif strategy == 'slow_poisoning':
            self._slow_poisoning_attack(trust_manager, malicious_nodes, current_step)
        elif strategy == 'strategic_cooperation':
            self._strategic_cooperation_attack(trust_manager, malicious_nodes)
        elif strategy == 'mimicry_attack':
            self._mimicry_attack(trust_manager, malicious_nodes)
        elif strategy == 'temporal_coordination':
            self._temporal_coordination_attack(trust_manager, malicious_nodes, current_step)
        
        # ALWAYS run coordination attacks more frequently
        if current_step % self.coordination_interval == 0:
            self._coordinated_burst_attack(trust_manager, malicious_nodes)
        
        self._learn_from_attack(trust_manager, malicious_nodes, strategy)
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
        
        if current_episode % 10 == 0 and current_step == 0:
            print(f"[AAA] Episode {current_episode} | Phase: {self.attack_phase} | "
                  f"Strategy: {strategy} | ε: {self.epsilon:.3f}")
    
    def _gradient_exploitation_attack(self, trust_manager, malicious_nodes):
        """Technique 1: STRENGTHENED Gradient-Based Trust Exploitation"""
        for node_id in malicious_nodes:
            current_trust = trust_manager.get_trust(node_id)
            
            if node_id in self.trust_gradients:
                gradient = self.trust_gradients[node_id]
            else:
                gradient = 0.02
            
            # STRONGER trust manipulation
            if current_trust < 0.35:  # Low trust - aggressive recovery
                trust_boost = random.uniform(0.10, 0.18) * (1.0 + gradient)
                trust_manager.adjust_trust(node_id, trust_boost)
            elif current_trust > 0.6:  # High trust - can attack
                # Attack honest nodes while trust is high
                honest_nodes = set(trust_manager.trust_scores.keys()) - malicious_nodes
                if honest_nodes:
                    target = random.choice(list(honest_nodes))
                    trust_manager.adjust_trust(target, -random.uniform(0.03, 0.08))
            else:
                # Medium trust - boost self
                trust_manager.adjust_trust(node_id, random.uniform(0.02, 0.06))
            
            new_trust = trust_manager.get_trust(node_id)
            self.trust_gradients[node_id] = (new_trust - current_trust) / (current_trust + 1e-6)
    
    def _slow_poisoning_attack(self, trust_manager, malicious_nodes, current_step):
        """Technique 2: STRENGTHENED Slow Poisoning"""
        # Attack every 3 steps (was 5)
        if current_step % 3 != 0:
            return
        
        honest_nodes = set(trust_manager.trust_scores.keys()) - malicious_nodes
        
        # STRONGER poison amount
        for node_id in honest_nodes:
            poison_amount = random.uniform(-0.025, -0.012)  # INCREASED
            trust_manager.adjust_trust(node_id, poison_amount)
        
        # STRONGER self-boost
        for node_id in malicious_nodes:
            if trust_manager.get_trust(node_id) < 0.7:
                trust_manager.adjust_trust(node_id, 0.015)  # INCREASED
    
    def _strategic_cooperation_attack(self, trust_manager, malicious_nodes):
        """Technique 3: STRENGTHENED Strategic Cooperation"""
        malicious_list = list(malicious_nodes)
        
        if len(malicious_list) < 2:
            return
        
        # More aggressive mutual boosting
        for i, node_id in enumerate(malicious_list):
            target1 = malicious_list[(i + 1) % len(malicious_list)]
            target2 = malicious_list[(i + 2) % len(malicious_list)]
            
            # STRONGER trust boosts
            trust_manager.adjust_trust(target1, 0.06)  # INCREASED from 0.03
            trust_manager.adjust_trust(target2, 0.04)  # INCREASED from 0.02
            
            # Also attack one honest node per malicious
            honest_nodes = set(trust_manager.trust_scores.keys()) - malicious_nodes
            if honest_nodes:
                victim = random.choice(list(honest_nodes))
                trust_manager.adjust_trust(victim, -0.03)
    
    def _mimicry_attack(self, trust_manager, malicious_nodes):
        """Technique 4: STRENGTHENED Mimicry Attack"""
        honest_nodes = set(trust_manager.trust_scores.keys()) - malicious_nodes
        
        if not honest_nodes:
            return
        
        # Find highest trust honest node
        honest_trust_scores = {n: trust_manager.get_trust(n) for n in honest_nodes}
        target_honest = max(honest_trust_scores, key=honest_trust_scores.get)
        target_trust = honest_trust_scores[target_honest]
        
        for node_id in malicious_nodes:
            current_trust = trust_manager.get_trust(node_id)
            trust_diff = target_trust - current_trust
            
            # FASTER convergence to mimic
            adjustment = trust_diff * self.mimicry_convergence
            trust_manager.adjust_trust(node_id, adjustment)
            
            # Simultaneously drag down the target honest node slightly
            if random.random() < 0.4:
                trust_manager.adjust_trust(target_honest, -0.02)
    
    def _temporal_coordination_attack(self, trust_manager, malicious_nodes, current_step):
        """Technique 5: STRENGTHENED Temporal Coordination"""
        if current_step % 10 != 0:  # More frequent (was 15)
            return
        
        honest_nodes = set(trust_manager.trust_scores.keys()) - malicious_nodes
        
        if not honest_nodes:
            return
        
        # Target MORE honest nodes (40% instead of 30%)
        num_targets = max(2, int(len(honest_nodes) * 0.4))
        targets = random.sample(list(honest_nodes), min(num_targets, len(honest_nodes)))
        
        # STRONGER coordinated attack
        for target in targets:
            reduction_per_attacker = -0.06 / max(1, len(malicious_nodes))  # INCREASED
            for node_id in malicious_nodes:
                trust_manager.adjust_trust(target, reduction_per_attacker)
        
        # STRONGER mutual boost
        for node_id in malicious_nodes:
            trust_manager.adjust_trust(node_id, 0.08)  # INCREASED from 0.06
    
    def _coordinated_burst_attack(self, trust_manager, malicious_nodes):
        """NEW: Coordinated burst attack at regular intervals"""
        honest_nodes = set(trust_manager.trust_scores.keys()) - malicious_nodes
        
        if not honest_nodes:
            return
        
        # Find honest nodes with highest trust and attack them
        honest_trust_scores = [(n, trust_manager.get_trust(n)) for n in honest_nodes]
        honest_trust_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Attack top 30% honest nodes
        num_targets = max(1, int(len(honest_nodes) * 0.3))
        targets = [n for n, _ in honest_trust_scores[:num_targets]]
        
        for target in targets:
            # All malicious nodes attack together
            total_attack = -0.04 * len(malicious_nodes) / len(targets)
            trust_manager.adjust_trust(target, total_attack)
    
    def _update_attack_phase(self, current_episode):
        """Update attack phase."""
        self.phase_counter += 1
        
        if current_episode < 10:  # FASTER transitions
            self.attack_phase = 'exploration'
        elif current_episode < 25:
            self.attack_phase = 'exploitation'
        else:
            self.attack_phase = 'evasion'
    
    def _select_attack_strategy(self):
        """Select attack strategy using ε-greedy with ensemble."""
        if random.random() < self.epsilon:
            return random.choice(self.attack_strategies)
        
        if not any(self.strategy_performance.values()):
            strategy = self.attack_strategies[self.current_strategy_idx]
            self.current_strategy_idx = (self.current_strategy_idx + 1) % len(self.attack_strategies)
            return strategy
        
        avg_performance = {s: np.mean(perf) if perf else 0.0 
                          for s, perf in self.strategy_performance.items()}
        return max(avg_performance, key=avg_performance.get)
    
    def _learn_from_attack(self, trust_manager, malicious_nodes, strategy):
        """Learn from attack outcome."""
        malicious_trusts = [trust_manager.get_trust(n) for n in malicious_nodes]
        avg_malicious_trust = np.mean(malicious_trusts) if malicious_trusts else 0.0
        
        honest_nodes = set(trust_manager.trust_scores.keys()) - malicious_nodes
        honest_trusts = [trust_manager.get_trust(n) for n in honest_nodes]
        avg_honest_trust = np.mean(honest_trusts) if honest_trusts else 0.5
        
        # Success = high malicious trust + low honest trust
        success_score = avg_malicious_trust * (1.0 - avg_honest_trust) + 0.5 * (avg_malicious_trust - avg_honest_trust + 0.5)
        
        self.strategy_performance[strategy].append(success_score)
        if len(self.strategy_performance[strategy]) > 100:
            self.strategy_performance[strategy] = self.strategy_performance[strategy][-100:]
        
        self.attack_history.append(success_score)
        self.success_rate = np.mean(list(self.attack_history))


def simulate_aaa_attack(trust_manager, malicious_nodes, **kwargs):
    """Wrapper function for AAA attack."""
    global _aaa_instance
    
    if _aaa_instance is None:
        num_nodes = len(trust_manager.trust_scores)
        malicious_ratio = len(malicious_nodes) / num_nodes if num_nodes > 0 else 0.3
        _aaa_instance = AdaptiveAdversarialAttack(
            num_nodes=num_nodes,
            malicious_ratio=malicious_ratio
        )
    
    _aaa_instance.execute_attack(
        trust_manager=trust_manager,
        malicious_nodes=malicious_nodes,
        current_step=kwargs.get('current_step', 0),
        current_episode=kwargs.get('current_episode', 0)
    )
