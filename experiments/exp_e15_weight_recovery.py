"""E15: can the HETally decryptor recover the hidden trust weights from what it decrypts?

Per step the decryptor sees one decoded ciphertext of T = 16 slots, out_t = p^(s)(m_t) with
    m_t = sum_i w_i (V[t,i] - theta) / k        (k = 16 delegates, public votes V, public theta)
and p(x) = 1.5x - 0.5x^3 iterated s times (s = 0: raw margin).  V, theta, k and s are public, so every
decoded slot is one (non)linear equation in the k unknown weights.  We run the real HETally (CKKS,
TenSEAL) on n = 1..16 batches and recover w by least squares:
  direct  : treat out_t as the margin (exact for s = 0, mis-specified for s >= 1)
  invert  : undo p^(s) by bisection first (p^(s) is strictly increasing on [-1, 1]); outputs that are
            saturated (|out| > 1 - 1e-6, where the inverse is ill-conditioned) are dropped.
Weights are drawn U(0.05, 1) and normalised to max 1, as TDCB does before encrypting.  Votes follow the
environment's vote model (invalid rate 0.3, honest fault 0.05, all delegates honest), so the margins are
the ones the system actually produces.
Outputs: results/raw/e15_weight_recovery/{runs.csv, summary.csv, meta.json}
"""
from __future__ import annotations

import time
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from experiments.common import base_parser, out_dir, parse_seeds, write
from experiments.exp_he_band import invert
from src.crypto.he_tally import HETally

K, T, THETA = 16, 16, 0.667
INVALID_RATE, FAULT = 0.3, 0.05
TOLS = (1e-3, 1e-2)
SAT = 1.0 - 1e-6


def _votes(rng: np.random.Generator) -> np.ndarray:
    valid = rng.random(T) >= INVALID_RATE
    flips = rng.random((T, K)) < FAULT
    return (valid[:, None] ^ flips).astype(float)


def _lstsq(a: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, int]:
    if len(y) == 0:
        return np.full(a.shape[1], np.nan), 0
    w, _, rank, _ = np.linalg.lstsq(a, y, rcond=None)
    return w, int(rank)


def main() -> None:
    args = base_parser("E15 HE weight recovery", "100-129").parse_args()
    seeds = parse_seeds(args.seeds)
    sign_iters, n_max = (0, 1, 2, 3), 16
    if args.smoke:
        seeds, sign_iters, n_max = seeds[:3], (0, 1), 4
    t0 = time.time()
    rows: List[Dict[str, Any]] = []
    for s in sign_iters:
        he = HETally(s)
        for seed in seeds:
            rng = np.random.default_rng([seed, 15])
            w = rng.uniform(0.05, 1.0, K)
            w = w / w.max()
            a_blocks, outs = [], []
            for n in range(1, n_max + 1):
                v = _votes(rng)
                r = he.tally(w, v, THETA)
                a_blocks.append((v - THETA) / K)
                outs.append(np.asarray(r.squashed, dtype=float))
                a, y = np.vstack(a_blocks), np.concatenate(outs)
                margins = a @ w
                for est in ("direct", "invert"):
                    if est == "direct":
                        keep = np.ones(len(y), dtype=bool)
                        target = y
                    else:
                        keep = np.abs(y) < SAT
                        target = invert(y, s) if s > 0 else y
                    w_hat, rank = _lstsq(a[keep], target[keep])
                    err = np.abs(w_hat - w)
                    rows.append(dict(sign_iters=s, seed=seed, batches=n, estimator=est, equations=int(keep.sum()),
                                     rank=rank, max_abs_err=float(err.max()), rmse=float(np.sqrt(np.mean(err ** 2))),
                                     saturated_frac=float((np.abs(y) > 0.9).mean()),
                                     median_abs_margin=float(np.median(np.abs(margins))),
                                     max_abs_margin=float(np.abs(margins).max())))
        print(f"[e15] sign_iters={s} done ({time.time() - t0:.0f}s)", flush=True)

    df = pd.DataFrame(rows)
    summary = []
    for (s, est), g in df.groupby(["sign_iters", "estimator"]):
        rec: Dict[str, Any] = dict(sign_iters=int(s), estimator=est, trials=int(g.seed.nunique()), max_batches=n_max)
        for tol in TOLS:
            first = []
            for _, h in g.groupby("seed"):
                ok = h[(h["rank"] == K) & (h.max_abs_err < tol)].batches
                first.append(float(ok.min()) if len(ok) else np.nan)
            f = np.array(first)
            tag = f"{tol:.0e}"
            rec[f"recovered_{tag}"] = int(np.isfinite(f).sum())
            rec[f"batches_median_{tag}"] = float(np.nanmedian(f)) if np.isfinite(f).any() else np.nan
            rec[f"batches_max_{tag}"] = float(np.nanmax(f)) if np.isfinite(f).any() else np.nan
        last = g[g.batches == n_max]
        rec["max_abs_err_at_max_batches_median"] = float(last.max_abs_err.median())
        rec["saturated_frac_mean"] = float(g.saturated_frac.mean())
        summary.append(rec)
    d = out_dir("e15_weight_recovery", args)
    write("e15_weight_recovery", d, summary, args, name="summary.csv")
    write("e15_weight_recovery", d, rows, args, name="runs.csv", t0=t0,
          extra_meta={"protocol": dict(k=K, T=T, theta=THETA, invalid_rate=INVALID_RATE, honest_fault=FAULT,
                                       weights="U(0.05,1) normalised to max 1", sign_iters=list(sign_iters),
                                       max_batches=n_max, tolerances=list(TOLS), saturation_cut=SAT,
                                       seeds=seeds)})


if __name__ == "__main__":
    main()
