# Experiment Guide

## Core Runs

- Single run:
  - `python main.py --agent drl --attack cra --nodes 16 --episodes 50 --steps 30`
- Agent comparison:
  - `python compare_agents.py`
- Figure generation:
  - `python generate_paper_figures.py`

## Batch Experiment Scripts

- Ablation:
  - `python experiments/run_ablation.py`
- Scalability:
  - `python experiments/run_scalability.py`
- Statistical significance:
  - `python experiments/run_significance_tests.py`
- Scenario comparison:
  - `python experiments/run_all_phase2.py`
- Malicious-fraction sweep:
  - `python experiments/run_malicious_sweep.py`

## Output Locations

- raw metrics: `experiments/results/`
- figures: `experiments/figures/`
- tables: `experiments/tables/`
- checkpoints: `experiments/checkpoints/`
