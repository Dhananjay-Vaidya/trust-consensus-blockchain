from __future__ import annotations

import glob
import json
import os
import re
from pathlib import Path
from typing import List, Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

router = APIRouter(prefix="/results", tags=["results"])


def _parse_prefix(name: str) -> dict:
    """Parse {nodes}_{episodes}_{agent}_{attack}_{pct}_episode_metrics.csv"""
    base = name.replace("_episode_metrics.csv", "")
    parts = base.split("_")
    if len(parts) >= 5:
        return {
            "nodes": parts[0],
            "episodes": parts[1],
            "agent": parts[2],
            "attack": parts[3],
        }
    return {}


@router.get("/")
async def list_results():
    results_dir = Path("results")
    if not results_dir.exists():
        return []
    rows = []
    for f in sorted(results_dir.glob("*_episode_metrics.csv")):
        info = _parse_prefix(f.name)
        if not info:
            continue
        # Derive run_id from filename stem (without _episode_metrics)
        run_id = f.name.replace("_episode_metrics.csv", "")
        final_f1 = None
        try:
            df = pd.read_csv(f)
            col = "F1 Score" if "F1 Score" in df.columns else df.columns[2]
            final_f1 = float(df[col].iloc[-1])
            episodes = len(df)
        except Exception:
            episodes = 0
        rows.append({
            "run_id": run_id,
            "agent": info.get("agent"),
            "attack": info.get("attack"),
            "nodes": info.get("nodes"),
            "final_f1": final_f1,
            "episodes": episodes,
            "completed_at": f.stat().st_mtime,
            "filename": f.name,
        })
    return rows


@router.get("/{run_id}/metrics")
async def get_metrics(run_id: str):
    csv_path = Path("results") / f"{run_id}_episode_metrics.csv"
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="Metrics CSV not found")
    df = pd.read_csv(csv_path)
    return df.to_dict(orient="records")


@router.get("/{run_id}/download")
async def download_metrics(run_id: str):
    csv_path = Path("results") / f"{run_id}_episode_metrics.csv"
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="Metrics CSV not found")
    return FileResponse(path=str(csv_path), media_type="text/csv",
                        filename=csv_path.name)


@router.get("/compare")
async def compare_runs(
    run_ids: str = Query(..., description="Comma-separated run IDs"),
    metric: str = Query("F1 Score"),
):
    """Return {run_id: [episode_values]} for the requested metric."""
    ids = [r.strip() for r in run_ids.split(",") if r.strip()]
    result = {}
    for rid in ids:
        csv_path = Path("results") / f"{rid}_episode_metrics.csv"
        if not csv_path.exists():
            result[rid] = []
            continue
        try:
            df = pd.read_csv(csv_path)
            col = None
            for c in df.columns:
                if metric.lower() in c.lower():
                    col = c
                    break
            result[rid] = df[col].tolist() if col else []
        except Exception:
            result[rid] = []
    return result
