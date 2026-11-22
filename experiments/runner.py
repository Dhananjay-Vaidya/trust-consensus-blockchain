"""Picklable single-run worker shared by the experiments."""
from __future__ import annotations

import json
import sys
import tracemalloc
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config.run_config import RunConfig  # noqa: E402
from src.env.honest_env import HonestEnv  # noqa: E402
from src.metrics.ground_truth_metrics import summarize  # noqa: E402

CALIBRATION_FILE = ROOT / "results" / "raw" / "calibration" / "selected.json"


def calibrated_sg(honest_fault_rate: float) -> Dict[str, Any]:
    """SleeperGuard overrides chosen on CALIB_SEEDS for the nominal honest fault rate.
    Falls back to the verified defaults (and says so) if calibration has not been run."""
    if not CALIBRATION_FILE.exists():
        return {}
    sel = json.loads(CALIBRATION_FILE.read_text())
    key = f"{honest_fault_rate:.2f}"
    if key not in sel:
        # nearest calibrated fault rate (documented: misspecification is studied in E7)
        key = min(sel, key=lambda k: abs(float(k) - honest_fault_rate))
    return {f"sg_{k}": v for k, v in sel[key].items()}


def run_one(job: Dict[str, Any]) -> Dict[str, Any]:
    """job: {'cfg': dict of RunConfig overrides, 'tags': dict copied to the output row,
             'measure_memory': bool}"""
    cfg = RunConfig().with_overrides(**job["cfg"])
    mem = job.get("measure_memory", False)
    if mem:
        tracemalloc.start()
    env = HonestEnv(cfg).run()
    row: Dict[str, Any] = dict(job.get("tags", {}))
    row.update({"seed": cfg.seed})
    row.update(summarize(env, window_start=job.get("window_start")))
    if mem:
        row["peak_mem_mb"] = tracemalloc.get_traced_memory()[1] / 1e6
        tracemalloc.stop()
    return row
