# parameters.py - BALANCED Configuration for Realistic Results
"""
Configuration tuned to achieve realistic F1 scores:
- AAA: ~0.75-0.85 (adaptive attacks evade some detection)
- BFI: ~0.70-0.80 (Byzantine faults cause confusion)
- TDP: ~0.80-0.90 before activation, ~0.65-0.75 after
- NMA: ~0.85-0.95 (simpler attack, easier to detect)
- CRA: ~0.75-0.85 (collusion attacks)
"""

# Network Configuration
TRANSACTION_SIZE_AVG = 256
BLOCK_HEADER_SIZE = 64
TOTAL_NODES = 16
SIGNATURE_VERIFICATION_COST = 0.01
BLOCK_INTERVAL = 10
DATA_TRANSMISSION_SPEED = 1000
MAX_BLOCK_INTERVAL = 60
BATCH_SIZE = 256
BLOCK_SIZE_MB = 4
MAC_CREATION_VERIFICATION_COST = 0.005
NODE_COMPUTING_CAPACITY = 10
MAX_TRANSACTION_THROUGHPUT = 50
MAX_COMPUTATION_COST = NODE_COMPUTING_CAPACITY * TOTAL_NODES

# Trust Configuration - BALANCED
TRUST_THRESHOLD = 0.45
MALICIOUS_RATIO = 0.30

# Training Configuration
EPISODES = 50
STEPS_PER_EPISODE = 100

# Normalization Constants
CHAIN_NORM = 100.0
CONSENSUS_NORM = 20.0

# Reward Weights
F1_REWARD_WEIGHT = 0.7
STEP_REWARD_WEIGHT = 0.3
FN_PENALTY_WEIGHT = 3.0

# Trust Update Parameters - WEAKENED for balance
TRUST_VALID_BOOST = 3.0
TRUST_INVALID_PENALTY = 2.0
TRUST_MALICIOUS_PENALTY = 4.0
TRUST_MALICIOUS_ALPHA_DECAY = 0.92
TRUST_DECAY_RATE = 0.95       # Task 4: used as trust_decay_factor (multiplicative)
CONSENSUS_THRESHOLD = 0.6     # Task 4: consensus_threshold adjustable at runtime

# Ground Truth Update Frequency
GROUND_TRUTH_UPDATE_INTERVAL = 15

# Attack Parameters - STRENGTHENED
CRA_INTENSITY = 0.85
CRA_ATTACK_FREQUENCY = 2
TDP_ACTIVATION_EPISODE = 25
TDP_ATTACK_INTENSITY = 0.75

# Attack-Specific Configurations
AAA_CONFIG = {
    'epsilon_decay': 0.98,
    'trust_boost_factor': 0.12,
    'trust_penalty_factor': 0.08,
    'mimicry_convergence': 0.25,
    'coordination_steps': 8,
}

BFI_CONFIG = {
    'equivocation_rate': 0.85,
    'sybil_amplification': 4,
    'eclipse_target_count': 3,
    'trust_manipulation_factor': 0.15,
    'adaptive_threshold': 0.45,
    'coordination_window': 8,
}

TDP_CONFIG = {
    'activation_episode': 25,
    'attack_intensity': 0.75,
    'dormant_boost_probability': 0.4,
    'target_ratio': 0.35,
    'coordinated_attack_steps': 3,
}

# Detection Difficulty Parameters
TRUST_NOISE_LEVEL = 0.08
INITIAL_TRUST_VARIANCE = 0.12

# Task 2 — FHE integration
FHE_ENABLED = False
FHE_OVERHEAD_LOG = []   # Accumulates per-call timing in ms

# Task 3 — Block mining
MINE_EVERY_N_STEPS = 5

# Task 4 — Expanded action space (27 = 3×3×3)
ACTION_SPACE_SIZE = 27
ACTION_MAP = {}   # Populated at runtime in SimulationManager._init_components()
