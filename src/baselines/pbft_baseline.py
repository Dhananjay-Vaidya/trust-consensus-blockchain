from __future__ import annotations

import hashlib
from typing import Any, Dict, List

from src.baselines.consensus_base import ConsensusBase


class PBFTConsensus(ConsensusBase):
    """
    Practical Byzantine Fault Tolerance (PBFT) simulation.

    Requires 2f+1 matching votes out of n delegates where
    f = floor((n - 1) / 3).  No trust weighting — pure vote counting.
    Three phases collapsed to a single-pass vote tally.
    """

    def __init__(self) -> None:
        self._round = 0
        self._prepare_count: List[int] = []
        self._commit_count: List[int] = []
        self._byzantine_count: List[int] = []

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

        f = (n - 1) // 3          # Byzantine tolerance
        quorum = 2 * f + 1        # Minimum matching votes needed

        # ------ Pre-prepare / prepare: each delegate votes on each tx ------
        # A delegate with trust > 0.7 votes correctly; < 0.3 votes adversarially
        votes: Dict[str, Dict[str, bool]] = {d: {} for d in delegated_nodes}
        tx_map: Dict[str, Dict[str, Any]] = {}

        for tx in transactions:
            h = self._hash_tx(tx)
            tx_map[h] = tx
            valid = self._verify_tx(tx)
            for d in delegated_nodes:
                t = trust_snapshot.get(d, 0.5)
                if t > 0.7:
                    votes[d][h] = valid
                elif t < 0.3:
                    votes[d][h] = not valid
                else:
                    votes[d][h] = (hash(d + h) % 2 == 0)

        # ------ Commit phase: count matching votes per tx ------
        verified_txs: List[Dict[str, Any]] = []
        prepare_total = 0
        commit_total = 0

        for h, tx in tx_map.items():
            approve_votes = sum(1 for d in delegated_nodes if votes[d].get(h, False))
            reject_votes = n - approve_votes
            prepare_total += n   # every delegate casts a prepare vote

            majority_approve = approve_votes >= quorum
            majority_reject = reject_votes >= quorum

            if majority_approve:
                commit_total += approve_votes
                verified_txs.append(tx)
            # If neither supermajority, tx is dropped (no commit)

        # ------ Byzantine detection: nodes inconsistent with quorum ------
        byzantine: List[str] = []
        for d in delegated_nodes:
            disagreements = 0
            for h in tx_map:
                # Majority vote for this tx
                approve_votes = sum(1 for dd in delegated_nodes if votes[dd].get(h, False))
                majority = approve_votes >= quorum
                if votes[d].get(h, False) != majority:
                    disagreements += 1
            if len(tx_map) > 0 and disagreements / len(tx_map) > 0.5:
                byzantine.append(d)

        self._prepare_count.append(prepare_total)
        self._commit_count.append(commit_total)
        self._byzantine_count.append(len(byzantine))

        return {
            "verified_transactions": len(verified_txs),
            "verified_tx_list": verified_txs,
            "malicious_nodes": byzantine,
            "status": "success",
            "consensus_round": self._round,
            "metrics": {
                "f": f,
                "quorum": quorum,
                "n_delegates": n,
                "prepare_count": prepare_total,
                "commit_count": commit_total,
                "byzantine_count": len(byzantine),
            },
        }

    def get_consensus_metrics(self) -> Dict[str, Any]:
        rounds = len(self._prepare_count)
        if rounds == 0:
            return {"total_votes": 0, "byzantine_count": 0, "consensus_ratio": 0.0}
        return {
            "total_votes": sum(self._prepare_count),
            "byzantine_count": sum(self._byzantine_count),
            "consensus_ratio": 1.0,   # PBFT always reaches consensus if f < n/3
            "avg_prepare_per_round": sum(self._prepare_count) / rounds,
            "avg_commit_per_round": sum(self._commit_count) / rounds,
            "total_rounds": rounds,
        }
