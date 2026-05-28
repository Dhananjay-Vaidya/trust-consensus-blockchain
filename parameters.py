from __future__ import annotations

from config.config_loader import load_config


_CFG = load_config("config/default.yaml")

# Network configuration
TRANSACTION_SIZE_AVG = 256
BLOCK_HEADER_SIZE = 64
TOTAL_NODES = _CFG.num_nodes
SIGNATURE_VERIFICATION_COST = 0.01
BLOCK_INTERVAL = 10
DATA_TRANSMISSION_SPEED = 1000
MAX_BLOCK_INTERVAL = 60
BATCH_SIZE = _CFG.batch_size
BLOCK_SIZE_MB = 4
MAC_CREATION_VERIFICATION_COST = 0.005
NODE_COMPUTING_CAPACITY = 10
MAX_TRANSACTION_THROUGHPUT = 50
MAX_COMPUTATION_COST = NODE_COMPUTING_CAPACITY * TOTAL_NODES

# Trust configuration
TRUST_THRESHOLD = _CFG.threshold
MALICIOUS_RATIO = _CFG.malicious_fraction
TRUST_VALID_BOOST = _CFG.valid_boost
TRUST_INVALID_PENALTY = _CFG.invalid_penalty
TRUST_MALICIOUS_PENALTY = _CFG.malicious_penalty
TRUST_MALICIOUS_ALPHA_DECAY = _CFG.malicious_alpha_decay
TRUST_DECAY_RATE = _CFG.decay_rate
CONSENSUS_THRESHOLD = _CFG.consensus_threshold
GROUND_TRUTH_UPDATE_INTERVAL = _CFG.ground_truth_update_interval
TRUST_NOISE_LEVEL = _CFG.noise_level
INITIAL_TRUST_VARIANCE = _CFG.initial_variance

# Training configuration
EPISODES = _CFG.episodes
STEPS_PER_EPISODE = _CFG.steps_per_episode
CHAIN_NORM = _CFG.chain_norm
CONSENSUS_NORM = _CFG.consensus_norm
ACTION_SPACE_SIZE = _CFG.action_space_size
ACTION_MAP: dict[int, tuple[float, float, float]] = {}

# Reward weights
F1_REWARD_WEIGHT = _CFG.f1_reward_weight
STEP_REWARD_WEIGHT = _CFG.step_reward_weight
FN_PENALTY_WEIGHT = _CFG.fn_penalty_weight

# Attack parameters
CRA_INTENSITY = _CFG.cra_intensity
CRA_ATTACK_FREQUENCY = _CFG.cra_attack_frequency
TDP_ACTIVATION_EPISODE = _CFG.tdp_activation_episode
TDP_ATTACK_INTENSITY = _CFG.tdp_attack_intensity

AAA_CONFIG = {
    "epsilon_decay": 0.98,
    "trust_boost_factor": 0.12,
    "trust_penalty_factor": 0.08,
    "mimicry_convergence": 0.25,
    "coordination_steps": 8,
}

BFI_CONFIG = {
    "equivocation_rate": 0.85,
    "sybil_amplification": 4,
    "eclipse_target_count": 3,
    "trust_manipulation_factor": 0.15,
    "adaptive_threshold": 0.45,
    "coordination_window": 8,
}

TDP_CONFIG = {
    "activation_episode": _CFG.tdp_activation_episode,
    "attack_intensity": _CFG.tdp_attack_intensity,
    "dormant_boost_probability": 0.4,
    "target_ratio": 0.35,
    "coordinated_attack_steps": 3,
}

# FHE and mining
FHE_ENABLED = _CFG.fhe_enabled
FHE_OVERHEAD_LOG: list[float] = []
MINE_EVERY_N_STEPS = _CFG.mine_every_n_steps

# Runtime feature toggles
NO_ABAC = False
NO_DECAY = False
DELEGATE_STRATEGY = "thompson"
ACTION_DIMS = 3
