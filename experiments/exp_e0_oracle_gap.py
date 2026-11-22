"""E0: how much does oracle access overstate performance?

Re-creates, *inside this experiment script only*, the oracle feedback of the pre-audit simulator
(simulation_manager.py:440-446 @ c8bab2f): every 15 steps, each true adversary gets a "malicious"
trust update and each true honest node a "valid" update, each with probability 0.7.  Everything
else (votes, audits, tally) is the honest environment.  The comparison is paired on seeds:
legacy Beta with vs without the oracle injection.  The oracle code deliberately lives outside src/.
"""
from __future__ import annotations

import itertools
import time
from typing import Any, Dict

from experiments.common import base_parser, out_dir, parse_seeds, run_parallel, write
from src.config.run_config import RunConfig
from src.env.honest_env import HonestEnv
from src.metrics.ground_truth_metrics import summarize


class OracleLeakEnv(HonestEnv):
    """HonestEnv + the old ground-truth trust injection (for measurement only)."""

    def step(self, knobs=None):  # type: ignore[override]
        rec = super().step(knobs)
        s = rec.step
        if s % 15 == 0 and hasattr(self.trust, "tm"):
            labels = self._world.coalition  # ORACLE: this is exactly the flaw being measured
            for n in self.nodes:
                if self.rng.random() < 0.7:
                    self.trust.tm.update_trust(n, "malicious" if n in labels else "valid")
        return rec


def _run(job: Dict[str, Any]) -> Dict[str, Any]:
    cfg = RunConfig().with_overrides(**job["cfg"])
    env = (OracleLeakEnv if job["tags"]["oracle"] else HonestEnv)(cfg).run()
    row = dict(job["tags"], seed=cfg.seed)
    row.update(summarize(env))
    return row


def main() -> None:
    args = base_parser("E0 oracle gap", "100-129").parse_args()
    seeds = parse_seeds(args.seeds)
    steps = 600
    if args.smoke:
        seeds, steps = seeds[:3], 200
    t0 = time.time()
    jobs = [{"cfg": dict(seed=s, steps=steps, t_switch=steps // 2, attack=a, honest_fault_rate=0.05,
                         trust_backend="legacy_beta"),
             "tags": dict(attack=a, oracle=o)}
            for a, o, s in itertools.product(("tdp", "cra", "nma", "aaa", "bfi"), (False, True), seeds)]
    rows = run_parallel(_run, jobs, args.workers)
    write("e0_oracle_gap", out_dir("e0_oracle_gap", args), rows, args, t0=t0)


if __name__ == "__main__":
    main()
