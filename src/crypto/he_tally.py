"""Homomorphic trust-weighted vote tally (CKKS via TenSEAL).

Two-party protocol simulated in one process:
  trust authority : knows the k delegate trust weights, encrypts them.
  aggregator      : sees Enc(w) and the PUBLIC signed votes, never the weights.
  decryptor       : decodes one ciphertext per step (T slots, one per transaction).

accept_t  <=>  sum_i w_i * v[t,i]  >=  theta * sum_i w_i
          <=>  margin_t = sum_i w_i * (v[t,i] - theta) / k  >= 0      (|margin| <= 1 when w in [0,1])

Production would use threshold/multiparty CKKS (e.g. OpenFHE) so no single party holds the secret key;
that is out of scope here and must be stated in the paper's limitations.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Sequence

import numpy as np

try:
    import tenseal as ts
except ImportError as exc:  # fail loudly: a silent mock is how the old FHE path went unnoticed
    raise ImportError("tenseal is required for HETally: pip install tenseal") from exc

_SIGN = [0.0, 1.5, 0.0, -0.5]  # odd polynomial 1.5x - 0.5x^3, 2 multiplicative levels per iteration
_BUDGET_BITS = {8192: 218, 16384: 438, 32768: 881}  # 128-bit security bounds for CKKS


@dataclass
class HETallyResult:
    accept: np.ndarray                 # bool (T,)
    squashed: np.ndarray               # decoded output in (-1, 1); reveals margin only inside the band
    timings_ms: Dict[str, float] = field(default_factory=dict)
    ciphertext_bytes: int = 0


class HETally:
    def __init__(self, sign_iters: int = 3) -> None:
        """sign_iters=0: decode the raw margin (cheapest, decryptor learns margins).
        sign_iters>=1: iterate the sign polynomial so the decryptor learns ~sign(margin) outside a small band."""
        self.sign_iters = sign_iters
        levels = 2 * sign_iters + 1                      # +1 level for the ct x pt product
        bits = 60 + 40 * levels + 60
        poly = next(n for n, b in sorted(_BUDGET_BITS.items()) if bits <= b)
        self.ctx = ts.context(ts.SCHEME_TYPE.CKKS, poly, -1, [60] + [40] * levels + [60])
        self.ctx.global_scale = 2 ** 40
        self.ctx.generate_galois_keys()
        self.poly_modulus_degree = poly

    def tally(self, weights: Sequence[float], votes: np.ndarray, theta: float) -> HETallyResult:
        w = np.clip(np.asarray(weights, dtype=float), 0.0, 1.0)
        v = np.asarray(votes, dtype=float)               # (T, k), 1.0 = approve
        t_count, k = v.shape
        assert w.shape == (k,), "weights must have one entry per delegate"
        tm: Dict[str, float] = {}

        t0 = time.perf_counter()
        enc_w = ts.ckks_vector(self.ctx, w.tolist())     # trust authority
        tm["encrypt"] = (time.perf_counter() - t0) * 1e3

        t0 = time.perf_counter()
        enc_m = enc_w.mm(((v - theta) / k).T.tolist())   # aggregator: all T margins in one ciphertext
        tm["margin"] = (time.perf_counter() - t0) * 1e3

        t0 = time.perf_counter()
        for _ in range(self.sign_iters):
            enc_m = enc_m.polyval(_SIGN)
        tm["sign_poly"] = (time.perf_counter() - t0) * 1e3

        t0 = time.perf_counter()
        out = np.asarray(enc_m.decrypt()[:t_count], dtype=float)   # decryptor
        tm["decrypt"] = (time.perf_counter() - t0) * 1e3
        return HETallyResult(out > 0.0, out, tm, len(enc_m.serialize()))


def plaintext_tally(weights: Sequence[float], votes: np.ndarray, theta: float):
    """Reference rule; returns (accept bool (T,), normalised margin (T,))."""
    w = np.clip(np.asarray(weights, dtype=float), 0.0, 1.0)
    v = np.asarray(votes, dtype=float)
    margin = (v @ w - theta * w.sum()) / len(w)
    return margin >= 0.0, margin
