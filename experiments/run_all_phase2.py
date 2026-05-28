"""
Scenario runner: executes all three real-world scenario YAMLs and
generates a comparative figure.

Usage:
    python experiments/run_all_phase2.py
"""
from __future__ import annotations

import glob
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

OUTPUT_DIR = "experiments/tables"
SCENARIOS = [
    ("experiments/scenarios/smart_grid.yaml",      "Smart Grid",      "cra"),
    ("experiments/scenarios/healthcare_iot.yaml",  "Healthcare IoT",  "tdp"),
    ("experiments/scenarios/industrial_iot.yaml",  "Industrial IoT",  "bfi"),
]


def run_scenario(yaml_path: str, attack_override: str) -> Optional[str]:
    """
    Run the simulation for a scenario and return the path to the result CSV.
    """
    with open(yaml_path) as f:
        raw = yaml.safe_load(f)

    net = raw.get("network", {})
    tr = raw.get("training", {})
    nodes = net.get("num_nodes", 16)
    malicious = net.get("malicious_fraction", 0.3)
    episodes = tr.get("episodes", 100)
    steps = tr.get("steps_per_episode", 50)

    cmd = [
        sys.executable, "main.py",
        "--agent", "marl",
        "--attack", attack_override,
        "--scenario", yaml_path,
        "--nodes", str(nodes),
        "--episodes", str(episodes),
        "--steps", str(steps),
        "--malicious", str(malicious),
        "--seed", "42",
        "--log-level", "WARNING",
    ]
    print(f"  [scenario] {Path(yaml_path).stem}: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [WARN] Scenario {yaml_path} failed:\n{result.stderr[-400:]}")
        return None

    pct = int(malicious * 100)
    pattern = f"experiments/results/{nodes}_{episodes}_marl_{attack_override}_{pct}_*_episode_metrics.csv"
    matches = sorted(glob.glob(pattern))
    if matches:
        return matches[-1]
    # Fallback
    pattern2 = f"experiments/results/{nodes}_{episodes}_marl_{attack_override}_{pct}_episode_metrics.csv"
    matches2 = sorted(glob.glob(pattern2))
    return matches2[-1] if matches2 else None


def plot_scenarios(scenario_data: Dict[str, pd.DataFrame], out_dir: str = OUTPUT_DIR) -> None:
    os.makedirs(out_dir, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    plt.rcParams.update({"font.family": "serif", "font.size": 11})

    colors = ["#2196F3", "#4CAF50", "#F44336"]
    markers = ["o", "s", "^"]

    for (name, color, marker), (label, df) in zip(
        zip([s[1] for s in SCENARIOS], colors, markers),
        scenario_data.items()
    ):
        if df.empty:
            continue
        col = "F1 Score" if "F1 Score" in df.columns else df.columns[2]
        ep_col = "Episode" if "Episode" in df.columns else df.columns[0]
        ax.plot(df[ep_col].values, df[col].values,
                color=color, marker=marker, markevery=10,
                linewidth=2, markersize=6, label=label)

    ax.set_xlabel("Episode", fontsize=12)
    ax.set_ylabel("F1 Score", fontsize=12)
    ax.set_title("F1 Score over Episodes: Real-World Scenario Comparison\n(MARL agent, seed=42)",
                 fontsize=13)
    ax.legend(fontsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.grid(True, linestyle="--", alpha=0.3)
    ax.set_ylim(0, 1.05)

    plt.tight_layout()
    out_path = os.path.join(out_dir, "scenario_comparison.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[scenarios] Saved: {out_path}")


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("\n=== Real-World Scenario Comparison ===\n")

    scenario_data: Dict[str, pd.DataFrame] = {}
    summary_rows = []

    for yaml_path, label, attack in SCENARIOS:
        csv_path = run_scenario(yaml_path, attack)
        if csv_path and Path(csv_path).exists():
            df = pd.read_csv(csv_path)
            scenario_data[label] = df
            f1_col = "F1 Score" if "F1 Score" in df.columns else df.columns[2]
            final_f1 = float(df[f1_col].iloc[-1])
            # Convergence: first episode above 0.8 sustained 5 steps
            vals = df[f1_col].values
            conv = float("nan")
            for i in range(len(vals) - 5):
                if vals[i] >= 0.8 and all(vals[i:i+6] >= 0.8):
                    conv = float(i + 1)
                    break
            summary_rows.append({
                "Scenario": label,
                "Attack": attack.upper(),
                "Final F1": f"{final_f1:.4f}",
                "Convergence Episode": f"{conv:.1f}" if not np.isnan(conv) else "N/A",
            })
        else:
            scenario_data[label] = pd.DataFrame()
            summary_rows.append({
                "Scenario": label, "Attack": attack.upper(),
                "Final F1": "N/A", "Convergence Episode": "N/A",
            })

    # Print summary
    print("\n--- Summary Table ---")
    summary_df = pd.DataFrame(summary_rows)
    print(summary_df.to_string(index=False))
    summary_df.to_csv(os.path.join(OUTPUT_DIR, "scenario_summary.csv"), index=False)

    plot_scenarios(scenario_data)
    print("\n[Done]")


if __name__ == "__main__":
    main()
