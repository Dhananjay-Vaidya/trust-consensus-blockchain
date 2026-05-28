# Codebase Documentation

## Purpose

This repository implements a blockchain-IoT trust simulation that compares `RL`, `DRL`, and `MARL` agents against five attack families: `NMA`, `CRA`, `AAA`, `BFI`, and `TDP`. The runtime entrypoint is [`main.py`](main.py), which wires together configuration, node initialization, trust management, ABAC filtering, attack injection, delegated consensus, agent learning, metrics, plots, checkpoints, and CSV result export.

## Main Runtime Path

### Entry point

- `python main.py --agent drl --attack cra --nodes 16 --episodes 50 --steps 30`
- `main()` in `main.py` parses CLI arguments, mutates values in `parameters.py`, instantiates `SimulationManager`, and calls `run_simulation()`.

### How everything integrates into `main.py`

`main.py` is the orchestration layer. Its integration flow is:

1. `main()` reads CLI arguments and overwrites global config values in `parameters.py`.
2. `SimulationManager.__init__()` resets persistent attack instances and initializes:
   - `ABAC` from `abac.py`
   - `FullyHomomorphicEncryption` from `fhe.py`
   - `RewardSystem` from `reward.py`
   - `TDCB` from `tdcb.py`
   - `Blockchain` from `blockchain.py`
   - One learning agent:
     - `RLAgent` from `rl_agent.py`
     - `DDQN` from `drl_d3p.py`
     - `MARLAgent` from `marl_agent.py`
3. `_init_nodes()` creates `Node_0 ... Node_n`, samples malicious nodes, assigns ABAC attributes, and creates `TrustManager` from `trust.py`.
4. `run_simulation()` loops over episodes and calls `run_episode()`.
5. `run_episode()` loops over steps and does:
   - generate transactions
   - ABAC/trust filtering
   - periodic trust decay
   - periodic attack injection through `attack_util.apply_attack()`
   - agent action selection for delegation-ratio adjustment
   - delegate selection through `TrustManager.select_delegated_nodes()`
   - trust-weighted consensus through `TDCB.execute_consensus()`
   - blockchain pending-transaction accumulation
   - trust updates for malicious and valid delegates
   - periodic ground-truth trust corrections
   - state recomputation
   - reward shaping through `RewardSystem.calculate_shaped_rewards()`
   - agent replay/training update
6. End of episode:
   - detection quality is evaluated with `_evaluate_results()`
   - best model checkpoints are saved if the agent implements `save_model`
7. End of simulation:
   - plots are generated via `plot_util.py`
   - results and parameter CSVs are written under `results/`

## Execution Workflow

### Step-level workflow

For each simulation step inside `SimulationManager.run_episode()`:

1. Random transactions are generated.
2. Each transaction sender is checked by `ABAC.enforce_policy_with_learning()`.
3. Trust decay is applied every 5 steps.
4. If an attack mode is active, `attack_util.apply_attack()` mutates trust scores every 5 steps.
5. The selected agent emits an adjustment in `{0.9, 1.0, 1.1}`.
6. `blockchain.delegation_ratio` is scaled by that adjustment and clamped to `[0.1, 1.0]`.
7. `TrustManager.select_delegated_nodes()` uses Thompson sampling on Beta trust distributions.
8. `TDCB.execute_consensus()` collects delegate votes, aggregates them with trust weighting, flags Byzantine behavior, and returns verified transactions.
9. Verified transactions are pushed into the blockchain pending pool via `Blockchain.add_transaction()`.
10. Malicious delegates get penalized in `TrustManager`; non-malicious delegates get positive trust updates.
11. Ground-truth periodic corrections reinforce known honest and malicious nodes.
12. The new environment state vector is computed.
13. `RewardSystem` computes shaped rewards from trust separation and detection quality.
14. The active learning agent stores experience and trains.

### Episode outputs

Per episode, `main.py` tracks:

- cumulative reward
- F1 score
- precision
- recall
- blockchain length
- last block transaction count
- byzantine detections
- trust separation
- false positives
- false negatives

### Final outputs

At the end of a simulation run, `main.py`:

- prints a classification report
- generates plots in `images/`
- writes `*_episode_metrics.csv` and `*_simulation_parameters.csv` in `results/`
- saves best-model checkpoints in `checkpoints/`

## State and Learning Design

### State vector used by agents

`SimulationManager._compute_state()` builds a 16-dimensional state:

1. average trust
2. trust variance
3. trust skew
4. trust median
5. trust range
6. trust IQR
7. coefficient of variation
8. normalized consensus output
9. normalized blockchain length
10. honest-to-malicious ratio
11. fraction of low-trust nodes
12. fraction of high-trust nodes
13. delegation efficiency
14. normalized throughput rate
15. blocks added in last 5 episodes
16. scaled collusion score

### Agent roles

- `rl_agent.py`: tabular-style discrete adjustment controller backed by a dueling DQN implementation.
- `drl_d3p.py`: the default `DDQN` agent with noisy layers and prioritized replay.
- `marl_agent.py`: per-node multi-agent variant with attention, local replay, and shared replay.

All three agents ultimately control only one system variable during runtime: `blockchain.delegation_ratio`.

## Module Connections

### Core dependency graph

- `main.py`
  - imports `parameters`
  - imports `ABAC` from `abac.py`
  - imports `FullyHomomorphicEncryption` from `fhe.py`
  - imports `TrustManager` from `trust.py`
  - imports `RewardSystem` from `reward.py`
  - imports `TDCB` from `tdcb.py`
  - imports `DDQN` from `drl_d3p.py`
  - imports `MARLAgent` from `marl_agent.py`
  - conditionally imports `RLAgent` from `rl_agent.py`
  - imports plot functions from `plot_util.py`
  - imports `apply_attack` and `reset_attack_instances` from `attack_util.py`
- `attack_util.py`
  - imports `nma_attack`, `cra_attack`, `aaa_attack`, `bfi_attack`, `tdp_attack`
- `abac.py`
  - lazily imports `FullyHomomorphicEncryption` from `fhe.py` when `fhe_enabled=True`
- `compare_agents.py`
  - imports `parameters`
  - imports plot helpers
  - tries to import `SimulationManager` from `simulation_manager`, but no such file exists in this repo

## File-by-File Documentation

### Root Python files

#### `main.py`

- Role: main orchestration script and executable entrypoint.
- Imports:
  - `os`, `time`, `random`, `numpy`, `torch`, `torch.nn.functional`, `sys`, `argparse`, `pandas`
  - `classification_report`, `confusion_matrix` from `sklearn.metrics`
  - `tqdm`
  - `parameters as params`
  - `ABAC`, `FullyHomomorphicEncryption`, `TrustManager`, `RewardSystem`, `TDCB`, `DDQN`, `MARLAgent`
  - plotting helpers from `plot_util`
  - `apply_attack`, `reset_attack_instances` from `attack_util`
- Top-level objects:
  - `detect_collusion()`
  - `BatchProcessor`
  - `SimulationManager`
  - `main()`
- Key responsibilities:
  - CLI parsing and parameter override
  - system bootstrap
  - episode/step loop
  - attack scheduling
  - agent action/training loop
  - trust evaluation and F1 computation
  - plot generation
  - CSV and checkpoint export
- Connections:
  - central integration point for the entire project

#### `parameters.py`

- Role: global configuration constants.
- Imports: none.
- Defines:
  - network settings
  - trust thresholds and penalties
  - training episode defaults
  - normalization constants
  - attack parameter dictionaries for `AAA`, `BFI`, `TDP`
- Runtime use:
  - imported by `main.py`
  - imported by `compare_agents.py`
  - mutated in `main.py` from CLI arguments

#### `trust.py`

- Role: Bayesian trust management.
- Imports:
  - `torch`, `numpy`, `heapq`, `random`
  - `beta` from `scipy.stats`
- Top-level objects:
  - `TrustManager`
- Main methods:
  - `update_trust()`
  - `adjust_trust()`
  - `decay_trust()`
  - `get_trust()`
  - `get_trust_with_uncertainty()`
  - `select_delegated_nodes()`
  - `select_delegates_ucb()`
  - `calculate_trust_snapshot()`
  - `get_reputation_metrics()`
  - `get_statistics()`
  - `get_trust_distribution()`
  - `reset()`
- Connections:
  - receives direct attack manipulations from attack modules
  - provides delegate selection to `main.py`
  - provides trust features to reward and evaluation logic

#### `tdcb.py`

- Role: trust-weighted delegated consensus implementation.
- Imports:
  - `torch`
  - `hashlib`
  - typing utilities
- Top-level objects:
  - `TDCB`
- Main methods:
  - `execute_consensus()`
  - `_collect_votes()`
  - `_aggregate_votes()`
  - `_detect_byzantine_behavior()`
  - `_verify_transaction()`
  - `_hash_transaction()`
  - `get_consensus_metrics()`
- Connections:
  - called by `main.py`
  - consumes current delegated nodes and trust snapshot
  - returns verified transactions and malicious delegate detections

#### `blockchain.py`

- Role: blockchain data structure and block mining logic.
- Imports:
  - `hashlib`, `time`
  - typing utilities
  - `dataclass`, `field`
- Top-level objects:
  - `Block`
  - `Blockchain`
- Main methods:
  - `Block.calculate_hash()`
  - `Block.mine_block()`
  - `Blockchain.add_transaction()`
  - `Blockchain.mine_pending_transactions()`
  - `Blockchain.is_chain_valid()`
- Connections:
  - created by `main.py`
  - receives verified transactions from `TDCB` output
  - exposes `delegation_ratio`, which is tuned by the RL agents

#### `reward.py`

- Role: reward shaping for learning.
- Imports:
  - `torch`, `numpy`
  - `Dict` from `typing`
- Top-level objects:
  - `RewardSystem`
- Main methods:
  - `calculate_rewards()`
  - `calculate_shaped_rewards()`
- Connections:
  - called by `main.py` after each step
  - uses trust separation between honest and malicious sets

#### `abac.py`

- Role: attribute-based access control with optional FHE-backed trust checks.
- Imports:
  - typing utilities
  - `dataclass`
  - `time`, `numpy`
  - `defaultdict`
- Top-level objects:
  - `AttributePolicy`
  - `ABAC`
- Main methods:
  - `_init_default_policies()`
  - `_get_fhe()`
  - `add_user_attributes()`
  - `check_attribute_requirements()`
  - `check_time_restrictions()`
  - `check_location_restrictions()`
  - `enforce_policy()`
  - `enforce_policy_with_fhe()`
  - `enforce_policy_with_learning()`
  - `learn_from_feedback()`
  - `adjust_trust_threshold()`
  - `get_policy_effectiveness()`
  - `reset_statistics()`
- Connections:
  - instantiated in `main.py`
  - each node gets attributes in `SimulationManager._init_nodes()`
  - filters transaction senders before consensus

#### `fhe.py`

- Role: FHE abstraction layer with TenSEAL when available and Fernet fallback otherwise.
- Imports:
  - `Fernet` from `cryptography.fernet`
  - optional `tenseal`, `numpy`
- Top-level objects:
  - `FullyHomomorphicEncryption`
- Main methods:
  - `encrypt_value()`
  - `encrypt_vector()`
  - `decrypt_value()`
  - `decrypt_vector()`
  - `compute_encrypted_mean()`
  - `compute_encrypted_comparison()`
  - `serialize()`
  - `deserialize()`
- Connections:
  - instantiated in `main.py`
  - lazily used by `ABAC` if FHE mode is enabled

#### `attack_util.py`

- Role: unified attack dispatch layer and attack-instance lifecycle.
- Imports:
  - `simulate_nma_attack`
  - `simulate_cra_attack`
  - `simulate_aaa_attack`
  - `ByzantineFaultInjection`
  - `TimeDelayedPoisoning`
- Top-level objects:
  - `apply_attack()`
  - `reset_attack_instances()`
  - `get_attack_description()`
  - `get_available_attacks()`
  - `is_valid_attack()`
  - `get_expected_f1_ranges()`
- Connections:
  - called by `main.py`
  - owns persistent attack instances across steps/episodes

#### `nma_attack.py`

- Role: naive malicious/noise manipulation attack.
- Imports:
  - `random`, `numpy`
  - typing utilities
  - `defaultdict`
- Top-level objects:
  - `NoiseManipulationAttack`
  - `simulate_nma_attack()`
  - `reset_nma_instance()`
- Behavior:
  - self-camouflage on malicious nodes
  - false-flag attacks on honest high-trust nodes
  - optional entropy injection
- Connections:
  - invoked indirectly via `attack_util.apply_attack()`

#### `cra_attack.py`

- Role: collusive rumor / coordinated reputation manipulation attack.
- Imports:
  - `random`, `numpy`
  - typing utilities
  - `deque`
- Top-level objects:
  - `CollusiveRumorAttack`
  - `simulate_cra_attack()`
  - `reset_cra_instance()`
- Behavior:
  - mutual malicious trust boosting
  - strategic honest-node suppression
  - stealth camouflage
- Connections:
  - invoked indirectly via `attack_util.apply_attack()`

#### `aaa_attack.py`

- Role: adaptive adversarial attack with multiple attack strategies and stateful learning.
- Imports:
  - `numpy`, `random`
  - `deque`
- Top-level objects:
  - `reset_aaa_instance()`
  - `AdaptiveAdversarialAttack`
  - `simulate_aaa_attack()`
- Strategies:
  - gradient exploitation
  - slow poisoning
  - strategic cooperation
  - mimicry attack
  - temporal coordination
- Connections:
  - invoked indirectly via `attack_util.apply_attack()`
  - mutates `TrustManager` through `adjust_trust()`

#### `bfi_attack.py`

- Role: Byzantine fault injection attack with Sybil and eclipse behaviors.
- Imports:
  - `random`, `numpy`
  - `defaultdict`, `deque`
- Top-level objects:
  - `reset_bfi_instance()`
  - `ByzantineFaultInjection`
  - `simulate_bfi_attack()`
- Behavior:
  - equivocation
  - Sybil amplification
  - eclipse attack
  - collusive trust boosting
  - coordinated strikes on honest nodes
- Connections:
  - instantiated and driven through `attack_util.apply_attack()`

#### `tdp_attack.py`

- Role: sleeper-agent time-delayed poisoning attack.
- Imports:
  - `random`, `numpy`
- Top-level objects:
  - `reset_tdp_instance()`
  - `TimeDelayedPoisoning`
  - `simulate_tdp_attack()`
- Behavior:
  - dormant trust-building phase
  - activated coordinated suppression phase after a chosen episode
- Connections:
  - instantiated and driven through `attack_util.apply_attack()`

#### `rl_agent.py`

- Role: reinforcement-learning agent for delegation adjustment.
- Imports:
  - `torch`, `torch.nn`, `torch.optim`, `torch.nn.functional`
  - `numpy`, `random`
  - `deque`
- Top-level objects:
  - `EnhancedD3QNetwork`
  - `PrioritizedReplayBuffer`
  - `RLAgent`
- Main responsibilities:
  - dueling network inference
  - prioritized replay
  - epsilon-greedy action selection
  - target-network updates
  - checkpoint saving
- Connections:
  - conditionally imported inside `SimulationManager._init_components()`

#### `drl_d3p.py`

- Role: deep RL agent used as the default `drl` option.
- Imports:
  - `torch`, `torch.nn`, `torch.optim`, `torch.nn.functional`
  - `numpy`, `random`
  - `deque`
- Top-level objects:
  - `D3QNetwork`
  - `PrioritizedReplayBuffer`
  - `NoisyLinear`
  - `DDQN`
- Main responsibilities:
  - dueling double DQN
  - noisy layers for exploration
  - prioritized replay
  - TD-error-based training
- Connections:
  - directly instantiated in `main.py` for `agent_type != rl and != marl`

#### `marl_agent.py`

- Role: multi-agent RL system with attention and shared replay.
- Imports:
  - `torch`, `torch.nn`, `torch.optim`, `torch.nn.functional`
  - `numpy`, `random`
  - `deque`
- Top-level objects:
  - `AttentionModule`
  - `AdvancedD3QNetwork`
  - `PrioritizedReplayBuffer`
  - `SharedExperienceBuffer`
  - `MARLAgent`
- Main responsibilities:
  - per-agent models and targets
  - local plus shared prioritized replay
  - attention-enhanced Q-network
  - soft target updates
- Connections:
  - instantiated in `main.py` when `--agent marl`

#### `plot_util.py`

- Role: simple plotting helpers used by the main simulation loop.
- Imports:
  - `matplotlib.pyplot`
  - `seaborn`
  - `confusion_matrix` from `sklearn.metrics`
- Top-level functions:
  - `plot_cumulative_reward()`
  - `plot_f1_score()`
  - `plot_blockchain_length()`
  - `plot_throughput()`
  - `plot_confusion_matrix_from_labels()`
- Connections:
  - called by `main.py` after simulation completes

#### `generate_paper_figures.py`

- Role: post-processing script for paper-ready aggregate figures and tables.
- Imports:
  - `os`, `pandas`, `numpy`, `matplotlib.pyplot`, `seaborn`
  - `Path` from `pathlib`
  - `argparse`
  - `defaultdict`
- Top-level functions:
  - `parse_filename()`
  - `load_all_results()`
  - `get_final_f1_scores()`
  - `compute_confusion_matrix_from_f1()`
  - `figure1_confusion_matrix_grid()`
  - `figure2_f1_comparison_bar()`
  - `figure3_reward_curves_combined()`
  - `figure4_tdp_reward_comparison()`
  - `figure5_f1_evolution()`
  - `figure6_throughput_comparison()`
  - `figure7_blockchain_length()`
  - `generate_summary_table()`
  - `generate_latex_table()`
  - `main()`
- Connections:
  - consumes CSVs from `results/`
  - writes consolidated outputs to `images/` or `new_res/`

#### `compare_agents.py`

- Role: experimental comparison helper script.
- Imports:
  - `matplotlib.pyplot`, `numpy`
  - `parameters as params`
  - plot helpers from `plot_util`
  - `SimulationManager` from `simulation_manager`
- Status:
  - currently inconsistent with this repository, because `simulation_manager.py` does not exist and `SimulationManager` is defined in `main.py`.
- Intended workflow:
  - run one simulation per agent type
  - generate comparative reward/F1/throughput/blockchain-length charts

### Root non-Python files

#### `readme.md`

- Role: top-level project overview, architecture summary, and quick-start instructions.

#### `requirements.txt`

- Role: Python dependency list for the project runtime and analysis stack.

#### `LICENSE`

- Role: repository license file.

#### `.gitignore`

- Role: Git ignore rules for generated artifacts and environment files.

## Data and Artifact Directories

### `results/`

Role:

- per-run raw metrics and per-run parameter snapshots exported by `main.py`

Filename pattern:

- `{nodes}_{episodes}_{agent}_{attack}_{malicious_pct}_episode_metrics.csv`
- `{nodes}_{episodes}_{agent}_{attack}_{malicious_pct}_simulation_parameters.csv`

Files:

- `results/10_100_drl_tdp_30_episode_metrics.csv`
- `results/10_100_drl_tdp_30_simulation_parameters.csv`
- `results/10_100_marl_tdp_30_episode_metrics.csv`
- `results/10_100_marl_tdp_30_simulation_parameters.csv`
- `results/10_100_rl_tdp_30_episode_metrics.csv`
- `results/10_100_rl_tdp_30_simulation_parameters.csv`
- `results/10_50_drl_aaa_30_episode_metrics.csv`
- `results/10_50_drl_aaa_30_simulation_parameters.csv`
- `results/10_50_drl_bfi_30_episode_metrics.csv`
- `results/10_50_drl_bfi_30_simulation_parameters.csv`
- `results/10_50_drl_cra_30_episode_metrics.csv`
- `results/10_50_drl_cra_30_simulation_parameters.csv`
- `results/10_50_drl_nma_30_episode_metrics.csv`
- `results/10_50_drl_nma_30_simulation_parameters.csv`
- `results/10_50_drl_tdp_30_episode_metrics.csv`
- `results/10_50_drl_tdp_30_simulation_parameters.csv`
- `results/10_50_marl_aaa_30_episode_metrics.csv`
- `results/10_50_marl_aaa_30_simulation_parameters.csv`
- `results/10_50_marl_bfi_30_episode_metrics.csv`
- `results/10_50_marl_bfi_30_simulation_parameters.csv`
- `results/10_50_marl_cra_30_episode_metrics.csv`
- `results/10_50_marl_cra_30_simulation_parameters.csv`
- `results/10_50_marl_nma_30_episode_metrics.csv`
- `results/10_50_marl_nma_30_simulation_parameters.csv`
- `results/10_50_marl_tdp_30_episode_metrics.csv`
- `results/10_50_marl_tdp_30_simulation_parameters.csv`
- `results/10_50_rl_aaa_30_episode_metrics.csv`
- `results/10_50_rl_aaa_30_simulation_parameters.csv`
- `results/10_50_rl_bfi_30_episode_metrics.csv`
- `results/10_50_rl_bfi_30_simulation_parameters.csv`
- `results/10_50_rl_cra_30_episode_metrics.csv`
- `results/10_50_rl_cra_30_simulation_parameters.csv`
- `results/10_50_rl_nma_30_episode_metrics.csv`
- `results/10_50_rl_nma_30_simulation_parameters.csv`
- `results/10_50_rl_tdp_30_episode_metrics.csv`
- `results/10_50_rl_tdp_30_simulation_parameters.csv`
- `results/16_100_drl_tdp_30_episode_metrics.csv`
- `results/16_100_drl_tdp_30_simulation_parameters.csv`
- `results/16_100_marl_tdp_30_episode_metrics.csv`
- `results/16_100_marl_tdp_30_simulation_parameters.csv`
- `results/16_100_rl_tdp_30_episode_metrics.csv`
- `results/16_100_rl_tdp_30_simulation_parameters.csv`
- `results/16_50_drl_aaa_30_episode_metrics.csv`
- `results/16_50_drl_aaa_30_simulation_parameters.csv`
- `results/16_50_drl_bfi_30_episode_metrics.csv`
- `results/16_50_drl_bfi_30_simulation_parameters.csv`
- `results/16_50_drl_cra_30_episode_metrics.csv`
- `results/16_50_drl_cra_30_simulation_parameters.csv`
- `results/16_50_drl_nma_30_episode_metrics.csv`
- `results/16_50_drl_nma_30_simulation_parameters.csv`
- `results/16_50_drl_tdp_30_episode_metrics.csv`
- `results/16_50_drl_tdp_30_simulation_parameters.csv`
- `results/16_50_marl_aaa_30_episode_metrics.csv`
- `results/16_50_marl_aaa_30_simulation_parameters.csv`
- `results/16_50_marl_bfi_30_episode_metrics.csv`
- `results/16_50_marl_bfi_30_simulation_parameters.csv`
- `results/16_50_marl_cra_30_episode_metrics.csv`
- `results/16_50_marl_cra_30_simulation_parameters.csv`
- `results/16_50_marl_nma_30_episode_metrics.csv`
- `results/16_50_marl_nma_30_simulation_parameters.csv`
- `results/16_50_marl_tdp_30_episode_metrics.csv`
- `results/16_50_marl_tdp_30_simulation_parameters.csv`
- `results/16_50_rl_aaa_30_episode_metrics.csv`
- `results/16_50_rl_aaa_30_simulation_parameters.csv`
- `results/16_50_rl_bfi_30_episode_metrics.csv`
- `results/16_50_rl_bfi_30_simulation_parameters.csv`
- `results/16_50_rl_cra_30_episode_metrics.csv`
- `results/16_50_rl_cra_30_simulation_parameters.csv`
- `results/16_50_rl_nma_30_episode_metrics.csv`
- `results/16_50_rl_nma_30_simulation_parameters.csv`
- `results/16_50_rl_tdp_30_episode_metrics.csv`
- `results/16_50_rl_tdp_30_simulation_parameters.csv`

### `images/`

Role:

- generated per-run plots from `main.py`
- generated aggregate paper plots and summary artifacts

Files:

- `images/attack_png.png`
- `images/blockchain_length_all.png`
- `images/blockchain_length_vs_episodes_drl_aaa.png`
- `images/blockchain_length_vs_episodes_drl_bfi.png`
- `images/blockchain_length_vs_episodes_drl_cra.png`
- `images/blockchain_length_vs_episodes_drl_nma.png`
- `images/blockchain_length_vs_episodes_drl_tdp.png`
- `images/blockchain_length_vs_episodes_marl_aaa.png`
- `images/blockchain_length_vs_episodes_marl_bfi.png`
- `images/blockchain_length_vs_episodes_marl_cra.png`
- `images/blockchain_length_vs_episodes_marl_nma.png`
- `images/blockchain_length_vs_episodes_marl_tdp.png`
- `images/blockchain_length_vs_episodes_rl_aaa.png`
- `images/blockchain_length_vs_episodes_rl_bfi.png`
- `images/blockchain_length_vs_episodes_rl_cra.png`
- `images/blockchain_length_vs_episodes_rl_nma.png`
- `images/blockchain_length_vs_episodes_rl_tdp.png`
- `images/confusion_matrix_drl_aaa.png`
- `images/confusion_matrix_drl_bfi.png`
- `images/confusion_matrix_drl_cra.png`
- `images/confusion_matrix_drl_nma.png`
- `images/confusion_matrix_drl_tdp.png`
- `images/confusion_matrix_grid.png`
- `images/confusion_matrix_marl_aaa.png`
- `images/confusion_matrix_marl_bfi.png`
- `images/confusion_matrix_marl_cra.png`
- `images/confusion_matrix_marl_nma.png`
- `images/confusion_matrix_marl_tdp.png`
- `images/confusion_matrix_rl_aaa.png`
- `images/confusion_matrix_rl_bfi.png`
- `images/confusion_matrix_rl_cra.png`
- `images/confusion_matrix_rl_nma.png`
- `images/confusion_matrix_rl_tdp.png`
- `images/cumulative_reward_vs_episodes_drl_aaa.png`
- `images/cumulative_reward_vs_episodes_drl_bfi.png`
- `images/cumulative_reward_vs_episodes_drl_cra.png`
- `images/cumulative_reward_vs_episodes_drl_nma.png`
- `images/cumulative_reward_vs_episodes_drl_tdp.png`
- `images/cumulative_reward_vs_episodes_marl_aaa.png`
- `images/cumulative_reward_vs_episodes_marl_bfi.png`
- `images/cumulative_reward_vs_episodes_marl_cra.png`
- `images/cumulative_reward_vs_episodes_marl_nma.png`
- `images/cumulative_reward_vs_episodes_marl_tdp.png`
- `images/cumulative_reward_vs_episodes_rl_aaa.png`
- `images/cumulative_reward_vs_episodes_rl_bfi.png`
- `images/cumulative_reward_vs_episodes_rl_cra.png`
- `images/cumulative_reward_vs_episodes_rl_nma.png`
- `images/cumulative_reward_vs_episodes_rl_tdp.png`
- `images/f1_comparison_bar.png`
- `images/f1_evolution_all.png`
- `images/f1_score_vs_episodes_drl_aaa.png`
- `images/f1_score_vs_episodes_drl_bfi.png`
- `images/f1_score_vs_episodes_drl_cra.png`
- `images/f1_score_vs_episodes_drl_nma.png`
- `images/f1_score_vs_episodes_drl_tdp.png`
- `images/f1_score_vs_episodes_marl_aaa.png`
- `images/f1_score_vs_episodes_marl_bfi.png`
- `images/f1_score_vs_episodes_marl_cra.png`
- `images/f1_score_vs_episodes_marl_nma.png`
- `images/f1_score_vs_episodes_marl_tdp.png`
- `images/f1_score_vs_episodes_rl_aaa.png`
- `images/f1_score_vs_episodes_rl_bfi.png`
- `images/f1_score_vs_episodes_rl_cra.png`
- `images/f1_score_vs_episodes_rl_nma.png`
- `images/f1_score_vs_episodes_rl_tdp.png`
- `images/f1_table.tex`
- `images/results_summary.csv`
- `images/reward_curves_combined.png`
- `images/tdp_reward_comparison.png`
- `images/throughput_comparison.png`
- `images/throughput_vs_episodes_drl_aaa.png`
- `images/throughput_vs_episodes_drl_bfi.png`
- `images/throughput_vs_episodes_drl_cra.png`
- `images/throughput_vs_episodes_drl_nma.png`
- `images/throughput_vs_episodes_drl_tdp.png`
- `images/throughput_vs_episodes_marl_aaa.png`
- `images/throughput_vs_episodes_marl_bfi.png`
- `images/throughput_vs_episodes_marl_cra.png`
- `images/throughput_vs_episodes_marl_nma.png`
- `images/throughput_vs_episodes_marl_tdp.png`
- `images/throughput_vs_episodes_rl_aaa.png`
- `images/throughput_vs_episodes_rl_bfi.png`
- `images/throughput_vs_episodes_rl_cra.png`
- `images/throughput_vs_episodes_rl_nma.png`
- `images/throughput_vs_episodes_rl_tdp.png`

### `new_res/`

Role:

- alternate output directory for consolidated post-processed paper figures

Files:

- `new_res/blockchain_length_all.png`
- `new_res/confusion_matrix_grid.png`
- `new_res/f1_comparison_bar.png`
- `new_res/f1_evolution_all.png`
- `new_res/f1_table.tex`
- `new_res/results_summary.csv`
- `new_res/reward_curves_combined.png`
- `new_res/tdp_reward_comparison.png`
- `new_res/throughput_comparison.png`

### `checkpoints/`

Role:

- saved best-model weights produced during training
- naming encodes agent, attack type, and F1 score at save time

Files:

- `checkpoints/best_model_marl_aaa_f1_0.4589.pth`
- `checkpoints/best_model_marl_aaa_f1_0.5636.pth`
- `checkpoints/best_model_marl_aaa_f1_0.6190.pth`
- `checkpoints/best_model_marl_aaa_f1_0.6444.pth`
- `checkpoints/best_model_marl_aaa_f1_0.6537.pth`
- `checkpoints/best_model_marl_aaa_f1_0.6761.pth`
- `checkpoints/best_model_marl_aaa_f1_0.6970.pth`
- `checkpoints/best_model_marl_aaa_f1_0.7333.pth`
- `checkpoints/best_model_marl_aaa_f1_0.8545.pth`
- `checkpoints/best_model_marl_aaa_f1_0.9086.pth`
- `checkpoints/best_model_marl_aaa_f1_1.0000.pth`
- `checkpoints/best_model_marl_bfi_f1_0.4286.pth`
- `checkpoints/best_model_marl_bfi_f1_0.6444.pth`
- `checkpoints/best_model_marl_bfi_f1_0.7949.pth`
- `checkpoints/best_model_marl_bfi_f1_0.9086.pth`
- `checkpoints/best_model_marl_bfi_f1_1.0000.pth`
- `checkpoints/best_model_marl_cra_f1_0.2308.pth`
- `checkpoints/best_model_marl_cra_f1_0.3750.pth`
- `checkpoints/best_model_marl_cra_f1_0.6667.pth`
- `checkpoints/best_model_marl_cra_f1_0.7333.pth`
- `checkpoints/best_model_marl_cra_f1_0.7922.pth`
- `checkpoints/best_model_marl_cra_f1_0.8901.pth`
- `checkpoints/best_model_marl_cra_f1_1.0000.pth`
- `checkpoints/best_model_marl_nma_f1_0.7949.pth`
- `checkpoints/best_model_marl_nma_f1_1.0000.pth`
- `checkpoints/best_model_marl_tdp_f1_0.5466.pth`
- `checkpoints/best_model_marl_tdp_f1_0.5636.pth`
- `checkpoints/best_model_marl_tdp_f1_0.6000.pth`
- `checkpoints/best_model_marl_tdp_f1_0.6761.pth`
- `checkpoints/best_model_marl_tdp_f1_0.7333.pth`
- `checkpoints/best_model_marl_tdp_f1_0.7922.pth`
- `checkpoints/best_model_marl_tdp_f1_0.8545.pth`
- `checkpoints/best_model_marl_tdp_f1_0.8901.pth`
- `checkpoints/best_model_marl_tdp_f1_0.9227.pth`
- `checkpoints/best_model_marl_tdp_f1_1.0000.pth`
- `checkpoints/best_model_rl_aaa_f1_0.4589.pth`
- `checkpoints/best_model_rl_aaa_f1_0.5608.pth`
- `checkpoints/best_model_rl_aaa_f1_0.6970.pth`
- `checkpoints/best_model_rl_aaa_f1_0.7917.pth`
- `checkpoints/best_model_rl_aaa_f1_1.0000.pth`
- `checkpoints/best_model_rl_bfi_f1_0.4286.pth`
- `checkpoints/best_model_rl_bfi_f1_0.6444.pth`
- `checkpoints/best_model_rl_bfi_f1_0.7949.pth`
- `checkpoints/best_model_rl_bfi_f1_0.9086.pth`
- `checkpoints/best_model_rl_bfi_f1_1.0000.pth`
- `checkpoints/best_model_rl_cra_f1_0.4949.pth`
- `checkpoints/best_model_rl_cra_f1_0.5000.pth`
- `checkpoints/best_model_rl_cra_f1_0.6000.pth`
- `checkpoints/best_model_rl_cra_f1_0.6190.pth`
- `checkpoints/best_model_rl_cra_f1_0.6761.pth`
- `checkpoints/best_model_rl_cra_f1_0.7333.pth`
- `checkpoints/best_model_rl_cra_f1_0.8901.pth`
- `checkpoints/best_model_rl_cra_f1_1.0000.pth`
- `checkpoints/best_model_rl_nma_f1_0.4286.pth`
- `checkpoints/best_model_rl_nma_f1_0.6000.pth`
- `checkpoints/best_model_rl_nma_f1_0.6444.pth`
- `checkpoints/best_model_rl_nma_f1_0.6970.pth`
- `checkpoints/best_model_rl_nma_f1_0.9227.pth`
- `checkpoints/best_model_rl_nma_f1_1.0000.pth`
- `checkpoints/best_model_rl_tdp_f1_0.6537.pth`
- `checkpoints/best_model_rl_tdp_f1_0.7257.pth`
- `checkpoints/best_model_rl_tdp_f1_0.7333.pth`
- `checkpoints/best_model_rl_tdp_f1_0.9227.pth`
- `checkpoints/best_model_rl_tdp_f1_1.0000.pth`

## Important Notes and Observations

- `main.py` is the real system spine. If you want to understand execution, start there.
- `compare_agents.py` is stale relative to the current repo structure.
- `BatchProcessor` exists in `main.py` but is only lightly used; transaction tensors are prepared, but consensus still operates on Python dictionaries.
- `FullyHomomorphicEncryption` is instantiated by `main.py`, but the actual transaction path uses `ABAC.enforce_policy_with_learning()`, not the encrypted `enforce_policy_with_fhe()` path.
- `Blockchain.mine_pending_transactions()` exists, but `main.py` only appends verified transactions to `pending_transactions`; block mining is not actively triggered in the main episode loop.

## Recommended Reading Order

1. `main.py`
2. `parameters.py`
3. `trust.py`
4. `tdcb.py`
5. `abac.py`
6. `reward.py`
7. `attack_util.py`
8. attack modules: `nma_attack.py`, `cra_attack.py`, `aaa_attack.py`, `bfi_attack.py`, `tdp_attack.py`
9. active agent implementation for your run: `rl_agent.py`, `drl_d3p.py`, or `marl_agent.py`
10. `plot_util.py`
11. `generate_paper_figures.py`
