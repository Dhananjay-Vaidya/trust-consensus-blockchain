from __future__ import annotations

import glob
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.simulation.simulation_manager import SimulationManager


AGENT_TYPES = ["rl", "drl", "marl"]
EPISODES = 50
ATTACK = "none"
RESULTS_DIR = Path("experiments/results")
FIGURES_DIR = Path("experiments/figures")


def _latest_metrics_csv(agent: str) -> Path | None:
    pattern = str(RESULTS_DIR / f"**/*_{agent}_{ATTACK}_*_episode_metrics.csv")
    matches = sorted(glob.glob(pattern, recursive=True))
    return Path(matches[-1]) if matches else None


def _load_metrics(agent: str) -> pd.DataFrame | None:
    csv_path = _latest_metrics_csv(agent)
    if csv_path is None or not csv_path.exists():
        return None
    return pd.read_csv(csv_path)


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, pd.DataFrame] = {}

    for agent in AGENT_TYPES:
        print(f"\n=== Running simulation for agent: {agent.upper()} ===")
        sim = SimulationManager(episodes=EPISODES, agent_type=agent, attack_mode=ATTACK)
        sim.run_simulation()
        df = _load_metrics(agent)
        if df is not None:
            results[agent] = df

    plots = [
        ("Cumulative Reward", "comparative_cumulative_reward.png", "Comparative Cumulative Reward vs. Episodes"),
        ("F1 Score", "comparative_f1_score.png", "Comparative F1-Score vs. Episodes"),
        ("Blockchain Length", "comparative_blockchain_length.png", "Comparative Blockchain Growth vs. Episodes"),
        ("Throughput", "comparative_throughput.png", "Comparative Throughput vs. Episodes"),
    ]

    for column, filename, title in plots:
        plt.figure(figsize=(10, 6))
        for agent, df in results.items():
            if column in df.columns:
                plt.plot(df["Episode"], df[column], marker="o", label=agent.upper())
        plt.xlabel("Episode")
        plt.ylabel(column)
        plt.title(title)
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / filename)
        plt.close()

    print("\n=== Summary of Comparative Results ===")
    for agent, df in results.items():
        print(
            f"{agent.upper()}: "
            f"Final Reward={df['Cumulative Reward'].iloc[-1]:.2f}, "
            f"F1={df['F1 Score'].iloc[-1]:.4f}, "
            f"Chain={int(df['Blockchain Length'].iloc[-1])}, "
            f"Throughput={float(df['Throughput'].iloc[-1]):.2f}"
        )


if __name__ == "__main__":
    main()
