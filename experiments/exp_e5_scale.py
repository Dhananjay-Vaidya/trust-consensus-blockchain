"""E5: scale.  nodes {16, 64, 256, 1024} x committee k {8, 16, 32, 64} (k <= nodes).

Reports simulated throughput / latency percentiles (cost model D7), measured wall-clock per step and
peak Python heap (tracemalloc) of one run.  SleeperGuard (calibrated, f=0.05), TDP intensity 0.25,
plaintext tally (HE cost vs k is E4).  Runs are executed with 1 worker per job so wall-clock is
comparable across sizes.
"""
from __future__ import annotations

import itertools
import time

from experiments.common import base_parser, out_dir, parse_seeds, run_parallel, write
from experiments.runner import calibrated_sg, run_one


def main() -> None:
    args = base_parser("E5 scale", "100-109").parse_args()
    seeds = parse_seeds(args.seeds)
    steps, nodes, ks = 600, (16, 64, 256, 1024), (8, 16, 32, 64)
    if args.smoke:
        seeds, steps, nodes, ks = seeds[:3], 100, (16, 64), (8, 16)
    t0 = time.time()
    jobs = []
    for n, k, s in itertools.product(nodes, ks, seeds):
        if k > n:
            continue
        jobs.append({"cfg": dict(seed=s, steps=steps, t_switch=steps // 2, num_nodes=n, committee_size=k,
                                 attack="tdp", attack_intensity=0.25, selection_temperature=0.1,
                                 **calibrated_sg(0.05)),
                     "tags": dict(nodes=n, k=k), "measure_memory": True})
    # wall-clock fairness: modest parallelism, identical for all sizes
    rows = run_parallel(run_one, jobs, min(args.workers, 4))
    write("e5_scale", out_dir("e5_scale", args), rows, args, t0=t0,
          extra_meta={"note": "wall-clock measured with up to 4 concurrent worker processes"})


if __name__ == "__main__":
    main()
