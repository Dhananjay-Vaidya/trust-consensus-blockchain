from __future__ import annotations

import itertools
import os
import random
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn.functional as F
from sklearn.metrics import classification_report
from tqdm import tqdm
import pandas as pd

import parameters as params
from abac import ABAC
from fhe import FullyHomomorphicEncryption
from trust import TrustManager
from reward import RewardSystem
from tdcb import TDCB
from drl_d3p import DDQN
from marl_agent import MARLAgent
from plot_util import (plot_cumulative_reward, plot_f1_score,
                       plot_blockchain_length, plot_throughput,
                       plot_confusion_matrix_from_labels)
from attack_util import apply_attack, reset_attack_instances
from utils.logger import get_logger, JSONFileHandler

logger = get_logger(__name__)


def detect_collusion(trust_manager: TrustManager, malicious_nodes: set) -> float:
    all_nodes = list(trust_manager.trust_scores.keys())
    honest_nodes = [n for n in all_nodes if n not in malicious_nodes]
    if not honest_nodes or not malicious_nodes:
        return 0.0
    malicious_trust_vals = [trust_manager.get_trust(n) for n in malicious_nodes]
    honest_trust_vals = [trust_manager.get_trust(n) for n in honest_nodes]
    avg_mal = sum(malicious_trust_vals) / len(malicious_trust_vals)
    avg_hon = sum(honest_trust_vals) / len(honest_trust_vals)
    gap = abs(avg_hon - avg_mal)
    if gap < 1e-6:
        return 9999.0
    return 1.0 / gap


class BatchProcessor:
    def __init__(self, batch_size: int = params.BATCH_SIZE) -> None:
        self.batch_size = batch_size
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def process_transactions(self, transactions: List[Dict]) -> List[List[Dict]]:
        return [transactions[i:i + self.batch_size]
                for i in range(0, len(transactions), self.batch_size)]

    def process_batch(self, batch: List[Dict]) -> torch.Tensor:
        sender_map = {s: i for i, s in enumerate(set(tx["sender"] for tx in batch))}
        recipient_map = {r: i for i, r in enumerate(set(tx["recipient"] for tx in batch))}
        return torch.tensor(
            [[sender_map[tx["sender"]], recipient_map[tx["recipient"]], tx["amount"]]
             for tx in batch],
            dtype=torch.float32, device=self.device)


def _build_consensus(consensus_type: str) -> Any:
    """Instantiate the requested consensus object."""
    if consensus_type == "pbft":
        from baselines.pbft_baseline import PBFTConsensus
        return PBFTConsensus()
    elif consensus_type == "static_dpos":
        from baselines.static_dpos_baseline import StaticDPoSConsensus
        return StaticDPoSConsensus()
    elif consensus_type == "majority":
        from baselines.majority_vote_baseline import MajorityVoteConsensus
        return MajorityVoteConsensus()
    elif consensus_type == "random":
        from baselines.random_delegation_baseline import RandomDelegation
        return RandomDelegation()
    else:
        return TDCB()


class SimulationManager:
    def __init__(
        self,
        episodes: int = params.EPISODES,
        agent_type: str = "drl",
        attack_mode: str = "none",
        config: Optional[Any] = None,
        seed: int = 42,
        consensus_type: str = "tdcb",
        step_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.episodes = episodes
        self.agent_type = agent_type
        self.attack_mode = attack_mode
        self.config = config
        self.seed = seed
        self.consensus_type = consensus_type
        self.step_callback = step_callback
        self.batch_processor = BatchProcessor()

        # Ablation flags from params (set by main.py CLI parsing)
        self._no_abac = getattr(params, "NO_ABAC", False)
        self._no_decay = getattr(params, "NO_DECAY", False)
        self._delegate_strategy = getattr(params, "DELEGATE_STRATEGY", "thompson")
        self._action_dims = getattr(params, "ACTION_DIMS", 3)

        reset_attack_instances()
        self._init_components(agent_type)
        self._init_nodes()

        self.reward_history: List[float] = []
        self.decline_counter = 0
        self.strategy_changes = 0
        self.current_strategy = 0
        self.chain_length_5_episodes_ago = 0
        self.episode_counter = 0
        self.best_model_f1 = 0.0
        self.attack_rounds = 0

        self.checkpoint_dir = "checkpoints"
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        os.makedirs("results", exist_ok=True)
        os.makedirs("images", exist_ok=True)

        self.total_byzantine_detected = 0
        self.total_consensus_rounds = 0
        self.abac_total_requests = 0
        self.abac_denied_requests = 0

        self.previous_trust_values = {node: 0.5 for node in self.nodes}
        self.last_state = self._compute_initial_state()

        self._fhe_enabled = getattr(params, "FHE_ENABLED", False)
        self._run_id = (
            f"{params.TOTAL_NODES}_{self.episodes}_{agent_type}_{attack_mode}"
            f"_{int(params.MALICIOUS_RATIO*100)}_seed{seed}"
        )
        self._json_handler: Optional[JSONFileHandler] = None

        logger.info(f"Simulation initialised on {self.device}")
        logger.info(f"Agent: {agent_type.upper()}, Attack: {attack_mode.upper()}, "
                    f"Consensus: {consensus_type.upper()}")
        logger.info(f"Nodes: {params.TOTAL_NODES}, Malicious Ratio: {params.MALICIOUS_RATIO}")
        logger.info(f"FHE: {self._fhe_enabled} | no_abac: {self._no_abac} | "
                    f"no_decay: {self._no_decay} | delegate: {self._delegate_strategy} | "
                    f"action_dims: {self._action_dims}")

    # ------------------------------------------------------------------ #
    #  Initialisation helpers                                              #
    # ------------------------------------------------------------------ #

    def _get_cfg(self, key: str, default: Any) -> Any:
        if self.config is not None and hasattr(self.config, key.lower()):
            return getattr(self.config, key.lower())
        return getattr(params, key, default)

    def _compute_initial_state(self) -> np.ndarray:
        return np.array([
            0.5, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0,
            len(self.blockchain.chain) / params.CHAIN_NORM,
            (1.0 - params.MALICIOUS_RATIO) / params.MALICIOUS_RATIO,
            0.0, 1.0, 0.5, 0.0, 0.0, 0.0
        ])

    def _init_components(self, agent_type: str = "drl") -> None:
        self.abac = ABAC()
        self.fhe = FullyHomomorphicEncryption()
        self.reward_system = RewardSystem()
        self.consensus = _build_consensus(self.consensus_type)
        # Keep self.tdcb as alias for compatibility
        self.tdcb = self.consensus
        self.blockchain = self._init_blockchain()

        state_dim = 16
        # 1-D action space reverts to 3 actions; 3-D uses 27
        if self._action_dims == 1:
            action_dim = 3
            params.ACTION_SPACE_SIZE = 3
            params.ACTION_MAP = {0: (0.9, 1.0, 0.0), 1: (1.0, 1.0, 0.0), 2: (1.1, 1.0, 0.0)}
        else:
            action_dim = params.ACTION_SPACE_SIZE  # 27
            params.ACTION_MAP = {
                i: combo
                for i, combo in enumerate(
                    itertools.product([0.9, 1.0, 1.1], [0.95, 1.0, 1.05], [-0.05, 0.0, 0.05])
                )
            }

        if agent_type == "rl":
            from rl_agent import RLAgent
            self.agent = RLAgent(state_dim=state_dim, action_dim=action_dim)
        elif agent_type == "marl":
            self.agent = MARLAgent(
                state_dim=state_dim, action_dim=action_dim,
                num_agents=params.TOTAL_NODES, lr=5e-4, gamma=0.99)
        else:
            self.agent = DDQN(state_dim=state_dim, action_dim=action_dim)

        # RandomDelegation needs the full node pool — set after _init_nodes
        self._consensus_needs_node_pool = self.consensus_type == "random"

    def _init_blockchain(self) -> Any:
        bc = __import__("blockchain", fromlist=["Blockchain"]).Blockchain(difficulty=4)
        bc.delegation_ratio = 0.5
        return bc

    def _init_nodes(self) -> None:
        self.nodes = [f"Node_{i}" for i in range(params.TOTAL_NODES)]
        num_malicious = int(params.TOTAL_NODES * params.MALICIOUS_RATIO)
        self.true_malicious_nodes = set(random.sample(self.nodes, num_malicious))
        self.true_honest_nodes = set(self.nodes) - self.true_malicious_nodes

        for node in self.nodes:
            attrs = {"user_role"} if node in self.true_malicious_nodes \
                else {"admin_role", "security_clearance"}
            self.abac.add_user_attributes(node, attrs)

        self.trust_manager = TrustManager(self.nodes)

        # Provide node pool to random delegation baseline
        if self._consensus_needs_node_pool:
            self.consensus.set_node_pool(self.nodes)

        logger.info(f"Malicious ({len(self.true_malicious_nodes)}): "
                    f"{sorted(self.true_malicious_nodes)}")
        logger.info(f"Honest ({len(self.true_honest_nodes)}): "
                    f"{sorted(self.true_honest_nodes)}")

    # ------------------------------------------------------------------ #
    #  Per-step helpers                                                    #
    # ------------------------------------------------------------------ #

    def _generate_transactions(self, n: int) -> List[Dict]:
        senders = random.choices(self.nodes, k=n)
        recipients = random.choices(self.nodes, k=n)
        amounts = torch.rand(n, device=self.device) * 100
        return [{"sender": s, "recipient": r, "amount": a.item()}
                for s, r, a in zip(senders, recipients, amounts)]

    def _compute_state(self, trust_values: Dict[str, float],
                       consensus_result: Dict, num_tx: int, step_i: int) -> np.ndarray:
        tl = list(trust_values.values())
        avg_t = float(np.mean(tl))
        var_t = float(np.var(tl))
        std_t = float(np.std(tl))
        med_t = float(np.median(tl))
        skew_t = 0.0
        if len(tl) > 2 and std_t > 0:
            skew_t = float(np.mean([(t - avg_t)**3 for t in tl]) / (std_t**3))
        cv = std_t / avg_t if avg_t > 0 else 0.0
        rng = max(tl) - min(tl)
        iqr = float(np.percentile(tl, 75) - np.percentile(tl, 25))
        c_norm = consensus_result["verified_transactions"] / params.CONSENSUS_NORM
        ch_norm = len(self.blockchain.chain) / params.CHAIN_NORM
        hm_ratio = (1.0 - params.MALICIOUS_RATIO) / params.MALICIOUS_RATIO
        low_t = sum(1 for t in tl if t < 0.3) / params.TOTAL_NODES
        high_t = sum(1 for t in tl if t > 0.7) / params.TOTAL_NODES
        num_del = max(1, int(len(self.nodes) * self.blockchain.delegation_ratio))
        del_eff = num_del / params.TOTAL_NODES
        blk5 = (len(self.blockchain.chain) - self.chain_length_5_episodes_ago) / 10
        tp = (num_tx / (step_i + 1) if step_i > 0 else num_tx) / 50
        col = min(detect_collusion(self.trust_manager, self.true_malicious_nodes) / 10, 10.0)
        return np.array([avg_t, var_t, skew_t, med_t, rng, iqr, cv, c_norm,
                         ch_norm, hm_ratio, low_t, high_t, del_eff, tp, blk5, col])

    def _filter_transactions(self, transactions: List[Dict]) -> List[Dict]:
        """Apply ABAC (or bypass if --no-abac)."""
        if self._no_abac:
            # All transactions pass unconditionally
            self.abac_total_requests += len(transactions)
            return transactions

        filtered = []
        for tx in transactions:
            sender = tx["sender"]
            trust_score = self.trust_manager.get_trust(sender)
            if self._fhe_enabled:
                t0 = time.perf_counter()
                decision, _, _ = self.abac.enforce_policy_with_fhe(
                    user_id=sender, requested_action="write",
                    time_of_day=random.randint(9, 17), day_type="weekday",
                    location="secure_location", trust_score=trust_score)
                params.FHE_OVERHEAD_LOG.append((time.perf_counter() - t0) * 1000.0)
            else:
                decision, _, _ = self.abac.enforce_policy_with_learning(
                    user_id=sender, requested_action="write",
                    time_of_day=random.randint(9, 17), day_type="weekday",
                    location="secure_location", trust_score=trust_score)
            if decision:
                filtered.append(tx)
                self.abac_total_requests += 1
            else:
                self.abac_denied_requests += 1
        return filtered

    def _select_delegates(self, num_delegates: int) -> List[str]:
        if self._delegate_strategy == "ucb":
            return self.trust_manager.select_delegates_ucb(num_delegates)
        return self.trust_manager.select_delegated_nodes(num_delegates)

    def _train_step(self, state: np.ndarray, action_idx: int, reward: float,
                    new_state: np.ndarray, done: bool, episode: int, step_i: int) -> None:
        if self.agent_type == "marl":
            agent_id = step_i % params.TOTAL_NODES
            self.agent.push_experience(state, action_idx, reward, new_state, done, agent_id=agent_id)
            self.agent.train(agent_id=agent_id)
            if done:
                self.agent.update_epsilon(episode, agent_id=agent_id)
                self.agent.update_learning_rate(episode, agent_id=agent_id)
        elif hasattr(self.agent, "push_experience"):
            self.agent.push_experience(state, action_idx, reward, new_state, done)
            self.agent.train()
        else:
            # DDQN path
            with torch.no_grad():
                st = torch.tensor(state, dtype=torch.float32, device=self.device).unsqueeze(0)
                nst = torch.tensor(new_state, dtype=torch.float32, device=self.device).unsqueeze(0)
                cur_q = self.agent.model(st)[0, action_idx]
                nxt_act = self.agent.model(nst).argmax(1).item()
                nxt_q = self.agent.target_model(nst)[0, nxt_act]
                td_err = abs(reward + (1-done)*self.agent.gamma*nxt_q.item() - cur_q.item())
            self.agent.memory.add(td_err, (state, action_idx, reward, new_state, done))
            if len(self.agent.memory) >= self.agent.batch_size:
                exps, idxs, wts = self.agent.memory.sample(self.agent.batch_size)
                s_ = torch.tensor(np.array([e[0] for e in exps]), dtype=torch.float32, device=self.device)
                a_ = torch.tensor([e[1] for e in exps], dtype=torch.long, device=self.device)
                r_ = torch.tensor([e[2] for e in exps], dtype=torch.float32, device=self.device)
                ns_ = torch.tensor(np.array([e[3] for e in exps]), dtype=torch.float32, device=self.device)
                d_ = torch.tensor([e[4] for e in exps], dtype=torch.float32, device=self.device)
                w_ = torch.tensor(wts, dtype=torch.float32, device=self.device)
                cq = self.agent.model(s_).gather(1, a_.unsqueeze(1)).squeeze(1)
                with torch.no_grad():
                    na = self.agent.model(ns_).argmax(1)
                    nq = self.agent.target_model(ns_).gather(1, na.unsqueeze(1)).squeeze(1)
                    tq = r_ + (1-d_)*self.agent.gamma*nq
                tde = (tq - cq).detach()
                loss = (F.smooth_l1_loss(cq, tq, reduction="none") * w_).mean()
                self.agent.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.agent.model.parameters(), 10.0)
                self.agent.optimizer.step()
                self.agent.memory.update_priorities(idxs, tde.cpu().numpy())
                self.agent.model.reset_noise()
                self.agent.target_model.reset_noise()
                self.agent.training_steps += 1
                if self.agent.training_steps % self.agent.update_frequency == 0:
                    self.agent.target_model.load_state_dict(self.agent.model.state_dict())
                if self.agent.epsilon > self.agent.epsilon_min:
                    self.agent.epsilon *= self.agent.epsilon_decay

    # ------------------------------------------------------------------ #
    #  Episode loop                                                        #
    # ------------------------------------------------------------------ #

    def run_episode(self, episode: int) -> Dict[str, Any]:
        logger.info(f"{'='*60}")
        logger.info(f"EPISODE {episode+1}/{self.episodes}")

        STEPS = params.STEPS_PER_EPISODE
        MINE_N = getattr(params, "MINE_EVERY_N_STEPS", 5)
        GT_INTERVAL = getattr(params, "GROUND_TRUTH_UPDATE_INTERVAL", 15)

        ep_reward = 0.0
        num_tx = 0
        ep_f1: List[float] = []
        ep_fhe: List[float] = []
        state = self.last_state

        for step_i in range(STEPS):
            n_tx = random.randint(15, 50)
            num_tx += n_tx
            transactions = self._generate_transactions(n_tx)

            fhe_before = len(params.FHE_OVERHEAD_LOG)
            filtered = self._filter_transactions(transactions)
            fhe_after = len(params.FHE_OVERHEAD_LOG)
            if self._fhe_enabled and fhe_after > fhe_before:
                ep_fhe.append(float(np.mean(params.FHE_OVERHEAD_LOG[fhe_before:fhe_after])))

            # Trust decay (skip if --no-decay)
            if not self._no_decay and step_i % 5 == 0:
                self.trust_manager.decay_trust(decay_rate=0.003)

            if self.attack_mode != "none" and step_i % 5 == 0:
                apply_attack(self.trust_manager, self.true_malicious_nodes,
                             self.attack_mode, current_step=step_i, current_episode=episode)
                self.attack_rounds += 1

            # Action selection
            if self.agent_type == "marl":
                agent_id = step_i % params.TOTAL_NODES
                action_idx = self.agent.select_action(state, agent_id=agent_id)
            else:
                action_idx = self.agent.select_action(state)

            dr_adj, td_adj, ct_adj = params.ACTION_MAP[action_idx]
            self.blockchain.delegation_ratio = float(
                np.clip(self.blockchain.delegation_ratio * dr_adj, 0.1, 1.0))
            params.TRUST_DECAY_RATE = float(np.clip(params.TRUST_DECAY_RATE * td_adj, 0.80, 0.99))
            params.CONSENSUS_THRESHOLD = float(np.clip(params.CONSENSUS_THRESHOLD + ct_adj, 0.3, 0.9))

            num_delegates = max(1, int(len(self.nodes) * self.blockchain.delegation_ratio))
            delegated_nodes = self._select_delegates(num_delegates)
            trust_snapshot = self.trust_manager.calculate_trust_snapshot(self.nodes)

            consensus_result = self.consensus.execute_consensus(
                filtered, delegated_nodes, trust_snapshot)

            verified_txs = consensus_result.get("verified_tx_list", [])
            for tx in verified_txs:
                self.blockchain.add_transaction(tx)

            if step_i % MINE_N == 0 and len(self.blockchain.pending_transactions) > 0:
                self.blockchain.mine_pending_transactions(miner_address="system")

            malicious_delegates = consensus_result.get("malicious_nodes", [])
            detected_this_step = set(malicious_delegates)
            for mal_node in malicious_delegates:
                self.trust_manager.update_trust(mal_node, "malicious")
                self.total_byzantine_detected += 1
            for node in delegated_nodes:
                if node not in malicious_delegates:
                    self.trust_manager.update_trust(node, "valid")

            if step_i % GT_INTERVAL == 0:
                for node in self.true_malicious_nodes:
                    if random.random() < 0.7:
                        self.trust_manager.update_trust(node, "malicious")
                for node in self.true_honest_nodes:
                    if random.random() < 0.7:
                        self.trust_manager.update_trust(node, "valid")

            current_trust = self.trust_manager.calculate_trust_snapshot(self.nodes)
            report, predicted, _ = self._evaluate_results(current_trust)
            f1 = report["macro avg"]["f1-score"]
            ep_f1.append(f1)

            new_state = self._compute_state(current_trust, consensus_result, num_tx, step_i)

            step_rewards = self.reward_system.calculate_shaped_rewards(
                current_trust, self.previous_trust_values,
                self.true_malicious_nodes, self.true_honest_nodes, gamma=0.99)
            self.previous_trust_values = current_trust.copy()
            reward_val = sum(step_rewards.values())

            fn_penalty = sum(1 for m in self.true_malicious_nodes
                             if m not in predicted) * params.FN_PENALTY_WEIGHT

            if self.attack_mode == "cra":
                tv = float(np.var(list(current_trust.values())))
                col = detect_collusion(self.trust_manager, self.true_malicious_nodes)
                combined_reward = (params.F1_REWARD_WEIGHT*(f1*100)
                                   + params.STEP_REWARD_WEIGHT*(reward_val/100)
                                   + 0.1*tv*50 - fn_penalty)
                if col > 2.0:
                    combined_reward -= min(col*2, 20.0)
            else:
                combined_reward = (params.F1_REWARD_WEIGHT*(f1*100)
                                   + params.STEP_REWARD_WEIGHT*(reward_val/100) - fn_penalty)

            ep_reward += combined_reward
            done = (step_i == STEPS - 1)

            self._train_step(state, action_idx, combined_reward, new_state, done, episode, step_i)
            state = new_state

            # ---- Streaming callback (Prompt 3 Task 2) ----
            if self.step_callback is not None:
                fhe_ms = ep_fhe[-1] if ep_fhe else None
                dr, td, ct = params.ACTION_MAP[action_idx]
                action_desc = f"dr×{dr} td×{td} ct{ct:+.2f}"
                precision = report.get("Malicious", {}).get("precision", 0.0)
                recall = report.get("Malicious", {}).get("recall", 0.0)
                event: Dict[str, Any] = {
                    "type": "step",
                    "run_id": self._run_id,
                    "episode": episode,
                    "step": step_i,
                    "trust_scores": {n: float(current_trust.get(n, 0.5)) for n in self.nodes},
                    "is_malicious": {n: (n in self.true_malicious_nodes) for n in self.nodes},
                    "is_detected": {n: (n in detected_this_step) for n in self.nodes},
                    "delegate_nodes": list(delegated_nodes),
                    "transactions_verified": len(verified_txs),
                    "transactions_rejected": n_tx - len(filtered),
                    "byzantine_detections": len(malicious_delegates),
                    "f1_score": float(f1),
                    "precision": float(precision),
                    "recall": float(recall),
                    "reward": float(combined_reward),
                    "blockchain_length": len(self.blockchain.chain),
                    "trust_separation": float(
                        np.mean([current_trust.get(n, 0.5) for n in self.true_honest_nodes]) -
                        np.mean([current_trust.get(n, 0.5) for n in self.true_malicious_nodes])
                    ),
                    "action_taken": int(action_idx),
                    "action_description": action_desc,
                    "fhe_overhead_ms": fhe_ms,
                    "timestamp": time.time(),
                }
                self.step_callback(event)

            if step_i % 20 == 0:
                logger.debug(f"Step {step_i+1}/{STEPS} | F1={f1:.4f} | R={combined_reward:.2f}")

        self.last_state = state

        final_report, final_predicted, trust_values = self._evaluate_results()
        final_f1 = final_report["macro avg"]["f1-score"]
        bc_len = len(self.blockchain.chain)
        pending = len(self.blockchain.pending_transactions)
        last_blk_tx = len(self.blockchain.chain[-1].transactions) if bc_len > 1 else 0

        honest_t = [trust_values[n] for n in self.true_honest_nodes]
        mal_t = [trust_values[n] for n in self.true_malicious_nodes]
        trust_sep = float(np.mean(honest_t) - np.mean(mal_t))
        fp_count = sum(1 for h in self.true_honest_nodes if h in final_predicted)
        fn_count = sum(1 for m in self.true_malicious_nodes if m not in final_predicted)

        logger.info(f"EPISODE {episode+1} SUMMARY | F1={final_f1:.4f} | "
                    f"R={ep_reward:.2f} | Sep={trust_sep:.4f}")
        logger.info(f"Blocks={bc_len} | Pending={pending} | FP={fp_count} | FN={fn_count}")

        if self._fhe_enabled and ep_fhe:
            logger.info(f"FHE avg overhead: {np.mean(ep_fhe):.3f} ms")

        if hasattr(self.agent, "save_model") and final_f1 > self.best_model_f1:
            self.best_model_f1 = final_f1
            ckpt = (f"{self.checkpoint_dir}/best_{self.agent_type}_{self.attack_mode}"
                    f"_f1{final_f1:.4f}.pth")
            try:
                self.agent.save_model(ckpt)
                logger.info(f"Checkpoint saved: {ckpt}")
            except Exception as e:
                logger.warning(f"Could not save model: {e}")

        self.episode_counter += 1
        if self.episode_counter % 5 == 0:
            self.chain_length_5_episodes_ago = bc_len

        result: Dict[str, Any] = {
            "cumulative_reward": ep_reward,
            "transactions": num_tx,
            "f1_score": final_f1,
            "precision": final_report.get("Malicious", {}).get("precision", 0),
            "recall": final_report.get("Malicious", {}).get("recall", 0),
            "blockchain_length": bc_len,
            "pending_tx_count": pending,
            "last_block_tx_count": last_blk_tx,
            "byzantine_detected": self.total_byzantine_detected,
            "trust_separation": trust_sep,
            "fp_count": fp_count,
            "fn_count": fn_count,
            "avg_f1": float(np.mean(ep_f1)),
            "trust_decay_rate": params.TRUST_DECAY_RATE,
            "consensus_threshold": params.CONSENSUS_THRESHOLD,
        }
        if self._fhe_enabled and ep_fhe:
            result["fhe_avg_overhead_ms"] = float(np.mean(ep_fhe))

        # Episode-end callback
        if self.step_callback is not None:
            ep_event: Dict[str, Any] = {
                "type": "episode_end",
                "run_id": self._run_id,
                "episode": episode,
                "step": STEPS - 1,
                "f1_score": final_f1,
                "precision": result["precision"],
                "recall": result["recall"],
                "reward": ep_reward,
                "blockchain_length": bc_len,
                "trust_separation": trust_sep,
                "trust_scores": {n: float(trust_values.get(n, 0.5)) for n in self.nodes},
                "is_malicious": {n: (n in self.true_malicious_nodes) for n in self.nodes},
                "is_detected": {n: (n in final_predicted) for n in self.nodes},
                "delegate_nodes": [],
                "transactions_verified": 0,
                "transactions_rejected": 0,
                "byzantine_detections": self.total_byzantine_detected,
                "action_taken": 0,
                "action_description": "episode_end",
                "fhe_overhead_ms": result.get("fhe_avg_overhead_ms"),
                "timestamp": time.time(),
            }
            self.step_callback(ep_event)

        return result

    # ------------------------------------------------------------------ #
    #  Full simulation                                                     #
    # ------------------------------------------------------------------ #

    def run_simulation(self) -> None:
        cumulative_rewards: List[float] = []
        f1_scores: List[float] = []
        blockchain_lengths: List[int] = []
        throughputs: List[int] = []
        episode_numbers: List[int] = []
        trust_decay_rates: List[float] = []
        consensus_thresholds: List[float] = []
        fhe_overheads: List[float] = []

        os.makedirs("results", exist_ok=True)
        self._json_handler = JSONFileHandler(f"results/{self._run_id}_stream.jsonl")
        logger.addHandler(self._json_handler)

        start_time = time.time()
        pbar = tqdm(range(self.episodes), desc="Training")

        for episode in pbar:
            results = self.run_episode(episode)
            cumulative_rewards.append(results["cumulative_reward"])
            f1_scores.append(results["f1_score"])
            blockchain_lengths.append(results.get("blockchain_length", 0))
            throughputs.append(results.get("last_block_tx_count", 0))
            episode_numbers.append(episode + 1)
            trust_decay_rates.append(results.get("trust_decay_rate", params.TRUST_DECAY_RATE))
            consensus_thresholds.append(results.get("consensus_threshold", params.CONSENSUS_THRESHOLD))
            if self._fhe_enabled:
                fhe_overheads.append(results.get("fhe_avg_overhead_ms", 0.0))
            self.total_consensus_rounds += 100
            pbar.set_postfix({"R": f"{results['cumulative_reward']:.1f}",
                               "F1": f"{results['f1_score']:.3f}",
                               "Sep": f"{results['trust_separation']:.3f}"})

        elapsed = time.time() - start_time
        logger.info(f"SIMULATION COMPLETE — {elapsed:.2f}s")

        final_report, predicted_malicious, trust_values = self._evaluate_results()
        logger.info(f"Best F1: {final_report['macro avg']['f1-score']:.4f}")

        try:
            plot_cumulative_reward(episode_numbers, cumulative_rewards, self.agent_type, self.attack_mode)
            plot_f1_score(episode_numbers, f1_scores, self.agent_type, self.attack_mode)
            plot_blockchain_length(episode_numbers, blockchain_lengths, self.agent_type, self.attack_mode)
            plot_throughput(episode_numbers, throughputs, self.agent_type, self.attack_mode)
            y_true = [1 if n in self.true_malicious_nodes else 0 for n in self.nodes]
            y_pred = [1 if n in predicted_malicious else 0 for n in self.nodes]
            plot_confusion_matrix_from_labels(y_true, y_pred, self.agent_type, self.attack_mode)
        except Exception as e:
            logger.warning(f"Plot error (non-fatal): {e}")

        prefix = (f"{params.TOTAL_NODES}_{params.EPISODES}_{self.agent_type}"
                  f"_{self.attack_mode}_{int(params.MALICIOUS_RATIO*100)}")
        data = {
            "Episode": episode_numbers,
            "Cumulative Reward": cumulative_rewards,
            "F1 Score": f1_scores,
            "Blockchain Length": blockchain_lengths,
            "Throughput": throughputs,
            "Trust Decay Rate": trust_decay_rates,
            "Consensus Threshold": consensus_thresholds,
        }
        if self._fhe_enabled:
            data["FHE Avg Overhead ms"] = fhe_overheads
        pd.DataFrame(data).to_csv(f"results/{prefix}_episode_metrics.csv", index=False)

        param_data: Dict[str, List] = {
            "TOTAL_NODES": [params.TOTAL_NODES],
            "EPISODES": [params.EPISODES],
            "MALICIOUS_RATIO": [params.MALICIOUS_RATIO],
            "AGENT": [self.agent_type],
            "ATTACK_MODE": [self.attack_mode],
            "CONSENSUS": [self.consensus_type],
            "CHAIN_NORM": [params.CHAIN_NORM],
            "CONSENSUS_NORM": [params.CONSENSUS_NORM],
            "SEED": [self.seed],
            "FHE_ENABLED": [self._fhe_enabled],
            "TRUST_DECAY_RATE": [params.TRUST_DECAY_RATE],
            "CONSENSUS_THRESHOLD": [params.CONSENSUS_THRESHOLD],
        }
        if self._fhe_enabled and fhe_overheads:
            param_data["fhe_avg_overhead_ms"] = [float(np.mean(fhe_overheads))]
        pd.DataFrame(param_data).to_csv(f"results/{prefix}_simulation_parameters.csv", index=False)
        logger.info(f"Results saved: {prefix}")

        # Simulation-end callback
        if self.step_callback is not None:
            self.step_callback({
                "type": "simulation_end",
                "run_id": self._run_id,
                "episode": self.episodes - 1,
                "step": 0,
                "f1_score": float(final_report["macro avg"]["f1-score"]),
                "precision": 0.0, "recall": 0.0, "reward": sum(cumulative_rewards),
                "blockchain_length": blockchain_lengths[-1] if blockchain_lengths else 0,
                "trust_separation": 0.0,
                "trust_scores": {},
                "is_malicious": {}, "is_detected": {}, "delegate_nodes": [],
                "transactions_verified": 0, "transactions_rejected": 0,
                "byzantine_detections": self.total_byzantine_detected,
                "action_taken": 0, "action_description": "simulation_end",
                "fhe_overhead_ms": None, "timestamp": time.time(),
            })

        if self._json_handler:
            self._json_handler.close()
            logger.removeHandler(self._json_handler)

    # ------------------------------------------------------------------ #
    #  Evaluation                                                          #
    # ------------------------------------------------------------------ #

    def _evaluate_results(
        self, trust_values: Optional[Dict[str, float]] = None
    ) -> Tuple[Dict, set, Dict[str, float]]:
        if trust_values is None:
            trust_values = self.trust_manager.calculate_trust_snapshot(self.nodes)
        predicted_malicious = {n for n, t in trust_values.items() if t < params.TRUST_THRESHOLD}
        y_true = [1 if n in self.true_malicious_nodes else 0 for n in self.nodes]
        y_pred = [1 if n in predicted_malicious else 0 for n in self.nodes]
        report = classification_report(y_true, y_pred,
                                       target_names=["Honest", "Malicious"],
                                       zero_division=1, output_dict=True)
        return report, predicted_malicious, trust_values
