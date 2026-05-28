# Trust Consensus Blockchain

Trust-aware blockchain-IoT simulation platform for studying Byzantine detection, delegated consensus, ABAC/FHE overhead, and adaptive agent behavior across adversarial conditions.

The repository now supports both:

- the original CLI-driven simulation workflow
- a FastAPI + React web application for live execution, streaming, replay, and results comparison

## What The Project Covers

- Trust management for IoT nodes under malicious behavior
- TDCB and baseline consensus modes
- ABAC authorization with optional FHE overhead modeling
- RL, DRL-D3P, and MARL delegation agents
- Attack families: `none`, `nma`, `cra`, `aaa`, `bfi`, `tdp`
- Experiment outputs, replayable event streams, plots, and comparison tooling

## Architecture

Core runtime code lives under `src/`:

- `src/simulation/`
  Main orchestration, episode execution, callbacks, result writing
- `src/trust/`
  Trust state, updates, trust separation, node-level trust logic
- `src/consensus/`
  TDCB consensus and delegate selection behavior
- `src/blockchain/`
  Chain, blocks, transactions, mining, chain state
- `src/abac/`
  ABAC access control and FHE support
- `src/attacks/`
  Attack injection modules and helpers
- `src/agents/`
  RL, DRL-D3P, MARL agents
- `src/rewards/`
  Reward shaping and scoring
- `src/utils/`
  Plotting and structured logging
- `src/api/`
  FastAPI backend, async simulation runner, WebSocket streaming, results API

High-level entrypoints remain at the repo root for backward compatibility:

- `main.py`
- `compare_agents.py`
- `generate_paper_figures.py`
- `api/` compatibility package

The React dashboard lives in `dashboard/` and is served by FastAPI from `dashboard/dist` in production.

## Repository Layout

```text
.
├── api/                  # Compatibility wrappers for FastAPI package
├── config/               # YAML config and loader
├── dashboard/            # React + TypeScript + Vite frontend
├── docs/                 # Architecture, experiments, security docs
├── experiments/
│   ├── results/          # CSVs and JSONL event streams
│   ├── figures/          # Generated figures
│   ├── checkpoints/      # Saved agent checkpoints
│   ├── tables/           # Derived tables
│   └── *.py              # Experiment runners
├── infra/                # Docker and compose
├── src/                  # Main Python packages
├── tests/                # Automated tests
├── main.py               # CLI simulation wrapper
├── compare_agents.py     # Cross-agent comparison entrypoint
├── generate_paper_figures.py
└── start_dev.sh
```

## Quick Start

### Python environment

```bash
pip install -r requirements.txt
```

### Frontend environment

```bash
cd dashboard
npm install
cd ..
```

## CLI Usage

The original command-line flow is preserved.

Run a simulation:

```bash
python main.py --agent drl --attack cra --nodes 16 --episodes 50 --steps 30
```

Compare agent families:

```bash
python compare_agents.py
```

Generate paper figures:

```bash
python generate_paper_figures.py
```

Run experiment scripts:

```bash
python experiments/run_ablation.py
python experiments/run_scalability.py
python experiments/run_significance_tests.py
python experiments/run_malicious_sweep.py
python experiments/run_all_phase2.py
```

## Web Dashboard

### Development mode

Backend:

```bash
python -m uvicorn api.main:app --reload --port 8000
```

Frontend:

```bash
cd dashboard
npm run dev
```

Or start both together:

```bash
./start_dev.sh
```

### Production mode

Build the frontend:

```bash
cd dashboard
npm run build
cd ..
```

Start the backend:

```bash
python -m uvicorn api.main:app --port 8000
```

The backend will serve:

- `/health`
- `/docs`
- `/simulation/*`
- `/results/*`
- the built dashboard at `/`

## API Summary

### Health

- `GET /health`

### Simulation

- `POST /simulation/start`
- `GET /simulation/{run_id}/status`
- `POST /simulation/{run_id}/stop`
- `WS /simulation/{run_id}/stream`
- `WS /simulation/{run_id}/replay`

### Results

- `GET /results`
- `GET /results/{run_id}/metrics`
- `GET /results/{run_id}/download`
- `GET /results/compare`

## Event Stream

`SimulationManager` now emits structured callback events without breaking CLI execution:

- `step`
- `episode_end`
- `simulation_end`
- `error`

These are written to JSONL stream files in `experiments/results/` and can be replayed through the WebSocket API.

## Agents

- `rl`
  Q-learning style RL agent
- `drl`
  D3QN / DDQN-style deep RL agent
- `marl`
  Multi-agent RL setup

## Consensus Modes

- `tdcb`
  Trust-driven delegated consensus
- `pbft`
  PBFT baseline
- `static_dpos`
  Static delegated proof-of-stake style baseline
- `majority`
  Majority-vote baseline
- `random`
  Random delegation baseline

## Attack Families

- `none`
  No adversarial behavior
- `nma`
  Malicious node activity manipulation
- `cra`
  Collusion / coordinated rating attack behavior
- `aaa`
  ABAC-oriented adversarial access abuse
- `bfi`
  Blockchain flooding / invalidation pressure
- `tdp`
  Trust data poisoning

## Result Artifacts

- Episode metrics CSVs: `experiments/results/`
- Live/replay event streams: `experiments/results/*_stream.jsonl`
- Figures: `experiments/figures/`
- Checkpoints: `experiments/checkpoints/`
- Tables: `experiments/tables/`

## Documentation

- `docs/ARCHITECTURE.md`
- `docs/EXPERIMENT_GUIDE.md`
- `docs/SECURITY_MODEL.md`

## Docker

Build and run the production app:

```bash
docker compose -f infra/docker-compose.yml up --build app
```

Run the CLI simulation container:

```bash
docker compose -f infra/docker-compose.yml up --build simulation
```
