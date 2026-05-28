"""
Malicious fraction sweep across {0.10, 0.20, 0.30, 0.40, 0.45}.

Usage:
    python experiments/run_malicious_sweep.py
"""
from __future__ import annotations

import glob
import os
import subprocess
import sys
from typing import Dict, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

FRACTIONS = [0.10, 0.20, 0.30, 0.40, 0.45]
AGENTS = ["rl", "drl", "marl"]
OUTPUT_DIR = "experiments/tables"
RESULTS_CSV = "experiments/results/malicious_sweep_results.csv"
PBFT_LIMIT = 1.0 / 3.0  # theoretical PBFT Byzantine tolerance


def run_single(agent: str, malicious: float) -> Optional[float]:
    cmd = [
        sys.executable, "main.py",
        "--agent", agent, "--attack", "cra",
        "--nodes", "16", "--episodes", "100", "--steps", "30",
        "--malicious", str(malicious), "--seed", "42",
        "--log-level", "WARNING",
    ]
    pct = int(malicious * 100)
    print(f"  [sweep] agent={agent} malicious={pct}% ...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [WARN] Failed: {result.stderr[-300:]}")
        return None

    pattern = f"experiments/results/16_100_{agent}_cra_{pct}_*_episode_metrics.csv"
    matches = sorted(glob.glob(pattern))
    if not matches:
        pattern2 = f"experiments/results/16_100_{agent}_cra_{pct}_episode_metrics.csv"
        matches = sorted(glob.glob(pattern2))
    if matches:
        df = pd.read_csv(matches[-1])
        col = "F1 Score" if "F1 Score" in df.columns else df.columns[2]
        return float(df[col].tail(10).mean())
    return None


def collect_results() -> pd.DataFrame:
    rows = []
    for agent in AGENTS:
        for frac in FRACTIONS:
            f1 = run_single(agent, frac)
            rows.append({"agent": agent, "malicious_fraction": frac,
                         "f1_mean": f1 if f1 is not None else float("nan")})
    return pd.DataFrame(rows)


def plot_sweep(df: pd.DataFrame, out_dir: str = OUTPUT_DIR) -> None:
    os.makedirs(out_dir, exist_ok=True)
    if df.empty:
        return

    fig, ax = plt.subplots(figsize=(9, 6))
    plt.rcParams.update({"font.family": "serif", "font.size": 11})

    colors = {"rl": "#F44336", "drl": "#2196F3", "marl": "#4CAF50"}
    markers = {"rl": "s", "drl": "o", "marl": "^"}

    for agent in AGENTS:
        sub = df[df["agent"] == agent].sort_values("malicious_fraction")
        if sub["f1_mean"].notna().any():
            ax.plot(sub["malicious_fraction"].values, sub["f1_mean"].values,
                    marker=markers[agent], color=colors[agent], linewidth=2,
                    markersize=7, label=agent.upper())

    ax.axvline(x=PBFT_LIMIT, color="black", linestyle="--", linewidth=1.5,
               label=f"PBFT limit (n/3 ≈ {PBFT_LIMIT:.2f})")
    ax.set_xlabel("Malicious Node Fraction", fontsize=12)
    ax.set_ylabel("Mean F1 Score (last 10 episodes)", fontsize=12)
    ax.set_title("Robustness vs. Malicious Fraction\n(MARL/DRL/RL, CRA Attack, 16 Nodes)", fontsize=13)
    ax.set_xlim(0.05, 0.50)
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.grid(True, linestyle="--", alpha=0.3)

    plt.tight_layout()
    out_path = os.path.join(out_dir, "malicious_fraction_sweep.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[sweep] Saved: {out_path}")


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("\n=== Malicious Fraction Sweep ===\n")
    df = collect_results()
    print(df.to_string(index=False))
    os.makedirs("experiments/results", exist_ok=True)
    df.to_csv(RESULTS_CSV, index=False)
    print(f"\n[sweep] Data saved: {RESULTS_CSV}")
    plot_sweep(df)
    print("[Done]")


if __name__ == "__main__":
    main()
