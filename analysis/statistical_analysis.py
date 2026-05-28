"""
Statistical analysis for multi-seed simulation results.
Computes confidence intervals, significance tests, and effect sizes.

Usage:
    python -m analysis.statistical_analysis --results-dir results/ --output-dir new_res/
"""
from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats


# ------------------------------------------------------------------ #
#  Data loading                                                        #
# ------------------------------------------------------------------ #

def load_multi_seed_results(
    results_dir: str,
    agent: str,
    attack: str,
    nodes: int,
    episodes: int,
) -> pd.DataFrame:
    """Load all CSV files for a given (agent, attack, nodes, episodes) across seeds."""
    path = Path(results_dir)
    pattern = re.compile(
        rf"^{nodes}_{episodes}_{agent}_{attack}_\d+(?:_seed(\d+))?_episode_metrics\.csv$",
        re.IGNORECASE,
    )
    frames: List[pd.DataFrame] = []
    for f in path.glob("*_episode_metrics.csv"):
        m = pattern.match(f.name)
        if m:
            df = pd.read_csv(f)
            seed_val = int(m.group(1)) if m.group(1) else 0
            df["seed"] = seed_val
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _bootstrap_ci(data: np.ndarray, n_boot: int = 1000, ci: float = 0.95) -> Tuple[float, float]:
    """Bootstrap confidence interval for the mean."""
    if len(data) < 2:
        v = float(data[0]) if len(data) == 1 else float("nan")
        return v, v
    boot_means = np.array([
        np.mean(np.random.choice(data, size=len(data), replace=True))
        for _ in range(n_boot)
    ])
    lo = float(np.percentile(boot_means, (1 - ci) / 2 * 100))
    hi = float(np.percentile(boot_means, (1 + ci) / 2 * 100))
    return lo, hi


# ------------------------------------------------------------------ #
#  Statistical functions                                               #
# ------------------------------------------------------------------ #

def compute_final_episode_stats(
    df: pd.DataFrame,
    metric: str = "F1 Score",
) -> Dict:
    """
    From the last episode of each seed run, compute mean/std/CI95.
    """
    if df.empty:
        return {"mean": float("nan"), "std": float("nan"),
                "ci_low": float("nan"), "ci_high": float("nan"), "n_seeds": 0}
    # Normalise column name variants
    col = _find_col(df, metric)
    if col is None:
        return {"mean": float("nan"), "std": float("nan"),
                "ci_low": float("nan"), "ci_high": float("nan"), "n_seeds": 0}

    last_vals = df.groupby("seed")[col].last().values.astype(float)
    ci_lo, ci_hi = _bootstrap_ci(last_vals)
    return {
        "mean": float(np.mean(last_vals)),
        "std": float(np.std(last_vals, ddof=1)) if len(last_vals) > 1 else 0.0,
        "ci_low": ci_lo,
        "ci_high": ci_hi,
        "n_seeds": len(last_vals),
    }


def compare_agents_significance(
    results_dir: str,
    attack: str,
    metric: str = "F1 Score",
    nodes: int = 16,
    episodes: int = 50,
) -> pd.DataFrame:
    """
    Pairwise Mann-Whitney U tests across agents for a given attack.
    Returns DataFrame: agent_a, agent_b, u_stat, p_value, significant, effect_size.
    """
    agents = ["rl", "drl", "marl"]
    agent_data: Dict[str, np.ndarray] = {}
    for ag in agents:
        df = load_multi_seed_results(results_dir, ag, attack, nodes, episodes)
        if df.empty:
            continue
        col = _find_col(df, metric)
        if col is None:
            continue
        agent_data[ag] = df.groupby("seed")[col].last().values.astype(float)

    rows = []
    agent_list = list(agent_data.keys())
    for i in range(len(agent_list)):
        for j in range(i + 1, len(agent_list)):
            a, b = agent_list[i], agent_list[j]
            da, db = agent_data[a], agent_data[b]
            if len(da) < 2 or len(db) < 2:
                continue
            u, p = stats.mannwhitneyu(da, db, alternative="two-sided")
            n1, n2 = len(da), len(db)
            effect_size = 1.0 - (2 * u) / (n1 * n2)  # rank-biserial correlation
            rows.append({
                "agent_a": a, "agent_b": b,
                "u_stat": float(u), "p_value": float(p),
                "significant": bool(p < 0.05),
                "effect_size": float(effect_size),
            })
    return pd.DataFrame(rows)


def compute_convergence_episode(
    df: pd.DataFrame,
    metric: str = "F1 Score",
    threshold: float = 0.8,
    sustain: int = 5,
) -> float:
    """
    Average episode at which the metric first consistently exceeds threshold,
    sustained for `sustain` subsequent episodes.  Returns NaN if never achieved.
    """
    if df.empty:
        return float("nan")
    col = _find_col(df, metric)
    if col is None:
        return float("nan")

    convergence_episodes: List[float] = []
    for seed, grp in df.groupby("seed"):
        vals = grp.sort_values("Episode")[col].values if "Episode" in grp.columns \
            else grp[col].values
        found = float("nan")
        for i in range(len(vals) - sustain):
            if vals[i] >= threshold and all(vals[i:i + sustain + 1] >= threshold):
                found = float(i + 1)
                break
        convergence_episodes.append(found)
    valid = [e for e in convergence_episodes if not np.isnan(e)]
    return float(np.mean(valid)) if valid else float("nan")


def generate_results_table(
    results_dir: str,
    output_path: str = "new_res/statistical_table.csv",
    nodes: int = 16,
    episodes: int = 50,
) -> pd.DataFrame:
    """Full summary table for all (agent × attack) combinations."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    attacks = ["nma", "cra", "aaa", "bfi", "tdp"]
    agents = ["rl", "drl", "marl"]

    # Load PBFT baseline for comparison
    pbft_data: Dict[str, np.ndarray] = {}
    for atk in attacks:
        df_pbft = load_multi_seed_results(results_dir, "drl", atk, nodes, episodes)
        # Filter for PBFT runs if 'CONSENSUS' column exists, else just use all
        if not df_pbft.empty:
            col = _find_col(df_pbft, "F1 Score")
            if col:
                pbft_data[atk] = df_pbft.groupby("seed")[col].last().values.astype(float)

    rows = []
    for ag in agents:
        for atk in attacks:
            df = load_multi_seed_results(results_dir, ag, atk, nodes, episodes)
            stats_f1 = compute_final_episode_stats(df, "F1 Score")
            stats_prec = compute_final_episode_stats(df, "Cumulative Reward")
            conv = compute_convergence_episode(df)

            # Compare vs PBFT
            p_vs_pbft = float("nan")
            sig_vs_pbft = False
            pbft_arr = pbft_data.get(atk)
            if not df.empty and pbft_arr is not None and len(pbft_arr) >= 2:
                col = _find_col(df, "F1 Score")
                if col:
                    agent_arr = df.groupby("seed")[col].last().values.astype(float)
                    if len(agent_arr) >= 2:
                        _, p_vs_pbft = stats.mannwhitneyu(
                            agent_arr, pbft_arr, alternative="two-sided")
                        sig_vs_pbft = bool(p_vs_pbft < 0.05)

            rows.append({
                "agent": ag,
                "attack": atk,
                "f1_mean": stats_f1["mean"],
                "f1_std": stats_f1["std"],
                "f1_ci95": f"[{stats_f1['ci_low']:.3f}, {stats_f1['ci_high']:.3f}]",
                "precision_mean": float("nan"),
                "recall_mean": float("nan"),
                "convergence_episode": conv,
                "p_vs_pbft": p_vs_pbft,
                "significant_vs_pbft": sig_vs_pbft,
            })

    result_df = pd.DataFrame(rows)
    result_df.to_csv(output_path, index=False)

    # LaTeX table
    tex_path = output_path.replace(".csv", ".tex")
    _write_latex_table(result_df, tex_path)
    print(f"[StatAnalysis] Saved: {output_path} and {tex_path}")
    return result_df


def _write_latex_table(df: pd.DataFrame, path: str) -> None:
    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Simulation Results Summary}",
        r"\label{tab:results}",
        r"\begin{tabular}{llcccccc}",
        r"\toprule",
        r"Agent & Attack & F1 Mean$\pm$Std & CI 95\% & Conv. Ep. & $p$ vs PBFT \\",
        r"\midrule",
    ]
    for _, row in df.iterrows():
        f1_str = f"{row['f1_mean']:.3f}$\\pm${row['f1_std']:.3f}"
        if not np.isnan(row['f1_mean']):
            f1_str = r"\textbf{" + f1_str + "}" if row.get("significant_vs_pbft") else f1_str
        p_str = f"{row['p_vs_pbft']:.3f}$\\dagger$" if row.get("significant_vs_pbft") \
            else (f"{row['p_vs_pbft']:.3f}" if not np.isnan(row['p_vs_pbft']) else "N/A")
        conv_str = f"{row['convergence_episode']:.1f}" if not np.isnan(row['convergence_episode']) else "N/A"
        lines.append(
            f"{row['agent'].upper()} & {row['attack'].upper()} & {f1_str} & "
            f"{row['f1_ci95']} & {conv_str} & {p_str} \\\\"
        )
    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\begin{tablenotes}\footnotesize",
        r"\item[$\dagger$] $p < 0.05$ vs PBFT baseline (Mann-Whitney U test)",
        r"\end{tablenotes}",
        r"\end{table}",
    ]
    with open(path, "w") as f:
        f.write("\n".join(lines))


def _find_col(df: pd.DataFrame, name: str) -> Optional[str]:
    """Case-insensitive column lookup with common aliases."""
    aliases = {
        "f1 score": ["F1 Score", "f1_score", "F1"],
        "cumulative reward": ["Cumulative Reward", "cumulative_reward"],
        "precision": ["precision", "Precision"],
        "recall": ["recall", "Recall"],
    }
    search = name.lower()
    candidates = aliases.get(search, [name])
    for c in candidates:
        if c in df.columns:
            return c
    # Fuzzy match
    for col in df.columns:
        if search in col.lower():
            return col
    return None


# ------------------------------------------------------------------ #
#  Main entry point                                                    #
# ------------------------------------------------------------------ #

def main() -> None:
    parser = argparse.ArgumentParser(description="Statistical analysis of simulation results")
    parser.add_argument("--results-dir", default="results/")
    parser.add_argument("--output-dir", default="new_res/")
    parser.add_argument("--nodes", type=int, default=16)
    parser.add_argument("--episodes", type=int, default=50)
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print("STATISTICAL ANALYSIS REPORT")
    print(f"Results dir: {args.results_dir}")
    print(f"{'='*60}\n")

    table = generate_results_table(
        args.results_dir,
        output_path=os.path.join(args.output_dir, "statistical_table.csv"),
        nodes=args.nodes,
        episodes=args.episodes,
    )

    if not table.empty:
        print(table.to_string(index=False))
    else:
        print("No results found.  Run experiments first.")

    print("\nPairwise agent comparisons (CRA attack):")
    sig_df = compare_agents_significance(
        args.results_dir, "cra",
        nodes=args.nodes, episodes=args.episodes)
    if not sig_df.empty:
        print(sig_df.to_string(index=False))
    else:
        print("Insufficient data for significance tests.")

    print(f"\n[Done] Outputs saved to {args.output_dir}")


if __name__ == "__main__":
    main()
