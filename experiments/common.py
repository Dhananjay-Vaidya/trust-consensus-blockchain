"""Shared experiment plumbing: CLI, machine spec, parallel runs, result writing.

Every experiment writes ``results/raw/<exp>/runs.csv`` (one row per run), optional extra CSVs, and
``results/raw/<exp>/meta.json`` (machine spec, library versions, git commit, CLI, configs).
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

RAW = ROOT / "results" / "raw"


def parse_seeds(spec: str) -> List[int]:
    """'0-29' | '100-129' | '1,2,5' | '0-2,10'."""
    out: List[int] = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        elif part:
            out.append(int(part))
    return out


def base_parser(name: str, default_seeds: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=name)
    p.add_argument("--seeds", default=default_seeds, help="e.g. 100-129 or 1,2,3")
    p.add_argument("--smoke", action="store_true", help="3 seeds, shortened runs (CI)")
    p.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    p.add_argument("--out", default=None, help="output dir (default results/raw/<exp>)")
    return p


def _cpu_model() -> str:
    """Marketing CPU name (platform.processor() only gives the family/model code on Windows)."""
    try:
        if sys.platform.startswith("win"):
            out = subprocess.run(["powershell", "-NoProfile", "-Command",
                                  "(Get-CimInstance Win32_Processor).Name"], capture_output=True, text=True, timeout=20)
            name = out.stdout.strip().splitlines()[0].strip() if out.stdout.strip() else ""
            if name:
                return name
        elif sys.platform == "darwin":
            return subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True).stdout.strip()
        else:
            for line in open("/proc/cpuinfo", encoding="utf-8"):
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return platform.processor()


def machine_spec() -> Dict[str, Any]:
    import numpy
    import scipy
    import sklearn
    import torch

    spec: Dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "numpy": numpy.__version__, "scipy": scipy.__version__,
        "sklearn": sklearn.__version__, "torch": torch.__version__, "pandas": pd.__version__,
    }
    spec["cpu_model"] = _cpu_model()
    try:
        import psutil
        spec["ram_gb"] = round(psutil.virtual_memory().total / 1e9, 2)
        spec["physical_cores"] = psutil.cpu_count(logical=False)
    except Exception:  # pragma: no cover
        spec["ram_gb"] = None
    try:
        import tenseal
        spec["tenseal"] = tenseal.__version__
    except Exception:  # pragma: no cover
        spec["tenseal"] = None
    try:
        spec["git_commit"] = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                                            text=True).stdout.strip()
        spec["git_dirty"] = bool(subprocess.run(["git", "status", "--porcelain", "--", "src", "experiments"],
                                                cwd=ROOT, capture_output=True, text=True).stdout.strip())
    except Exception:  # pragma: no cover
        spec["git_commit"] = None
    return spec


def out_dir(exp: str, args: argparse.Namespace) -> Path:
    d = Path(args.out) if args.out else RAW / (exp + ("_smoke" if args.smoke else ""))
    d.mkdir(parents=True, exist_ok=True)
    return d


def run_parallel(fn: Callable[[Dict[str, Any]], Dict[str, Any]], jobs: Sequence[Dict[str, Any]],
                 workers: int) -> List[Dict[str, Any]]:
    if workers <= 1 or len(jobs) <= 1:
        return [fn(j) for j in jobs]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(fn, jobs, chunksize=max(1, len(jobs) // (workers * 4))))


def write(exp: str, d: Path, rows: Iterable[Dict[str, Any]], args: argparse.Namespace,
          extra_meta: Dict[str, Any] | None = None, name: str = "runs.csv", t0: float | None = None) -> Path:
    df = pd.DataFrame(list(rows))
    path = d / name
    df.to_csv(path, index=False)
    meta_path = d / "meta.json"
    meta: Dict[str, Any] = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    meta.update({
        "experiment": exp,
        "argv": sys.argv,
        "machine": machine_spec(),
        "written": time.strftime("%Y-%m-%dT%H:%M:%S"),
    })
    if t0 is not None:
        meta.setdefault("runtime_s", {})[name] = round(time.time() - t0, 1)
    if extra_meta:
        meta.update(extra_meta)
    meta_path.write_text(json.dumps(meta, indent=2, default=str))
    print(f"[{exp}] wrote {path} ({len(df)} rows)")
    return path
