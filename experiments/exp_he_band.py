"""E4c: CKKS guard band and decryptor leakage of HETally.

(a) Guard-band stress: equal weights and theta = j/k + delta put the margin of every transaction
    with j approvals at exactly -delta. Sweeping delta over +-{1e-2 ... 1e-9} and 0 measures the
    smallest |margin| at which HE and plaintext decisions still agree.
(b) Margin recoverability: the sign polynomial p(x) = 1.5x - 0.5x^3 is strictly increasing on
    [-1, 1], so p^(s) is invertible there.  For every decision in decisions.csv we invert the decoded
    value by bisection and report how accurately the decryptor recovers the margin, plus how often
    the output is saturated (|out| > 0.9), i.e. how often it actually hides the magnitude.
Outputs: results/raw/e4_he/{band.csv, leakage.csv}
"""
from __future__ import annotations

import time

import numpy as np
import pandas as pd

from experiments.common import RAW, base_parser, out_dir, write
from src.crypto.he_tally import HETally, plaintext_tally


def p_iter(x: np.ndarray, s: int) -> np.ndarray:
    for _ in range(s):
        x = 1.5 * x - 0.5 * x ** 3
    return x


def invert(y: np.ndarray, s: int) -> np.ndarray:
    lo, hi = -np.ones_like(y), np.ones_like(y)
    yc = np.clip(y, -1.0, 1.0)
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        up = p_iter(mid, s) < yc
        lo = np.where(up, mid, lo)
        hi = np.where(up, hi, mid)
    return 0.5 * (lo + hi)


def main() -> None:
    args = base_parser("E4c HE band + leakage", "0").parse_args()
    d = out_dir("e4_he", args) if args.smoke else RAW / "e4_he"
    d.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    k, t_count = 16, 17                       # one transaction per approval count j = 0..16
    deltas = [s * 10.0 ** -e for e in range(2, 10) for s in (1, -1)] + [0.0]
    sign_iters = (0, 1, 2, 3) if not args.smoke else (0,)
    rows = []
    for s in sign_iters:
        he = HETally(s)
        votes = np.array([[1.0] * j + [0.0] * (k - j) for j in range(t_count)])
        for j in range(1, k):
            for delta in deltas:
                theta = j / k + delta
                if not 0 < theta <= 1:
                    continue
                r = he.tally(np.ones(k), votes, theta)
                acc, margin = plaintext_tally(np.ones(k), votes, theta)
                rows.append(dict(sign_iters=s, j=j, delta=delta, margin=float(margin[j]), plain=bool(acc[j]),
                                 he=bool(r.accept[j]), he_out=float(r.squashed[j]), flip=bool(acc[j] != r.accept[j])))
        print(f"band sign_iters={s} done ({time.time() - t0:.0f}s)", flush=True)
    write("e4_he", d, rows, args, name="band.csv", t0=t0)

    dec = pd.read_csv(RAW / "e4_he" / "decisions.csv")
    lk = []
    for s, g in dec.groupby("sign_iters"):
        est = invert(g.he_out.values, int(s))
        err = np.abs(est - g.margin.values)
        lk.append(dict(sign_iters=int(s), n=len(g), median_abs_margin=float(g.margin.abs().median()),
                       recover_err_median=float(np.median(err)), recover_err_p99=float(np.quantile(err, 0.99)),
                       recover_err_max=float(err.max()),
                       saturated_frac=float((g.he_out.abs() > 0.9).mean()),
                       corr_out_margin=float(np.corrcoef(g.he_out.values, g.margin.values)[0, 1])))
    write("e4_he", d, lk, args, name="leakage.csv")


if __name__ == "__main__":
    main()
