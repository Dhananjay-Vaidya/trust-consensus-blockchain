from __future__ import annotations

from pathlib import Path
import re
from typing import List

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from src.api.models import CompareRunsResponse, ResultRunMetadata

router = APIRouter(prefix="/results", tags=["results"])
RESULTS_DIR = Path("experiments/results")


def _candidate_run_ids(run_id: str) -> list[str]:
    candidates = [run_id]
    stripped = re.sub(r"_seed\d+$", "", run_id)
    if stripped != run_id:
        candidates.append(stripped)
    else:
        seed_matches = sorted(RESULTS_DIR.glob(f"{run_id}_seed*_episode_metrics.csv"))
        candidates.extend(file.name.replace("_episode_metrics.csv", "") for file in seed_matches)
    seen: list[str] = []
    for item in candidates:
        if item not in seen:
            seen.append(item)
    return seen


def _resolve_metrics_csv(run_id: str) -> Path | None:
    for candidate in _candidate_run_ids(run_id):
        csv_path = RESULTS_DIR / f"{candidate}_episode_metrics.csv"
        if csv_path.exists():
            return csv_path
    return None


def _parse_prefix(name: str) -> dict:
    """Parse the conventional metrics filename prefix into a metadata dictionary."""
    base = name.replace("_episode_metrics.csv", "")
    parts = base.split("_")
    if len(parts) >= 5:
        return {"nodes": parts[0], "episodes": parts[1], "agent": parts[2], "attack": parts[3]}
    return {}


@router.get(
    "",
    response_model=List[ResultRunMetadata],
    summary="List completed run result files",
    description="Browse all completed simulation runs discovered from `experiments/results/*_episode_metrics.csv`.",
)
async def list_results():
    """Return completed run metadata discovered from saved episode metrics CSVs."""
    if not RESULTS_DIR.exists():
        return []
    rows: list[ResultRunMetadata] = []
    for file in sorted(RESULTS_DIR.glob("*_episode_metrics.csv")):
        info = _parse_prefix(file.name)
        if not info:
            continue
        run_id = file.name.replace("_episode_metrics.csv", "")
        final_f1 = None
        episodes = 0
        try:
            df = pd.read_csv(file)
            col = "F1 Score" if "F1 Score" in df.columns else df.columns[2]
            final_f1 = float(df[col].iloc[-1])
            episodes = len(df)
        except Exception:
            pass
        rows.append(
            ResultRunMetadata(
                run_id=run_id,
                agent=info.get("agent"),
                attack=info.get("attack"),
                nodes=info.get("nodes"),
                final_f1=final_f1,
                episodes=episodes,
                completed_at=file.stat().st_mtime,
                filename=file.name,
            )
        )
    return rows


@router.get(
    "/{run_id}/metrics",
    summary="Load a run's episode metrics",
    description="Read the episode metrics CSV for a completed run and return row-wise metric objects.",
)
async def get_metrics(run_id: str):
    """Return the raw episode metrics rows for a completed run."""
    csv_path = _resolve_metrics_csv(run_id)
    if csv_path is None:
        raise HTTPException(status_code=404, detail="Metrics CSV not found")
    return pd.read_csv(csv_path).to_dict(orient="records")


@router.get(
    "/{run_id}/download",
    summary="Download a run's episode metrics CSV",
    description="Serve the raw episode metrics CSV file for a completed run.",
)
async def download_metrics(run_id: str):
    """Return the episode metrics CSV file as a download response."""
    csv_path = _resolve_metrics_csv(run_id)
    if csv_path is None:
        raise HTTPException(status_code=404, detail="Metrics CSV not found")
    return FileResponse(path=str(csv_path), media_type="text/csv", filename=csv_path.name)


@router.get(
    "/compare",
    response_model=CompareRunsResponse,
    summary="Compare metrics across multiple runs",
    description="Return a per-run metric series and the corresponding final values for the selected run ids.",
)
async def compare_runs(
    run_ids: str = Query(..., description="Comma-separated run ids to compare.", examples=["16_50_marl_cra_30,16_50_drl_cra_30"]),
    metric: str = Query("F1 Score", description="Metric column to compare across runs.", examples=["F1 Score"]),
):
    """Return aligned metric series for multiple saved runs."""
    ids = [item.strip() for item in run_ids.split(",") if item.strip()]
    series: dict[str, list[float]] = {}
    finals: dict[str, float | None] = {}
    for run_id in ids:
        csv_path = _resolve_metrics_csv(run_id)
        if csv_path is None:
            series[run_id] = []
            finals[run_id] = None
            continue
        try:
            df = pd.read_csv(csv_path)
            column = next((c for c in df.columns if metric.lower() in c.lower()), None)
            values = df[column].tolist() if column else []
            series[run_id] = values
            finals[run_id] = float(values[-1]) if values else None
        except Exception:
            series[run_id] = []
            finals[run_id] = None
    return CompareRunsResponse(metric=metric, series=series, finals=finals)
