from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import parameters as params
from simulation_manager import SimulationManager
from plot_util import plot_cumulative_reward, plot_f1_score, plot_blockchain_length, plot_throughput

agent_types = ["rl", "drl", "marl"]
num_episodes = 50
results: dict = {}

for agent in agent_types:
    print(f"\n=== Running simulation for agent: {agent.upper()} ===")
    sim = SimulationManager(episodes=num_episodes, agent_type=agent)
    sim.run_simulation()

    results[agent] = {
        "episodes": list(range(1, num_episodes + 1)),
        "cumulative_rewards": [],
        "f1_scores": [],
        "blockchain_lengths": [],
        "throughputs": [],
    }

# --- Comparative Plots ---

plt.figure(figsize=(10, 6))
for agent in agent_types:
    if results[agent]["cumulative_rewards"]:
        plt.plot(results[agent]["episodes"], results[agent]["cumulative_rewards"],
                 marker="o", label=agent.upper())
plt.xlabel("Episode")
plt.ylabel("Cumulative Reward")
plt.title("Comparative Cumulative Reward vs. Episodes")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("comparative_cumulative_reward.png")
plt.show()

plt.figure(figsize=(10, 6))
for agent in agent_types:
    if results[agent]["f1_scores"]:
        plt.plot(results[agent]["episodes"], results[agent]["f1_scores"],
                 marker="o", label=agent.upper())
plt.xlabel("Episode")
plt.ylabel("F1-Score")
plt.title("Comparative F1-Score vs. Episodes")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("comparative_f1_score.png")
plt.show()

plt.figure(figsize=(10, 6))
for agent in agent_types:
    if results[agent]["blockchain_lengths"]:
        plt.plot(results[agent]["episodes"], results[agent]["blockchain_lengths"],
                 marker="o", label=agent.upper())
plt.xlabel("Episode")
plt.ylabel("Confirmed blocks")
plt.title("Comparative Blockchain Growth vs. Episodes")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("comparative_blockchain_length.png")
plt.show()

plt.figure(figsize=(10, 6))
for agent in agent_types:
    if results[agent]["throughputs"]:
        plt.plot(results[agent]["episodes"], results[agent]["throughputs"],
                 marker="o", label=agent.upper())
plt.xlabel("Episode")
plt.ylabel("Transaction Throughput (tx count in last block)")
plt.title("Comparative Throughput vs. Episodes")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("comparative_throughput.png")
plt.show()

print("\n=== Summary of Comparative Results ===")
for agent in agent_types:
    r = results[agent]
    if r["cumulative_rewards"]:
        print(
            f"{agent.upper()}: "
            f"Final Reward={r['cumulative_rewards'][-1]:.2f}, "
            f"F1={r['f1_scores'][-1]:.4f}, "
            f"Chain={r['blockchain_lengths'][-1]}, "
            f"Throughput={r['throughputs'][-1]}"
        )
