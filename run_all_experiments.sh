#!/bin/bash
set -euo pipefail

SEEDS="42 123 456 789 1024"
AGENTS="rl drl marl"
ATTACKS="nma cra aaa bfi tdp"
NODES=16
EPISODES=100
STEPS=30

mkdir -p experiments/results

# ---- Main RL agent experiments ----
for seed in $SEEDS; do
  for agent in $AGENTS; do
    for attack in $ATTACKS; do
      OUT="experiments/results/${NODES}_${EPISODES}_${agent}_${attack}_30_seed${seed}_episode_metrics.csv"
      if [ -f "$OUT" ]; then
        echo "[SKIP] $OUT already exists"
        continue
      fi
      echo "[RUN] agent=$agent attack=$attack seed=$seed"
      python main.py \
        --agent "$agent" \
        --attack "$attack" \
        --nodes "$NODES" \
        --episodes "$EPISODES" \
        --steps "$STEPS" \
        --seed "$seed"
    done
  done
done

# ---- Baseline consensus experiments (seed=42 only) ----
for consensus in pbft static_dpos majority random; do
  for attack in $ATTACKS; do
    OUT="experiments/results/${NODES}_${EPISODES}_drl_${attack}_30_consensus_${consensus}_episode_metrics.csv"
    if [ -f "$OUT" ]; then
      echo "[SKIP] $OUT already exists"
      continue
    fi
    echo "[RUN] consensus=$consensus attack=$attack seed=42"
    python main.py \
      --agent drl \
      --attack "$attack" \
      --consensus "$consensus" \
      --nodes "$NODES" \
      --episodes "$EPISODES" \
      --steps "$STEPS" \
      --seed 42
  done
done

echo "[DONE] All experiments completed."
