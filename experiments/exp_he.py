"""E4: accuracy and cost of the homomorphic trust-weighted tally (HETally).

Outputs (results/raw/e4_he/):
  decisions.csv  one row per transaction decided: config, plaintext margin, HE output, flip flag
  timings.csv    one row per tally: k, T, sign_iters, poly degree, encrypt/margin/sign/decrypt ms,
                 total ms, output-ciphertext bytes
  consensus.csv  end-to-end HonestEnv runs with tally_backend plain vs he (same seeds)
  params.json    CKKS parameter sets and the 128-bit security bound used
Timings are measured sequentially (no parallel workers) on the machine recorded in meta.json.
"""
from __future__ import annotations

import json
import time

import numpy as np

from experiments.common import base_parser, out_dir, parse_seeds, write
from experiments.runner import calibrated_sg, run_one
from src.crypto.he_tally import _BUDGET_BITS, HETally, plaintext_tally

KS = (8, 16, 32, 64)
TS = (8, 32, 128)
SIGN_ITERS = (0, 1, 2, 3)
BAND = 1e-3


def main() -> None:
    p = base_parser("E4 HE tally", "100-104")
    p.add_argument("--reps", type=int, default=5, help="tallies per (k, T, sign_iters)")
    args = p.parse_args()
    seeds = parse_seeds(args.seeds)
    reps, ks, ts_, steps = args.reps, KS, TS, 200
    if args.smoke:
        reps, ks, ts_, steps, seeds = 1, (8, 16), (8, 32), 30, seeds[:1]
    d = out_dir("e4_he", args)
    t0 = time.time()
    rng = np.random.default_rng(2024)
    dec_rows, tim_rows, params = [], [], {}
    for s in SIGN_ITERS:
        he = HETally(s)
        levels = 2 * s + 1
        params[str(s)] = {"poly_modulus_degree": he.poly_modulus_degree,
                          "coeff_mod_bit_sizes": [60] + [40] * levels + [60],
                          "total_bits": 120 + 40 * levels,
                          "max_bits_128bit_security": _BUDGET_BITS[he.poly_modulus_degree],
                          "global_scale": "2^40"}
        he.tally(rng.random(8), (rng.random((8, 8)) < 0.5).astype(float), 0.667)   # warm-up, discarded
        for k in ks:
            for t in ts_:
                for r in range(reps):
                    w = rng.random(k)
                    pa = rng.uniform(0.4, 0.95)
                    v = (rng.random((t, k)) < pa).astype(float)
                    theta = 0.667
                    res = he.tally(w, v, theta)
                    acc, margin = plaintext_tally(w, v, theta)
                    tim_rows.append(dict(sign_iters=s, k=k, T=t, rep=r, poly=he.poly_modulus_degree,
                                         **{f"{kk}_ms": vv for kk, vv in res.timings_ms.items()},
                                         total_ms=sum(res.timings_ms.values()),
                                         per_tx_ms=sum(res.timings_ms.values()) / t,
                                         ct_bytes=res.ciphertext_bytes))
                    for i in range(t):
                        dec_rows.append(dict(sign_iters=s, k=k, T=t, rep=r, margin=float(margin[i]),
                                             he_out=float(res.squashed[i]), plain=bool(acc[i]),
                                             he=bool(res.accept[i]), flip=bool(acc[i] != res.accept[i]),
                                             in_band=bool(abs(margin[i]) <= BAND)))
                print(f"sign_iters={s} k={k} T={t} done ({time.time() - t0:.0f}s)", flush=True)
    write("e4_he", d, dec_rows, args, name="decisions.csv")
    write("e4_he", d, tim_rows, args, name="timings.csv", t0=t0)
    (d / "params.json").write_text(json.dumps(params, indent=2))

    # ---- consensus-level: plain vs he on identical seeds ------------------------------------
    t1 = time.time()
    rows = []
    for s_it in ((0, 3) if not args.smoke else (0,)):
        n_seeds = seeds if s_it == 0 else seeds[:3]
        for seed in n_seeds:
            for backend in ("plain", "he"):
                cfg = dict(seed=seed, steps=steps, t_switch=steps // 2, attack="tdp", attack_intensity=0.25,
                           trust_backend="sleeper_guard", tally_backend=backend, he_sign_iters=s_it,
                           **calibrated_sg(0.05))
                r = run_one({"cfg": cfg, "tags": dict(backend=backend, sign_iters=s_it)})
                rows.append(r)
                print(f"consensus seed={seed} {backend} s={s_it}: wall/step={r['wall_ms_per_step']:.1f}ms", flush=True)
    write("e4_he", d, rows, args, name="consensus.csv", t0=t1)


if __name__ == "__main__":
    main()
