"""Export endpoints for figures, CSVs, and LaTeX tables."""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, Response, StreamingResponse

router = APIRouter(prefix="/export", tags=["export"])

RESULTS_DIR = Path("experiments/results")


@router.get("/results", summary="Download all results as a ZIP of CSVs")
async def export_results():
    """Return a ZIP archive of all episode-metrics CSV files."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        if RESULTS_DIR.exists():
            for csv in RESULTS_DIR.glob("*_episode_metrics.csv"):
                zf.write(csv, csv.name)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=results.zip"},
    )


PAPER_RAW = Path("results/raw")
PAPER_GEN = Path("paper/generated")
PAPER_FIGS = Path("paper/figs")


def _zip(paths, name: str) -> StreamingResponse:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in paths:
            zf.write(p, p.as_posix())
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/zip",
                             headers={"Content-Disposition": f"attachment; filename={name}"})


@router.get("/statistics", summary="Download the paired-statistics CSVs (Wilcoxon/Holm/bootstrap/Cliff)")
async def export_statistics():
    files = sorted((PAPER_RAW / "stats").glob("*.csv")) if (PAPER_RAW / "stats").exists() else []
    if not files:
        return Response(content="Statistics not available: run python paper/make_assets.py", status_code=404)
    return _zip(files, "statistics.zip")


@router.get("/latex_table", summary="Download the generated LaTeX tables")
async def export_latex_table():
    files = sorted(PAPER_GEN.glob("tab_*.tex")) if PAPER_GEN.exists() else []
    if not files:
        return Response(content="LaTeX tables not available: run python paper/make_assets.py", status_code=404)
    return FileResponse(files[0], media_type="text/plain") if len(files) == 1 else _zip(files, "tables.zip")


@router.get("/figures", summary="Export the paper figures (vector PDF) as a ZIP")
async def export_figures():
    files = sorted(PAPER_FIGS.glob("*.pdf")) if PAPER_FIGS.exists() else []
    if not files:
        return Response(content="Figures not available: run python paper/make_assets.py", status_code=404)
    return _zip(files, "figures.zip")
