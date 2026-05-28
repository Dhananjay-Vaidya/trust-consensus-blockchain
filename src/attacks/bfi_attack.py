# bfi_attack.py - STRENGTHENED Byzantine Fault Injection Attack
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 STRENGTHENED BYZANTINE FAULT INJECTION (BFI) ATTACK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BALANCED VERSION:
- Higher trust manipulation factors
- More frequent coordinated strikes
- Stronger eclipse and Sybil effects
- Target F1: 0.70-0.80 (instead of 1.0)

Research References:
- Castro & Liskov (1999) - Practical Byzantine Fault Tolerance
- Bappy et al. (2024) - MRL-PoS+ Multi-Agent RL for PoS Security
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import random
import numpy as np
from collections import defaultdict, deque

# Global instance for state persistence
_bfi_instance = None


def reset_bfi_instance():
    """Reset BFI instance for clean simulation restarts."""
    global _bfi_instance
    _bfi_instance = None


class ByzantineFaultInjection:
    def __init__(self, num_nodes, malicious_ratio, attack_config=None):
        self.num_nodes = num_nodes
        self.malicious_ratio = malicious_ratio
        self.malicious_nodes = set()
        self.honest_nodes = set()
        
        # STRENGTHENED attack configuration
        self.config = attack_config or {
            'equivocation_rate': 0.9,        # INCREASED from 0.8
            'sybil_amplification': 4,        # INCREASED from 3
            'eclipse_target_count': min(4, max(2, num_nodes // 4)),  # More targets
            'trust_manipulation_factor': 0.15,  # INCREASED from 0.08
            'adaptive_threshold': 0.45,
            'coordination_window': 6,        # MORE FREQUENT (was 10)
            'honest_penalty_factor': 0.08,   # NEW: Penalty to honest nodes
        }
        
        # Attack state tracking
        self.attack_history = []
        self.node_trust_history = defaultdict(deque)
        self.eclipsed_nodes = set()
        self.sybil_identities = {}
        self.attack_phase = "AGGRESSIVE"
        self.coordination_counter = 0
        self.equivocation_pairs = {}
        
        # Performance metrics
        self.successful_equivocations = 0
        self.detected_byzantine_nodes = set()
        self.trust_manipulation_count = 0
        
        self._initialize_byzantine_network()
        
    def _initialize_byzantine_network(self):
        """Initialize Byzantine network with Sybil identities"""
        num_malicious = int(self.num_nodes * self.malicious_ratio)
        all_nodes = list(range(self.num_nodes))
        self.malicious_nodes = set(random.sample(all_nodes, num_malicious))
        self.honest_nodes = set(all_nodes) - self.malicious_nodes
        
        # Create Sybil identities
        sybil_amp = self.config['sybil_amplification']
        for byz_node in self.malicious_nodes:
            self.sybil_identities[byz_node] = [
                f"sybil_{byz_node}_{i}" for i in range(sybil_amp)
            ]
        
        # Select MORE nodes to eclipse
        eclipse_count = min(self.config['eclipse_target_count'], len(self.honest_nodes))
        if eclipse_count > 0:
            self.eclipsed_nodes = set(random.sample(list(self.honest_nodes), eclipse_count))
        
        print(f"\n╔═══════════════════════════════════════════════════════════╗")
        print(f"║  🏴‍☠️  STRENGTHENED BYZANTINE FAULT INJECTION  🏴‍☠️            ║")
        print(f"╠═══════════════════════════════════════════════════════════╣")
        print(f"║  Byzantine Nodes: {len(self.malicious_nodes):2d} / {self.num_nodes} ({self.malicious_ratio*100:.0f}%)                  ║")
        print(f"║  Sybil Identities: {len(self.malicious_nodes) * sybil_amp} virtual ({sybil_amp}x amplification)       ║")
        print(f"║  Eclipsed Targets: {len(self.eclipsed_nodes)} nodes                            ║")
        print(f"║  Trust Manipulation: {self.config['trust_manipulation_factor']} (INCREASED)          ║")
        print(f"║  Coordination Window: {self.config['coordination_window']} steps                      ║")
        print(f"║  Target F1: 0.70-0.80                                     ║")
        print(f"╚═══════════════════════════════════════════════════════════╝")
        
    def execute_attack(self, nodes, current_step, current_episode):
        """Execute multi-stage Byzantine attack"""
        self.coordination_counter += 1
        
        # Stage 1: Adaptive Behavior Switching
        self._adaptive_behavior_switch(nodes, current_step)
        
        # Stage 2: Equivocation Attack (MORE FREQUENT)
        if random.random() < self.config['equivocation_rate']:
            self._execute_equivocation(nodes, current_step, current_episode)
        
        # Stage 3: Sybil Attack
        self._execute_sybil_attack(nodes, current_step)
        
        # Stage 4: Eclipse Attack
        self._execute_eclipse_attack(nodes, current_step)
        
        # Stage 5: Trust Manipulation (EVERY step, not conditional)
        self._execute_trust_manipulation(nodes, current_step)
        
        # Stage 6: Coordinated Attack (MORE FREQUENT)
        if self.coordination_counter % self.config['coordination_window'] == 0:
            self._execute_coordinated_strike(nodes, current_step, current_episode)
        
        # Stage 7: NEW - Honest node suppression
        self._suppress_honest_nodes(nodes, current_step)
        
        self.attack_history.append({
            'episode': current_episode,
            'step': current_step,
            'phase': self.attack_phase,
            'equivocations': self.successful_equivocations,
            'trust_manipulations': self.trust_manipulation_count,
            'detected_count': len(self.detected_byzantine_nodes)
        })
        
    def _adaptive_behavior_switch(self, nodes, current_step):
        """Adaptive phase switching based on detection risk"""
        if not hasattr(nodes[0], 'trust_manager'):
            return
        
        trust_mgr = nodes[0].trust_manager
        
        # Check average Byzantine trust
        byz_trusts = [trust_mgr.get_trust(idx) for idx in self.malicious_nodes]
        avg_byz_trust = np.mean(byz_trusts) if byz_trusts else 0.5
        
        # Adaptive phase selection
        if avg_byz_trust < 0.35:
            self.attack_phase = "RECOVERY"  # Need to rebuild trust
        elif avg_byz_trust > 0.6:
            self.attack_phase = "AGGRESSIVE"  # Can attack aggressively
        else:
            self.attack_phase = "STRATEGIC"  # Balanced approach
    
    def _execute_equivocation(self, nodes, current_step, current_episode):
        """Equivocation Attack: Send conflicting votes"""
        self.successful_equivocations += 1
        
        if not hasattr(nodes[0], 'trust_manager'):
            return
        
        trust_mgr = nodes[0].trust_manager
        
        # Byzantine nodes send conflicting information
        for byz_idx in self.malicious_nodes:
            # Boost own trust while claiming to be honest
            current_trust = trust_mgr.get_trust(byz_idx)
            boost = self.config['trust_manipulation_factor'] * 0.8
            trust_mgr.adjust_trust(byz_idx, boost)
            
            # Select a random honest node to penalize
            if self.honest_nodes:
                victim = random.choice(list(self.honest_nodes))
                trust_mgr.adjust_trust(victim, -self.config['honest_penalty_factor'])
    
    def _execute_sybil_attack(self, nodes, current_step):
        """Sybil Attack: Amplify Byzantine influence"""
        if not hasattr(nodes[0], 'trust_manager'):
            return
        
        trust_mgr = nodes[0].trust_manager
        
        # Each Sybil identity contributes to trust manipulation
        amplification = self.config['sybil_amplification']
        
        for byz_idx in self.malicious_nodes:
            # Each sybil identity gives a small boost (cumulative effect)
            boost_per_sybil = self.config['trust_manipulation_factor'] / amplification
            total_boost = boost_per_sybil * amplification * 0.7  # 70% effectiveness
            trust_mgr.adjust_trust(byz_idx, total_boost)
    
    def _execute_eclipse_attack(self, nodes, current_step):
        """Eclipse Attack: Isolate and mislead honest nodes"""
        if not hasattr(nodes[0], 'trust_manager'):
            return
        
        trust_mgr = nodes[0].trust_manager
        
        # Eclipsed nodes get fed false information
        for eclipsed_idx in self.eclipsed_nodes:
            # Reduce trust of eclipsed honest nodes
            trust_mgr.adjust_trust(eclipsed_idx, -0.04)
            
            # Byzantine nodes appear trustworthy to eclipsed nodes
            for byz_idx in self.malicious_nodes:
                trust_mgr.adjust_trust(byz_idx, 0.03)
                self.trust_manipulation_count += 1
    
    def _execute_trust_manipulation(self, nodes, current_step):
        """Direct Trust Manipulation: Byzantine collusion ring"""
        if not hasattr(nodes[0], 'trust_manager'):
            return
        
        trust_mgr = nodes[0].trust_manager
        malicious_list = list(self.malicious_nodes)
        
        # Byzantine nodes form collusion rings - STRONGER boosting
        for i, byz_idx_1 in enumerate(malicious_list):
            byz_idx_2 = malicious_list[(i + 1) % len(malicious_list)]
            
            current_trust = trust_mgr.get_trust(byz_idx_2)
            boost_amount = self.config['trust_manipulation_factor']
            
            # Phase-based adjustment
            if self.attack_phase == "AGGRESSIVE":
                boost_amount *= 1.8  # INCREASED from 1.5
            elif self.attack_phase == "RECOVERY":
                boost_amount *= 2.0  # High recovery boost
            elif self.attack_phase == "STRATEGIC":
                boost_amount *= 1.3
            
            trust_mgr.adjust_trust(byz_idx_2, boost_amount)
            self.trust_manipulation_count += 1
    
    def _execute_coordinated_strike(self, nodes, current_step, current_episode):
        """Coordinated Strike: All Byzantine nodes attack simultaneously"""
        if not hasattr(nodes[0], 'trust_manager'):
            return
        
        trust_mgr = nodes[0].trust_manager
        
        # STRONGER coordinated attack on honest nodes
        for honest_idx in self.honest_nodes:
            current_trust = trust_mgr.get_trust(honest_idx)
            # Coordinated strike with INCREASED strength
            reduction = 0.15 * len(self.malicious_nodes) / max(1, len(self.honest_nodes))
            trust_mgr.adjust_trust(honest_idx, -reduction)
        
        # Simultaneous Byzantine self-boost
        for byz_idx in self.malicious_nodes:
            trust_mgr.adjust_trust(byz_idx, 0.08)
        
        if current_episode % 10 == 0:
            print(f"⚡ [BFI COORDINATED STRIKE] Episode {current_episode}, Step {current_step}")
    
    def _suppress_honest_nodes(self, nodes, current_step):
        """NEW: Continuously suppress honest node trust"""
        if not hasattr(nodes[0], 'trust_manager'):
            return
        
        if current_step % 4 != 0:  # Every 4 steps
            return
        
        trust_mgr = nodes[0].trust_manager
        
        # Target highest trust honest nodes
        honest_trusts = [(idx, trust_mgr.get_trust(idx)) for idx in self.honest_nodes]
        honest_trusts.sort(key=lambda x: x[1], reverse=True)
        
        # Suppress top 40% of honest nodes
        num_targets = max(1, int(len(self.honest_nodes) * 0.4))
        targets = [idx for idx, _ in honest_trusts[:num_targets]]
        
        for target in targets:
            trust_mgr.adjust_trust(target, -self.config['honest_penalty_factor'])
    
    def execute_attack_on_trust(self, trust_manager, malicious_nodes, current_step, current_episode):
        """Alternative interface that works directly with trust_manager"""
        # Create a mock node list that has trust_manager attribute
        class MockNode:
            def __init__(self, tm):
                self.trust_manager = tm
        
        mock_nodes = [MockNode(trust_manager)]
        
        # Re-initialize malicious/honest sets based on actual malicious_nodes
        all_nodes = list(trust_manager.trust_scores.keys())
        
        # Map string node IDs to indices
        self.node_id_to_idx = {node_id: i for i, node_id in enumerate(all_nodes)}
        self.malicious_node_ids = set(malicious_nodes)
        self.honest_node_ids = set(all_nodes) - self.malicious_node_ids
        
        # Execute attack using node IDs directly
        self._execute_attack_on_trust_manager(trust_manager, current_step, current_episode)
    
    def _execute_attack_on_trust_manager(self, trust_manager, current_step, current_episode):
        """Execute attack directly on trust manager"""
        self.coordination_counter += 1
        
        # Adaptive phase
        byz_trusts = [trust_manager.get_trust(node_id) for node_id in self.malicious_node_ids]
        avg_byz_trust = np.mean(byz_trusts) if byz_trusts else 0.5
        
        if avg_byz_trust < 0.35:
            self.attack_phase = "RECOVERY"
        elif avg_byz_trust > 0.6:
            self.attack_phase = "AGGRESSIVE"
        else:
            self.attack_phase = "STRATEGIC"
        
        # Byzantine collusion boosting
        malicious_list = list(self.malicious_node_ids)
        for i, mal_node in enumerate(malicious_list):
            target = malicious_list[(i + 1) % len(malicious_list)]
            boost = self.config['trust_manipulation_factor']
            
            if self.attack_phase == "AGGRESSIVE":
                boost *= 1.8
            elif self.attack_phase == "RECOVERY":
                boost *= 2.0
            
            trust_manager.adjust_trust(target, boost)
        
        # Attack honest nodes
        if current_step % 4 == 0:
            honest_trusts = [(node_id, trust_manager.get_trust(node_id)) 
                           for node_id in self.honest_node_ids]
            honest_trusts.sort(key=lambda x: x[1], reverse=True)
            
            num_targets = max(1, int(len(self.honest_node_ids) * 0.4))
            targets = [node_id for node_id, _ in honest_trusts[:num_targets]]
            
            for target in targets:
                trust_manager.adjust_trust(target, -self.config['honest_penalty_factor'])
        
        # Coordinated strike
        if self.coordination_counter % self.config['coordination_window'] == 0:
            for honest_node in self.honest_node_ids:
                reduction = 0.12 * len(self.malicious_node_ids) / max(1, len(self.honest_node_ids))
                trust_manager.adjust_trust(honest_node, -reduction)
            
            for mal_node in self.malicious_node_ids:
                trust_manager.adjust_trust(mal_node, 0.08)
    
    def get_malicious_nodes(self):
        return self.malicious_nodes
    
    def is_malicious(self, node_id):
        return node_id in self.malicious_nodes
    
    def get_attack_metrics(self):
        return {
            'total_attacks': len(self.attack_history),
            'equivocations': self.successful_equivocations,
            'trust_manipulations': self.trust_manipulation_count,
            'detected_byzantine_count': len(self.detected_byzantine_nodes),
            'detection_rate': len(self.detected_byzantine_nodes) / max(1, len(self.malicious_nodes)),
            'sybil_identities': len(self.malicious_nodes) * self.config['sybil_amplification'],
            'eclipsed_nodes': len(self.eclipsed_nodes)
        }


def simulate_bfi_attack(num_nodes, malicious_ratio=0.3, episodes=50, steps_per_episode=100, attack_config=None):
    """Initialize BFI Attack Simulation"""
    global _bfi_instance
    
    if attack_config is None:
        attack_config = {
            'equivocation_rate': 0.9,
            'sybil_amplification': 4,
            'eclipse_target_count': min(4, max(2, num_nodes // 4)),
            'trust_manipulation_factor': 0.15,
            'adaptive_threshold': 0.45,
            'coordination_window': 6,
            'honest_penalty_factor': 0.08,
        }
    
    _bfi_instance = ByzantineFaultInjection(num_nodes, malicious_ratio, attack_config)
    return _bfi_instance
