"""E14 diagnostic: why do fixed-reference detectors beat SleeperGuard against the stealthy sleeper?

SleeperGuard's CUSUM reference is mu0 = max(baseline_floor, 1 - slow-Beta mean) per node, i.e. it adapts to the
node's own long-run disagreement rate.  Hypothesis: for a sleeper that keeps lying at a low rate, mu0 rises towards
the sleeper's own rate, so the CUSUM stops re-alarming after the first quarantines; a fixed-reference CUSUM keeps
alarming.  Measured on eval seeds 100-129: alarms per sleeper after activation and SleeperGuard's mu0 for sleepers
and honest nodes at the end of the run (stealthy sleeper, 4 of 16, t_switch 300, f = 0.05, calibrated parameters).
Output: results/raw/e14_baselines/mechanism.json
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from experiments.common import RAW, base_parser, parse_seeds
from experiments.runner import calibrated_sg
from src.config.run_config import RunConfig
from src.env.honest_env import HonestEnv
from src.metrics.ground_truth_metrics import node_labels


def main() -> None:
    args = base_parser("E14 mechanism diagnostic", "100-129").parse_args()
    seeds = parse_seeds(args.seeds)[:3] if args.smoke else parse_seeds(args.seeds)
    d = RAW / ("e14_baselines" + ("_smoke" if args.smoke else ""))
    cal = pd.read_csv(d / "calibration.csv")
    cu = json.loads(cal[(cal.method == "cusum") & (cal.fault == 0.05)].params.iloc[0])
    out = {}
    for name, ov in (("sg_full", dict(trust_backend="sleeper_guard", **calibrated_sg(0.05))),
                     ("cusum", dict(trust_backend="cusum", **cu))):
        al, mu_s, mu_h = [], [], []
        for seed in seeds:
            env = HonestEnv(RunConfig().with_overrides(seed=seed, steps=600, t_switch=300, attack="tdp",
                                                        attack_intensity=0.25, malicious_fraction=0.25,
                                                        honest_fault_rate=0.05, **ov)).run()
            lab = node_labels(env, len(env.records) - 1)
            sl, hn = set(np.flatnonzero(lab).tolist()), np.flatnonzero(~lab)
            al.append(sum(1 for r in env.records[300:] for a in r.alarms if a in sl) / max(1, len(sl)))
            if name == "sg_full":
                g = env.trust.sg  # type: ignore[attr-defined]

                def mu0(i: int) -> float:
                    n = env.nodes[i]
                    return max(g.cfg.baseline_floor, 1.0 - g._mean(g.a_slow[n], g.b_slow[n]))
                mu_s.append(float(np.mean([mu0(i) for i in sl])))
                mu_h.append(float(np.mean([mu0(i) for i in hn])))
        out[name] = dict(alarms_per_sleeper_after_switch=float(np.mean(al)),
                         sleeper_mu0_end=float(np.mean(mu_s)) if mu_s else None,
                         honest_mu0_end=float(np.mean(mu_h)) if mu_h else None, seeds=len(seeds))
    out["cusum_reference"] = cu.get("det_reference")
    out["sg_cusum_slack"] = calibrated_sg(0.05).get("sg_cusum_slack")
    (d / "mechanism.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
