from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Set, Tuple

import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class TDCB:
    def __init__(self, fault_tolerance_ratio: float = 0.33) -> None:
        self.consensus_log: List[Dict[str, Any]] = []
        self.fault_tolerance: float = fault_tolerance_ratio
        self.voting_history: List[Any] = []

    def execute_consensus(
        self,
        transactions: List[Dict[str, Any]],
        delegated_nodes: List[str],
        trust_scores: Dict[str, float],
    ) -> Dict[str, Any]:
        if not delegated_nodes:
            return {"verified_transactions": 0, "status": "no_delegates"}

        votes = self._collect_votes(transactions, delegated_nodes, trust_scores)
        verified_txs = self._aggregate_votes(votes, delegated_nodes, trust_scores, transactions)
        malicious_delegates = self._detect_byzantine_behavior(votes, delegated_nodes)

        self.consensus_log.append({
            "verified_count": len(verified_txs),
            "total_submitted": len(transactions),
            "delegates": delegated_nodes,
            "malicious_detected": malicious_delegates,
            "status": "success",
        })

        return {
            "verified_transactions": len(verified_txs),
            "status": "success",
            "consensus_round": len(self.consensus_log),
            "malicious_nodes": malicious_delegates,
            "verified_tx_list": verified_txs,
        }

    def _collect_votes(
        self,
        transactions: List[Dict[str, Any]],
        delegates: List[str],
        trust_scores: Dict[str, float],
    ) -> Dict[str, Dict[str, bool]]:
        votes: Dict[str, Dict[str, bool]] = {delegate: {} for delegate in delegates}
        for tx in transactions:
            tx_hash = self._hash_transaction(tx)
            for delegate in delegates:
                trust = trust_scores.get(delegate, 0.5)
                is_valid = self._verify_transaction(tx)
                if trust > 0.7:
                    votes[delegate][tx_hash] = is_valid
                elif trust < 0.3:
                    votes[delegate][tx_hash] = not is_valid
                else:
                    votes[delegate][tx_hash] = (hash(delegate + tx_hash) % 2 == 0)
        return votes

    def _aggregate_votes(
        self,
        votes: Dict[str, Dict[str, bool]],
        delegates: List[str],
        trust_scores: Dict[str, float],
        transactions: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        verified_txs: List[Dict[str, Any]] = []
        tx_hash_map: Dict[str, Dict[str, Any]] = {
            self._hash_transaction(tx): tx for tx in transactions
        }

        tx_votes: Dict[str, List[Tuple[str, bool]]] = {}
        for delegate, delegate_votes in votes.items():
            for tx_hash, vote in delegate_votes.items():
                if tx_hash not in tx_votes:
                    tx_votes[tx_hash] = []
                tx_votes[tx_hash].append((delegate, vote))

        for tx_hash, delegate_votes in tx_votes.items():
            total_weight = sum(trust_scores.get(d, 0.5) for d, _ in delegate_votes)
            approve_weight = sum(
                trust_scores.get(d, 0.5) for d, vote in delegate_votes if vote
            )
            if total_weight > 0 and approve_weight / total_weight >= 0.667:
                if tx_hash in tx_hash_map:
                    verified_txs.append(tx_hash_map[tx_hash])

        return verified_txs

    def _detect_byzantine_behavior(
        self,
        votes: Dict[str, Dict[str, bool]],
        delegates: List[str],
    ) -> List[str]:
        malicious: List[str] = []
        tx_hashes: Set[str] = set()
        for delegate_votes in votes.values():
            tx_hashes.update(delegate_votes.keys())

        for delegate in delegates:
            disagreement_count = 0
            total_votes = 0
            for tx_hash in tx_hashes:
                majority_vote = (
                    sum(1 for d in delegates if votes.get(d, {}).get(tx_hash, False))
                    > len(delegates) / 2
                )
                delegate_vote = votes.get(delegate, {}).get(tx_hash, False)
                if delegate_vote != majority_vote:
                    disagreement_count += 1
                total_votes += 1
            if total_votes > 0 and disagreement_count / total_votes > 0.5:
                malicious.append(delegate)

        return malicious

    def _verify_transaction(self, transaction: Dict[str, Any]) -> bool:
        required_fields = ["amount", "sender", "recipient"]
        if not all(field in transaction for field in required_fields):
            return False
        return transaction.get("amount", 0) > 0

    def _hash_transaction(self, tx: Dict[str, Any]) -> str:
        tx_string = f"{tx.get('sender')}{tx.get('recipient')}{tx.get('amount')}"
        return hashlib.sha256(tx_string.encode()).hexdigest()[:16]

    def get_consensus_metrics(self) -> Dict[str, Any]:
        if not self.consensus_log:
            return {
                "total_votes": 0,
                "byzantine_count": 0,
                "consensus_ratio": 0.0,
            }
        total_rounds = len(self.consensus_log)
        total_votes = sum(len(log.get("delegates", [])) for log in self.consensus_log)
        byzantine_count = sum(
            len(log.get("malicious_detected", [])) for log in self.consensus_log
        )
        consensus_ratio = (
            sum(1 for log in self.consensus_log if log.get("status") == "success")
            / total_rounds
        )
        return {
            "total_votes": total_votes,
            "byzantine_count": byzantine_count,
            "consensus_ratio": consensus_ratio,
            "total_consensus_rounds": total_rounds,
            "avg_verified_per_round": sum(
                log["verified_count"] for log in self.consensus_log
            ) / total_rounds,
        }
