"""
Scalability experiment: vary --nodes ∈ {8, 16, 32, 64, 128}.

Usage:
    python experiments/run_scalability.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from typing import Dict, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False
    print("[scalability] psutil not installed; memory tracking disabled.")

NODE_COUNTS = [8, 16, 32, 64, 128]
OUTPUT_DIR = "experiments/tables"
RESULTS_CSV = "experiments/results/scalability_results.csv"


def run_single(nodes: int) -> Dict:
    """Run simulation for a given node count and return metrics."""
    cmd = [
        sys.executable, "main.py",
        "--agent", "marl", "--attack", "cra",
        "--nodes", str(nodes), "--episodes", "100", "--steps", "30",
        "--seed", "42", "--log-level", "WARNING",
    ]
    print(f"  [scalability] nodes={nodes} ...")

    proc = psutil.Popen(cmd) if _HAS_PSUTIL else subprocess.Popen(cmd)
    t_start = time.perf_counter()
    max_rss = 0.0

    if _HAS_PSUTIL:
        while proc.poll() is None:
            try:
                rss = proc.memory_info().rss / 1e6
                max_rss = max(max_rss, rss)
            except Exception:
                pass
            time.sleep(0.5)
        proc.wait()
    else:
        proc.wait()

    elapsed = time.perf_counter() - t_start

    # Load CSV
    import glob
    pattern = f"experiments/results/{nodes}_100_marl_cra_*_episode_metrics.csv"
    matches = sorted(glob.glob(pattern))
    f1_mean = float("nan")
    throughput_mean = float("nan")
    if matches:
        df = pd.read_csv(matches[-1])
        f1_col = "F1 Score" if "F1 Score" in df.columns else df.columns[2]
        tp_col = "Throughput" if "Throughput" in df.columns else None
        f1_mean = float(df[f1_col].tail(10).mean())
        if tp_col:
            throughput_mean = float(df[tp_col].tail(10).mean())

    return {
        "nodes": nodes,
        "f1_mean": f1_mean,
        "throughput_mean": throughput_mean,
        "time_per_episode_s": elapsed / 100,
        "memory_mb": max_rss,
    }


def plot_scalability(df: pd.DataFrame, out_dir: str = OUTPUT_DIR) -> None:
    os.makedirs(out_dir, exist_ok=True)
    if df.empty:
        return

    x = df["nodes"].values.astype(float)
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    plt.rcParams.update({"font.family": "serif", "font.size": 11})

    def _plot(ax, y_col, ylabel, title, ref_lines=False):
        y = df[y_col].values.astype(float)
        ax.plot(x, y, "o-", color="#2196F3", linewidth=2, markersize=6)
        if ref_lines:
            y_ref = y[0] * x / x[0]
            ax.plot(x, y_ref, "--", color="gray", alpha=0.5, label="O(n)")
            y_ref2 = y[0] * (x / x[0])**2
            ax.plot(x, y_ref2, ":", color="red", alpha=0.5, label="O(n²)")
            ax.legend(fontsize=9)
        ax.set_xlabel("Number of Nodes", fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.set_title(title, fontsize=12)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.yaxis.grid(True, linestyle="--", alpha=0.3)

    _plot(axes[0, 0], "f1_mean", "Mean F1 Score", "F1 Score vs Node Count")
    _plot(axes[0, 1], "throughput_mean", "Avg Throughput (tx/ep)", "Throughput vs Node Count")
    _plot(axes[1, 0], "time_per_episode_s", "Time/Episode (s)", "Latency vs Node Count", ref_lines=True)
    _plot(axes[1, 1], "memory_mb", "Memory (MB)", "Memory Usage vs Node Count")

    plt.tight_layout()
    out_path = os.path.join(out_dir, "scalability_analysis.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[scalability] Saved: {out_path}")


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("\n=== Scalability Experiment ===\n")

    rows = [run_single(n) for n in NODE_COUNTS]
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))

    os.makedirs("results", exist_ok=True)
    df.to_csv(RESULTS_CSV, index=False)
    print(f"\n[scalability] Data saved: {RESULTS_CSV}")

    plot_scalability(df)
    print("[Done]")


if __name__ == "__main__":
    main()
