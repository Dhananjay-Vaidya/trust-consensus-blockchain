from __future__ import annotations

import hashlib
import random
from typing import Any, Dict, List

from src.baselines.consensus_base import ConsensusBase


class StaticDPoSConsensus(ConsensusBase):
    """
    Standard Delegated Proof of Stake — no adaptive trust.

    - Delegate selection is uniformly random (no Thompson sampling).
    - All selected delegates have equal weight (1/n).
    - Transaction verified if >50 % approve.
    - No Byzantine detection, no trust updates.
    """

    def __init__(self) -> None:
        self._round = 0
        self._verified_counts: List[int] = []

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

        verified_txs: List[Dict[str, Any]] = []
        for tx in transactions:
            h = self._hash_tx(tx)
            valid = self._verify_tx(tx)
            # Each delegate votes with equal weight, ignoring trust
            approvals = sum(
                1 for d in delegated_nodes
                if (hash(d + h) % 2 == 0) or valid  # simplified: honest delegates approve valid tx
            )
            # Pure 50% majority
            if approvals > n / 2:
                verified_txs.append(tx)

        self._verified_counts.append(len(verified_txs))

        return {
            "verified_transactions": len(verified_txs),
            "verified_tx_list": verified_txs,
            "malicious_nodes": [],   # No Byzantine detection in DPoS
            "status": "success",
            "consensus_round": self._round,
            "metrics": {"verified": len(verified_txs), "n_delegates": n},
        }

    def get_consensus_metrics(self) -> Dict[str, Any]:
        rounds = len(self._verified_counts)
        if rounds == 0:
            return {"total_votes": 0, "byzantine_count": 0, "consensus_ratio": 1.0}
        return {
            "total_votes": 0,
            "byzantine_count": 0,
            "consensus_ratio": 1.0,
            "avg_verified_per_round": sum(self._verified_counts) / rounds,
            "total_rounds": rounds,
        }
