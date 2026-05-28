"""
Ablation study runner.

Variants:
  full_system   – all components active
  no_abac       – ABAC bypassed
  no_fhe        – no FHE (already default; compare overhead)
  no_trust_decay – trust decay disabled
  ucb_selection – UCB instead of Thompson sampling for delegation
  1d_action     – 1-D action space (legacy 3-action)

Usage:
    python -m analysis.run_ablation
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


BASE_CMD = [sys.executable, "main.py",
            "--agent", "marl", "--attack", "cra",
            "--nodes", "16", "--episodes", "100", "--steps", "30"]

SEEDS = [42, 123, 456]

VARIANTS: Dict[str, List[str]] = {
    "full_system":    [],
    "no_abac":        ["--no-abac"],
    "no_fhe":         [],                         # default (no --fhe)
    "no_trust_decay": ["--no-decay"],
    "ucb_selection":  ["--delegate-strategy", "ucb"],
    "1d_action":      ["--action-dims", "1"],
}

OUTPUT_DIR = "new_res"


def _result_csv(nodes: int, episodes: int, agent: str, attack: str,
                malicious: int, seed: int) -> Path:
    return Path("results") / f"{nodes}_{episodes}_{agent}_{attack}_{malicious}_seed{seed}_episode_metrics.csv"


def run_variant(variant: str, extra_args: List[str], seed: int) -> Optional[float]:
    """Run a single variant/seed combination and return final F1."""
    # Build a unique output identifier via seed
    cmd = BASE_CMD + extra_args + ["--seed", str(seed)]
    print(f"  [ablation] {variant} seed={seed}: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [WARN] variant {variant} seed {seed} failed:\n{result.stderr[-500:]}")
        return None
    # Find the CSV
    csv_path = _result_csv(16, 100, "marl", "cra", 30, seed)
    if not csv_path.exists():
        # Try without seed suffix (older format)
        csv_path = Path("results") / "16_100_marl_cra_30_episode_metrics.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        col = "F1 Score" if "F1 Score" in df.columns else df.columns[2]
        return float(df[col].iloc[-1])
    return None


def collect_results() -> pd.DataFrame:
    """Run all variants × seeds and collect final F1 scores."""
    rows = []
    for variant, extra in VARIANTS.items():
        f1s = []
        for seed in SEEDS:
            f1 = run_variant(variant, extra, seed)
            if f1 is not None:
                f1s.append(f1)
        rows.append({
            "variant": variant,
            "f1_mean": float(np.mean(f1s)) if f1s else float("nan"),
            "f1_std": float(np.std(f1s)) if len(f1s) > 1 else 0.0,
            "n_seeds": len(f1s),
        })
    return pd.DataFrame(rows)


def plot_ablation(df: pd.DataFrame, out_dir: str = OUTPUT_DIR) -> None:
    os.makedirs(out_dir, exist_ok=True)
    if df.empty or df["f1_mean"].isna().all():
        print("[ablation] No data to plot.")
        return

    fig, ax = plt.subplots(figsize=(9, 5))
    plt.rcParams.update({"font.family": "serif", "font.size": 11})

    y = df["f1_mean"].values
    yerr = df["f1_std"].values
    x = np.arange(len(df))
    colors = ["#2196F3", "#F44336", "#4CAF50", "#FF9800", "#9C27B0", "#00BCD4"]

    bars = ax.bar(x, y, yerr=yerr, color=colors[:len(df)], capsize=5,
                  error_kw={"elinewidth": 1.5})
    ax.set_xticks(x)
    ax.set_xticklabels(df["variant"].tolist(), rotation=20, ha="right")
    ax.set_ylabel("Final F1 Score", fontsize=12)
    ax.set_title("Ablation Study: Component Contribution (MARL, CRA Attack)", fontsize=13)
    ax.set_ylim(0, 1.05)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.grid(True, linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)

    for bar, val in zip(bars, y):
        if not np.isnan(val):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                    f"{val:.3f}", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    out_path = os.path.join(out_dir, "ablation_comparison.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[ablation] Saved: {out_path}")


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("\n=== Ablation Study ===\n")
    df = collect_results()
    print(df.to_string(index=False))
    df.to_csv(os.path.join(OUTPUT_DIR, "ablation_results.csv"), index=False)
    plot_ablation(df)
    print("\n[Done]")


# Allow Optional import in type hint above
from typing import Optional

if __name__ == "__main__":
    main()
