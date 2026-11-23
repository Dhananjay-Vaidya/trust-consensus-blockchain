"""E13: the sleeper (TDP) experiment under the preprint's protocol, for a like-for-like comparison.

Preprint protocol (arXiv:2512.22860; pre-audit simulator @ c8bab2f, config/default.yaml):
  16 nodes, MALICIOUS_RATIO 0.30 -> int(16 * 0.30) = 4 adversarial nodes (the old code truncated; we
  therefore use malicious_fraction = 0.25, which gives exactly 4), 50 episodes x 100 steps with trust
  carried across episodes, sleepers activate at episode 25 (0-indexed, i.e. from episode 26 on),
  attack intensity 0.75, F1 computed at the END of each episode with static labels (a sleeper counts as
  malicious even while dormant).
Here: one continuous HonestEnv run of 5000 steps (t_switch = 2500), honest fault 0.05, legacy Beta and
SleeperGuard (calibrated), evaluation seeds 100-129.  Scored per 100-step episode with static labels
(preprint-style) and with active labels (D5).
Outputs: results/raw/e13_preprint_protocol/{episodes.csv, runs.csv, meta.json}
"""
from __future__ import annotations

import itertools
import time
from typing import Any, Dict, List

import numpy as np

from experiments.common import base_parser, out_dir, parse_seeds, run_parallel, write
from experiments.runner import calibrated_sg
from src.config.run_config import RunConfig
from src.env.honest_env import HonestEnv
from src.metrics.ground_truth_metrics import episode_snapshot_scores

EPISODES, EP_LEN, ACTIVATION_EP = 50, 100, 25


def _run(job: Dict[str, Any]) -> Dict[str, Any]:
    cfg = RunConfig().with_overrides(**job["cfg"])
    env = HonestEnv(cfg).run()
    st = episode_snapshot_scores(env, job["ep_len"], static_labels=True)
    ac = episode_snapshot_scores(env, job["ep_len"], static_labels=False)
    act = job["activation_ep"]
    eps = [dict(job["tags"], seed=cfg.seed, episode=a["episode"], f1_static=a["f1"], f1_active=b["f1"],
                precision_static=a["precision"], recall_static=a["recall"], mcc_static=a["mcc"])
           for a, b in zip(st, ac)]
    pre = [e["f1_static"] for e in eps if e["episode"] <= act]
    post = [e["f1_static"] for e in eps if e["episode"] > act]
    post_active = [e["f1_active"] for e in eps if e["episode"] > act]
    row = dict(job["tags"], seed=cfg.seed, n_adversary=len(env._world.coalition),
               f1_pre_mean=float(np.mean(pre)), f1_post_mean=float(np.mean(post)),
               f1_post_active_mean=float(np.mean(post_active)), f1_final=eps[-1]["f1_static"])
    return {"row": row, "episodes": eps}


def main() -> None:
    args = base_parser("E13 preprint protocol", "100-129").parse_args()
    seeds, episodes, ep_len, act = parse_seeds(args.seeds), EPISODES, EP_LEN, ACTIVATION_EP
    if args.smoke:
        seeds, episodes, ep_len, act = seeds[:3], 10, 50, 5
    t0 = time.time()
    jobs = []
    for be, s in itertools.product(("legacy_beta", "sleeper_guard"), seeds):
        tb = dict(trust_backend="sleeper_guard", **calibrated_sg(0.05)) if be == "sleeper_guard" else dict(trust_backend="legacy_beta")
        jobs.append({"cfg": dict(tb, seed=s, num_nodes=16, committee_size=16, malicious_fraction=0.25,
                                 steps=episodes * ep_len, t_switch=act * ep_len, attack="tdp",
                                 attack_intensity=0.75, honest_fault_rate=0.05),
                     "tags": dict(backend=be), "ep_len": ep_len, "activation_ep": act})
    res = run_parallel(_run, jobs, args.workers)
    d = out_dir("e13_preprint_protocol", args)
    eps: List[Dict[str, Any]] = [e for r in res for e in r["episodes"]]
    write("e13_preprint_protocol", d, eps, args, name="episodes.csv")
    write("e13_preprint_protocol", d, [r["row"] for r in res], args, name="runs.csv", t0=t0,
          extra_meta={"protocol": dict(nodes=16, adversaries=4, episodes=episodes, episode_len=ep_len,
                                       activation_episode=act, intensity=0.75,
                                       note="int(16*0.30)=4 adversaries as in the pre-audit code")})


if __name__ == "__main__":
    main()
