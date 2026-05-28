# Architecture

## Runtime Flow

1. `main.py` delegates to `src/simulation/main.py`.
2. CLI options are parsed and merged with `config/default.yaml`.
3. `SimulationManager` wires together:
   - `src.abac`
   - `src.trust`
   - `src.consensus`
   - `src.blockchain`
   - `src.attacks`
   - `src.agents`
   - `src.rewards`
4. Each episode runs:
   - transaction generation
   - ABAC filtering
   - optional attack injection
   - delegate selection
   - consensus
   - trust update
   - reward computation
   - agent training
5. Outputs are written under `experiments/`.

## Package Boundaries

- `src/simulation`: orchestration and runtime entry logic
- `src/abac`: ABAC and FHE
- `src/consensus`: TDCB consensus
- `src/trust`: trust manager
- `src/blockchain`: blockchain data structures
- `src/attacks`: attack models and attack dispatch
- `src/agents`: RL, DRL, MARL agents
- `src/rewards`: reward shaping
- `src/utils`: plotting and structured logging
- `src/baselines`: non-learning consensus baselines
- `src/api`: API and streaming endpoints

## Compatibility

Legacy top-level module names are preserved as shims so older scripts and tests continue to work.
