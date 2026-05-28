from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class ConsensusBase(ABC):
    """Shared interface for all consensus mechanisms."""

    @abstractmethod
    def execute_consensus(
        self,
        transactions: List[Dict[str, Any]],
        delegated_nodes: List[str],
        trust_snapshot: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Returns:
            dict with keys:
              verified_transactions  – int count
              verified_tx_list       – list of approved tx dicts
              malicious_nodes        – list of detected Byzantine nodes
              status                 – str
              consensus_round        – int
              metrics                – dict (algorithm-specific)
        """

    @abstractmethod
    def get_consensus_metrics(self) -> Dict[str, Any]:
        """Return algorithm-specific performance metrics."""
