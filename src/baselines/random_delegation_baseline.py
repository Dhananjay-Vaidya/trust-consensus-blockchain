from __future__ import annotations

import hashlib
import random
from typing import Any, Dict, List

from src.baselines.consensus_base import ConsensusBase


class RandomDelegation(ConsensusBase):
    """
    Exactly like TDCB but delegate selection is uniformly random.

    Isolates the contribution of trust-based delegation vs random selection.
    Uses simple majority vote after random delegate selection.
    """

    def __init__(self) -> None:
        self._round = 0
        self._verified_counts: List[int] = []
        self._byzantine_counts: List[int] = []
        self._all_node_ids: List[str] = []

    def set_node_pool(self, nodes: List[str]) -> None:
        """Must be called before execute_consensus with the full node list."""
        self._all_node_ids = list(nodes)

    def _hash_tx(self, tx: Dict[str, Any]) -> str:
        s = f"{tx.get('sender')}{tx.get('recipient')}{tx.get('amount')}"
        return hashlib.sha256(s.encode()).hexdigest()[:16]

    def _verify_tx(self, tx: Dict[str, Any]) -> bool:
        return all(k in tx for k in ("sender", "recipient", "amount")) and tx["amount"] > 0

    def execute_consensus(
        self,
        transactions: List[Dict[str, Any]],
        delegated_nodes: List[str],
        trust_snapshot: Dict[str, float],
    ) -> Dict[str, Any]:
        self._round += 1

        # Ignore the trust-selected delegated_nodes; pick randomly instead
        pool = self._all_node_ids if self._all_node_ids else list(trust_snapshot.keys())
        n_delegates = max(1, len(delegated_nodes))  # same count, random selection
        delegates = random.sample(pool, min(n_delegates, len(pool)))
        n = len(delegates)

        if n == 0:
            return {
                "verified_transactions": 0,
                "verified_tx_list": [],
                "malicious_nodes": [],
                "status": "no_delegates",
                "consensus_round": self._round,
                "metrics": {},
            }

        votes: Dict[str, Dict[str, bool]] = {d: {} for d in delegates}
        tx_map: Dict[str, Dict[str, Any]] = {}

        for tx in transactions:
            h = self._hash_tx(tx)
            tx_map[h] = tx
            valid = self._verify_tx(tx)
            for d in delegates:
                t = trust_snapshot.get(d, 0.5)
                if t < 0.3:
                    votes[d][h] = not valid
                else:
                    votes[d][h] = valid

        verified_txs: List[Dict[str, Any]] = []
        for h, tx in tx_map.items():
            approvals = sum(1 for d in delegates if votes[d].get(h, False))
            if approvals > n / 2:
                verified_txs.append(tx)

        # Simple Byzantine detection — >50% disagreement with majority
        byzantine: List[str] = []
        for d in delegates:
            disagreements = 0
            for h in tx_map:
                majority = sum(1 for dd in delegates if votes[dd].get(h, False)) > n / 2
                if votes[d].get(h, False) != majority:
                    disagreements += 1
            if len(tx_map) > 0 and disagreements / len(tx_map) > 0.5:
                byzantine.append(d)

        self._verified_counts.append(len(verified_txs))
        self._byzantine_counts.append(len(byzantine))

        return {
            "verified_transactions": len(verified_txs),
            "verified_tx_list": verified_txs,
            "malicious_nodes": byzantine,
            "status": "success",
            "consensus_round": self._round,
            "metrics": {
                "random_delegates": delegates,
                "verified": len(verified_txs),
            },
        }

    def get_consensus_metrics(self) -> Dict[str, Any]:
        rounds = len(self._verified_counts)
        if rounds == 0:
            return {"total_votes": 0, "byzantine_count": 0, "consensus_ratio": 1.0}
        return {
            "total_votes": 0,
            "byzantine_count": sum(self._byzantine_counts),
            "consensus_ratio": 1.0,
            "avg_verified_per_round": sum(self._verified_counts) / rounds,
            "total_rounds": rounds,
        }
