"""E10: adversarial test of the capped-influence safety proposition (paper/proof.md).

Proposition: if every committee member's weight share is <= c/k (cap enforced or round aborted) and
honest members vote reject on an invalid transaction, a coalition of b members can force its commit
only if b*c/k >= theta.

Part A (tally level, exhaustive-ish search): for k in {8,16,32}, c in {1.5,2,3}, theta in
{0.5, 0.667, 0.8}, b in 1..k, search honest/coalition weight vectors that MAXIMISE the coalition's
post-cap share, using structured extremes + random restarts + coordinate hill-climbing.  Every
candidate is pushed through the real code path: cap (exact, or the provided iterative
SleeperGuard.cap_shares) -> TDCB.tally(max_share).  For the iterative cap we also count aborts
(rounds lost because the cap was not met).
Records: max coalition share found, whether an invalid commit was achieved, whether the bound
predicted safety, and any violation (bound says safe but commit happened).
Part B (environment level): HonestEnv with honest_fault_rate = 0 and a coalition of b of 16 nodes
that approves every invalid transaction (CRA), SleeperGuard with the cap; count invalid commits.
"""
from __future__ import annotations

import itertools
import time
from typing import Any, Dict, List

import numpy as np

from experiments.common import base_parser, out_dir, parse_seeds, run_parallel, write
from experiments.runner import calibrated_sg, run_one
from src.consensus.tdcb import TDCB
from src.trust.capping import cap_shares_exact
from src.trust.sleeper_guard import cap_shares


def _attempt(w: np.ndarray, b: int, c: float, theta: float, method: str) -> Dict[str, Any]:
    k = len(w)
    ms = c / k
    wc = cap_shares_exact(w, ms) if method == "exact" else cap_shares(w, ms)
    votes = np.zeros((1, k))
    votes[0, :b] = 1.0                          # coalition = first b members approve; honest reject
    out = TDCB(theta).tally(wc, votes, theta, max_share=ms)
    share = float(wc[:b].sum() / wc.sum()) if wc.sum() > 0 else 0.0
    cap_ok = bool(wc.max() <= ms * wc.sum() + 1e-9) if wc.sum() > 0 else False
    return dict(share=share, commit=bool(out.accept[0]), aborted=out.aborted, cap_ok=cap_ok)


def _search(job: Dict[str, Any]) -> Dict[str, Any]:
    k, c, theta, b, seed = job["k"], job["c"], job["theta"], job["b"], job["seed"]
    rng = np.random.default_rng(seed)
    cands: List[np.ndarray] = []
    for eps in (0.0, 1e-9, 1e-3, 0.01, 0.1, 0.5, 1.0):     # structured extremes
        w = np.full(k, eps)
        w[:b] = 1.0
        cands.append(w)
        for z in range(0, k - b + 1):                       # zero out z honest members
            w2 = w.copy()
            w2[b:b + z] = 0.0
            cands.append(w2)
    for _ in range(job["restarts"]):
        w = rng.random(k) ** rng.uniform(0.2, 5.0)
        w[:b] = rng.uniform(0.5, 1.0, b)
        cands.append(w)
    best = None
    commits = aborts = cap_fail = 0
    for w in cands:
        r = _attempt(w, b, c, theta, job["method"])
        commits += r["commit"]
        aborts += r["aborted"]
        cap_fail += (not r["cap_ok"]) and not r["aborted"]
        if best is None or r["share"] > best[1]["share"]:
            best = (w, r)
    # hill-climb from the best candidate: shrink honest weights / raise coalition weights
    w, r = best
    for _ in range(job["climb"]):
        w2 = w.copy()
        i = rng.integers(k)
        w2[i] = np.clip(w2[i] * (rng.uniform(1.0, 2.0) if i < b else rng.uniform(0.0, 1.0)), 0, 1)
        r2 = _attempt(w2, b, c, theta, job["method"])
        commits += r2["commit"]
        aborts += r2["aborted"]
        cap_fail += (not r2["cap_ok"]) and not r2["aborted"]
        if r2["share"] >= r["share"]:
            w, r = w2, r2
    predicted_safe = b * c / k < theta
    return dict(method=job["method"], n_candidates=len(cands) + job["climb"], k=k, c=c, theta=theta, b=b, bound_bc_over_k=b * c / k, predicted_safe=predicted_safe,
                max_share_found=r["share"], any_commit=commits > 0, n_commits=commits, n_aborts=aborts,
                cap_unenforced_not_aborted=cap_fail,
                violation=bool(predicted_safe and commits > 0))


def main() -> None:
    p = base_parser("E10 safety bound", "100-129")
    p.add_argument("--restarts", type=int, default=300)
    p.add_argument("--climb", type=int, default=300)
    args = p.parse_args()
    seeds = parse_seeds(args.seeds)
    ks, restarts, climb, steps = (8, 16, 32), args.restarts, args.climb, 600
    if args.smoke:
        ks, restarts, climb, seeds, steps = (8, 16), 20, 20, seeds[:3], 150
    t0 = time.time()
    jobs = [dict(k=k, c=c, theta=th, b=b, seed=1000 + i, restarts=restarts, climb=climb, method=m)
            for m in ("exact", "verified_iterative")
            for i, (k, c, th) in enumerate(itertools.product(ks, (1.5, 2.0, 3.0), (0.5, 0.667, 0.8)))
            for b in range(1, k + 1)]
    rows = run_parallel(_search, jobs, args.workers)
    d = out_dir("e10_safety", args)
    write("e10_safety", d, rows, args, name="search.csv", t0=t0)

    t1 = time.time()
    env_jobs = [{"cfg": dict(seed=s, steps=steps, attack="cra", honest_fault_rate=0.0,
                             malicious_fraction=b / 16, **calibrated_sg(0.02)),
                 "tags": dict(b=b, k=16, c=2.0, theta=0.667, predicted_safe=b * 2.0 / 16 < 0.667),
                 "window_start": 0}
                for b in range(1, 9) for s in seeds]
    env_rows = run_parallel(run_one, env_jobs, args.workers)
    write("e10_safety", d, env_rows, args, name="env.csv", t0=t1)


if __name__ == "__main__":
    main()
