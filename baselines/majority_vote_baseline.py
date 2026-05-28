from __future__ import annotations

import hashlib
from typing import Any, Dict, List

from baselines.consensus_base import ConsensusBase


class MajorityVoteConsensus(ConsensusBase):
    """
    Simple majority vote — no trust weighting, no learning.

    - All nodes vote with equal weight.
    - Verified if strict majority (>50%) approve.
    - A node is flagged only if it votes against a supermajority (>75%).
    """

    def __init__(self) -> None:
        self._round = 0
        self._verified_counts: List[int] = []
        self._byzantine_counts: List[int] = []

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
        n = len(delegated_nodes)
        if n == 0:
            return {
                "verified_transactions": 0,
                "verified_tx_list": [],
                "malicious_nodes": [],
                "status": "no_delegates",
                "consensus_round": self._round,
                "metrics": {},
            }

        # Collect votes — low-trust delegates may vote adversarially
        votes: Dict[str, Dict[str, bool]] = {d: {} for d in delegated_nodes}
        tx_map: Dict[str, Dict[str, Any]] = {}

        for tx in transactions:
            h = self._hash_tx(tx)
            tx_map[h] = tx
            valid = self._verify_tx(tx)
            for d in delegated_nodes:
                t = trust_snapshot.get(d, 0.5)
                if t < 0.3:
                    votes[d][h] = not valid
                else:
                    votes[d][h] = valid

        # Verify if strict majority approves
        verified_txs: List[Dict[str, Any]] = []
        for h, tx in tx_map.items():
            approvals = sum(1 for d in delegated_nodes if votes[d].get(h, False))
            if approvals > n / 2:
                verified_txs.append(tx)

        # Flag nodes voting against supermajority (>75%)
        supermajority = 0.75
        byzantine: List[str] = []
        for d in delegated_nodes:
            disagreements = 0
            for h in tx_map:
                approve_votes = sum(1 for dd in delegated_nodes if votes[dd].get(h, False))
                super_approve = approve_votes / n > supermajority
                super_reject = (n - approve_votes) / n > supermajority
                d_vote = votes[d].get(h, False)
                if (super_approve and not d_vote) or (super_reject and d_vote):
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
                "verified": len(verified_txs),
                "byzantine_flagged": len(byzantine),
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
