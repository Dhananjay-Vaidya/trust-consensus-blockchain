"""E13: the sleeper (TDP) experiment under the preprint's protocol, without the oracle.

Protocol facts were established from the pre-audit code at commit c8bab2f (docs/DECISIONS.md D23):
  adversaries   int(16 * 0.30) = 4                     (simulation_manager.py:217)
  episodes      100 for TDP, 100 steps each             (results_summary.csv TDP rows; default.yaml:22)
  activation    episode index 25 (dormant while idx<25) (tdp_attack.py:67, attack_util.py:89)
  intensity     0.75                                    (attack_util.py:90, default.yaml:32)
  flag rule     trust < 0.45, no quarantine concept     (simulation_manager.py:723, default.yaml:11)
  reported F1   LAST episode only (iloc[-1])            (_generate_paper_figures_impl.py:529)
  labels        static: a sleeper is positive while dormant (simulation_manager.py:724)

Variants (one run per (adversaries, episodes, backend, seed); threshold and window are scoring-only):
  E13a_as_before       4 adversaries, 50 episodes, threshold 0.5 (+quarantine), all active episodes
  E13b_preprint_exact  4 adversaries, 100 episodes, threshold 0.45, final episode (code as run)
  grid                 adversaries {4,5} x episodes {50,100} x threshold {0.45,0.5}
                       x window {all_active, final10, final1}
Same seeds (100-129) and honest fault rate (0.05) for legacy Beta and SleeperGuard (calibrated).
Outputs: results/raw/e13_preprint_protocol/{episodes.csv, runs.csv, grid.csv, meta.json}
"""
from __future__ import annotations

import itertools
import time
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from experiments.common import base_parser, out_dir, parse_seeds, run_parallel, write
from experiments.runner import calibrated_sg
from src.config.run_config import RunConfig
from src.env.honest_env import HonestEnv
from src.metrics.ground_truth_metrics import episode_snapshot_scores
from src.stats.paired import bootstrap_ci

EP_LEN, ACTIVATION_EP, INTENSITY, FAULT = 100, 25, 0.75, 0.05
ADVERSARIES = (4, 5)
EPISODES = (50, 100)
THRESHOLDS = (0.45, 0.5)
WINDOWS = ("all_active", "final10", "final1")
# malicious_fraction realising each count under the environment's round(): 4/16 and 5/16 exactly
FRACTION = {4: 0.25, 5: 0.3125}
VARIANTS = {
    "E13a_as_before": dict(adversaries=4, episodes=50, threshold=0.5, window="all_active"),
    "E13b_preprint_exact": dict(adversaries=4, episodes=100, threshold=0.45, window="final1"),
}


def _window(eps: List[Dict[str, float]], window: str, act: int) -> List[Dict[str, float]]:
    active = [e for e in eps if e["episode"] > act]
    if window == "all_active":
        return active
    if window == "final10":
        return eps[-10:]
    return eps[-1:]


def _run(job: Dict[str, Any]) -> Dict[str, Any]:
    cfg = RunConfig().with_overrides(**job["cfg"])
    env = HonestEnv(cfg).run()
    n_adv = len(env._world.coalition)
    assert n_adv == job["adversaries"], f"realised {n_adv} adversaries, wanted {job['adversaries']}"
    act, ep_len = job["activation_ep"], job["ep_len"]
    eps_rows, run_rows = [], []
    for thr in job["thresholds"]:
        st = episode_snapshot_scores(env, ep_len, static_labels=True, flag_threshold=thr)
        ac = episode_snapshot_scores(env, ep_len, static_labels=False, flag_threshold=thr)
        for a, b in zip(st, ac):
            eps_rows.append(dict(job["tags"], seed=cfg.seed, threshold=thr, episode=a["episode"],
                                 f1_static=a["f1"], f1_active=b["f1"], precision_static=a["precision"],
                                 recall_static=a["recall"], mcc_static=a["mcc"]))
        post = [e for e in st if e["episode"] > act]
        hit = next((e["episode"] for e in post if e["f1"] >= 0.5), None)
        for w in job["windows"]:
            sel = _window(st, w, act)
            run_rows.append(dict(job["tags"], seed=cfg.seed, threshold=thr, window=w, n_adversary=n_adv,
                                 f1=float(np.mean([e["f1"] for e in sel])),
                                 f1_pre_mean=float(np.mean([e["f1"] for e in st if e["episode"] <= act])),
                                 first_detect_episode=float(hit) if hit is not None else float("nan"),
                                 detected=hit is not None))
    return {"episodes": eps_rows, "runs": run_rows}


def _ci(x: pd.Series) -> str:
    x = x.dropna()
    if x.empty:
        return "n/a"
    lo, hi = bootstrap_ci(x.values)
    return f"{np.median(x):.3f} [{lo:.3f}, {hi:.3f}]"


def main() -> None:
    args = base_parser("E13 preprint protocol", "100-129").parse_args()
    seeds, episodes, ep_len, act = parse_seeds(args.seeds), EPISODES, EP_LEN, ACTIVATION_EP
    variants = VARIANTS
    if args.smoke:
        seeds, episodes, ep_len, act = seeds[:3], (10,), 50, 5
        variants = {k: dict(v, episodes=10) for k, v in VARIANTS.items()}
    t0 = time.time()
    jobs = []
    for adv, n_ep, be, s in itertools.product(ADVERSARIES, episodes, ("legacy_beta", "sleeper_guard"), seeds):
        tb = dict(trust_backend="sleeper_guard", **calibrated_sg(FAULT)) if be == "sleeper_guard" else dict(trust_backend="legacy_beta")
        jobs.append({"cfg": dict(tb, seed=s, num_nodes=16, committee_size=16, malicious_fraction=FRACTION[adv],
                                 steps=n_ep * ep_len, t_switch=act * ep_len, attack="tdp",
                                 attack_intensity=INTENSITY, honest_fault_rate=FAULT),
                     "tags": dict(backend=be, adversaries=adv, episodes=n_ep),
                     "adversaries": adv, "ep_len": ep_len, "activation_ep": act,
                     "thresholds": THRESHOLDS, "windows": WINDOWS})
    res = run_parallel(_run, jobs, args.workers)
    episodes_df = pd.DataFrame([e for r in res for e in r["episodes"]])
    runs = pd.DataFrame([x for r in res for x in r["runs"]])
    runs["variant"] = ""
    for name, v in variants.items():
        m = ((runs.adversaries == v["adversaries"]) & (runs.episodes == v["episodes"])
             & (runs.threshold == v["threshold"]) & (runs.window == v["window"]))
        runs.loc[m, "variant"] = name
    assert (runs.n_adversary == runs.adversaries).all()

    grid_rows = []
    for (adv, n_ep, thr, w), g in runs.groupby(["adversaries", "episodes", "threshold", "window"]):
        lg, sg = g[g.backend == "legacy_beta"], g[g.backend == "sleeper_guard"]
        grid_rows.append(dict(adversaries=adv, episodes=n_ep, threshold=thr, window=w,
                              legacy_f1_median=float(lg.f1.median()), legacy_f1=_ci(lg.f1),
                              sg_f1_median=float(sg.f1.median()), sg_f1=_ci(sg.f1),
                              legacy_first_detect=float(lg.first_detect_episode.median()),
                              sg_first_detect=float(sg.first_detect_episode.median()),
                              legacy_detected_runs=int(lg.detected.sum()), sg_detected_runs=int(sg.detected.sum()),
                              runs_per_backend=len(lg)))
    d = out_dir("e13_preprint_protocol", args)
    write("e13_preprint_protocol", d, episodes_df.to_dict("records"), args, name="episodes.csv")
    write("e13_preprint_protocol", d, grid_rows, args, name="grid.csv")
    write("e13_preprint_protocol", d, runs.to_dict("records"), args, name="runs.csv", t0=t0,
          extra_meta={"protocol": dict(nodes=16, episode_len=ep_len, activation_episode=act, intensity=INTENSITY,
                                       honest_fault_rate=FAULT, seeds=seeds, adversaries=list(ADVERSARIES),
                                       episodes=list(episodes), thresholds=list(THRESHOLDS), windows=list(WINDOWS),
                                       fractions={str(k): v for k, v in FRACTION.items()},
                                       sleeper_guard=calibrated_sg(FAULT), variants=variants,
                                       source="docs/DECISIONS.md D23 (pre-audit code @ c8bab2f)")})


if __name__ == "__main__":
    main()
