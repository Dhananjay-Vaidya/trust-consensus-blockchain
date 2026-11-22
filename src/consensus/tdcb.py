"""Trust-weighted delegated consensus (TDCB) tally.

The tally is the only consensus decision: given the committee's public votes and the trust
weights, commit transaction t iff  sum_i w_i v[t,i] >= theta * sum_i w_i.

* ``theta`` is a configuration value (audit finding A6), never a literal.
* ``tally_backend="plain"`` evaluates the rule in the clear; ``"he"`` evaluates it under CKKS with
  :class:`src.crypto.he_tally.HETally`, so the aggregator never sees the weights.
* Votes are an *input*. This module never generates or alters votes (audit finding A2).
* If the per-delegate share cap could not be enforced (fewer positive-weight delegates than
  1/max_share), the round **aborts** (commits nothing): safety is preferred over liveness.
  See docs/DECISIONS.md D9 and paper/proof.md.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import numpy as np

from src.crypto.he_tally import HETally, plaintext_tally  # raises ImportError without tenseal


def tx_digest(*parts: Any) -> str:
    """Process-independent hash (blake2b); replaces the salted built-in ``hash`` (A6)."""
    h = hashlib.blake2b(digest_size=16)
    for p in parts:
        h.update(repr(p).encode())
        h.update(b"\x1f")
    return h.hexdigest()


@dataclass
class TallyOutcome:
    accept: np.ndarray                     # bool (T,)
    margin: np.ndarray                     # plaintext reference margin (T,), for diagnostics only
    aborted: bool = False
    he_ms: float = 0.0
    he_timings_ms: Dict[str, float] = field(default_factory=dict)
    he_flips: int = 0                      # decisions differing from the plaintext rule
    ciphertext_bytes: int = 0


class TDCB:
    def __init__(self, theta: float, tally_backend: str = "plain", he_sign_iters: int = 3) -> None:
        if tally_backend not in ("plain", "he"):
            raise ValueError(f"unknown tally_backend {tally_backend!r}")
        self.theta = float(theta)
        self.backend = tally_backend
        self._he: Optional[HETally] = HETally(he_sign_iters) if tally_backend == "he" else None

    def tally(self, weights: np.ndarray, votes: np.ndarray, theta: Optional[float] = None,
              max_share: Optional[float] = None) -> TallyOutcome:
        """``max_share``: if given, abort unless every delegate's weight share is <= max_share."""
        theta = self.theta if theta is None else float(theta)
        w = np.asarray(weights, dtype=float)
        v = np.asarray(votes, dtype=float)
        t_count = v.shape[0]
        if w.sum() <= 0 or (max_share is not None and w.max() > max_share * w.sum() + 1e-9):
            return TallyOutcome(np.zeros(t_count, dtype=bool), np.zeros(t_count), aborted=True)
        # Normalise so max weight is 1: the rule is scale-invariant and HETally clips to [0, 1].
        w = w / w.max()
        plain_accept, margin = plaintext_tally(w, v, theta)
        if self._he is None:
            return TallyOutcome(plain_accept, margin)
        r = self._he.tally(w, v, theta)
        return TallyOutcome(r.accept, margin, he_ms=float(sum(r.timings_ms.values())),
                            he_timings_ms=r.timings_ms,
                            he_flips=int((r.accept != plain_accept).sum()),
                            ciphertext_bytes=r.ciphertext_bytes)
