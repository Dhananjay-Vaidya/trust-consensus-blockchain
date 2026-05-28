# plot_util.py
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix

def plot_cumulative_reward(episodes, rewards, agent_type, attack):
    plt.figure(figsize=(8, 6))
    plt.plot(episodes, rewards, marker='o', linestyle='-', color='b', label='Cumulative Reward')
    plt.xlabel('Episode')
    plt.ylabel('Cumulative Reward')
    plt.title(f'Cumulative Reward vs. Episodes ({agent_type.upper()})')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'images/cumulative_reward_vs_episodes_{agent_type}_{attack}.png')
    plt.show()

def plot_f1_score(episodes, f1_scores, agent_type, attack):
    plt.figure(figsize=(8, 6))
    plt.plot(episodes, f1_scores, marker='o', linestyle='-', color='g', label='F1-score')
    plt.xlabel('Episode')
    plt.ylabel('F1-score')
    plt.title(f'F1-score vs. Episodes ({agent_type.upper()})')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'images/f1_score_vs_episodes_{agent_type}_{attack}.png')
    plt.show()

def plot_blockchain_length(episodes, blockchain_lengths, agent_type, attack):
    plt.figure(figsize=(8, 6))
    plt.plot(episodes, blockchain_lengths, marker='o', linestyle='-', color='purple', label='Blockchain Length')
    plt.xlabel('Episode')
    plt.ylabel('Confirmed blocks')
    plt.title(f'Blockchain Growth Over Episodes ({agent_type.upper()})')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'images/blockchain_length_vs_episodes_{agent_type}_{attack}.png')
    plt.show()

def plot_throughput(episodes, throughputs, agent_type, attack):
    plt.figure(figsize=(8, 6))
    plt.plot(episodes, throughputs, marker='o', linestyle='-', color='orange', label='Last Block Tx Count')
    plt.xlabel('Episode')
    plt.ylabel('Transaction Throughput (tx count in last block)')
    plt.title(f'Transaction Throughput Over Episodes ({agent_type.upper()})')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'images/throughput_vs_episodes_{agent_type}_{attack}.png')
    plt.show()

def plot_confusion_matrix_from_labels(y_true, y_pred, agent_type, attack_mode, title="Confusion Matrix"):
    """
    Plots a 2x2 confusion matrix for the given true and predicted labels.
    
    Parameters:
      y_true (list or array): Actual labels (e.g., 1 for honest, 0 for malicious).
      y_pred (list or array): Predicted labels.
      agent_type (str): The agent type (e.g., 'RL', 'DRL', 'MARL') used for the title.
      attack_mode (str): The attack mode used.
      title (str): Title for the plot.
    """
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", 
                xticklabels=["Predicted Honest", "Predicted Malicious"],
                yticklabels=["Actual Honest", "Actual Malicious"])
    plt.title(f"{title} ({agent_type.upper()}, Attack: {attack_mode.upper()})")
    plt.ylabel("Actual")
    plt.xlabel("Predicted")
    plt.tight_layout()
    plt.savefig(f"images/confusion_matrix_{agent_type}_{attack_mode}.png")
    plt.show()