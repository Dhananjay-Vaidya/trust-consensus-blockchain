"""Export endpoints for figures, CSVs, and LaTeX tables."""
from __future__ import annotations

import io
import os
import tempfile
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


@router.get("/statistics", summary="Download statistical analysis report CSV")
async def export_statistics():
    """Generate and return the statistical analysis table as CSV."""
    output_path = Path("new_res/statistical_table.csv")
    if not output_path.exists():
        try:
            from analysis.statistical_analysis import generate_results_table
            generate_results_table(
                str(RESULTS_DIR), "new_res",
                nodes=16, episodes=50,
            )
        except Exception as e:
            return Response(content=f"Error generating statistics: {e}", status_code=500)
    if output_path.exists():
        return FileResponse(str(output_path), media_type="text/csv", filename="statistical_table.csv")
    return Response(content="Statistics not available", status_code=404)


@router.get("/latex_table", summary="Download LaTeX results table")
async def export_latex_table():
    """Generate and return the LaTeX results table."""
    output_path = Path("new_res/statistical_table.tex")
    if not output_path.exists():
        try:
            from analysis.statistical_analysis import generate_results_table
            generate_results_table(
                str(RESULTS_DIR), "new_res",
                nodes=16, episodes=50,
            )
        except Exception as e:
            return Response(content=f"Error generating LaTeX table: {e}", status_code=500)
    if output_path.exists():
        return FileResponse(str(output_path), media_type="text/plain", filename="results_table.tex")
    return Response(content="LaTeX table not available", status_code=404)


@router.get("/figures", summary="Export paper figures as a ZIP")
async def export_figures(
    figures: str = "1,2,3",
    format: str = "png",
):
    """Generate requested paper figures and return them as a ZIP file."""
    import matplotlib
    matplotlib.use("Agg")

    requested = [f.strip() for f in figures.split(",") if f.strip()]
    buf = io.BytesIO()

    with tempfile.TemporaryDirectory() as tmpdir:
        generated: list[Path] = []
        try:
            import generate_paper_figures as gpf
            func_map = {
                "1": getattr(gpf, "figure1_f1_scores", None),
                "2": getattr(gpf, "figure2_trust_separation", None),
                "3": getattr(gpf, "figure8_baseline_comparison", None),
                "4": getattr(gpf, "figure9_ablation_study", None),
                "5": getattr(gpf, "figure10_scalability", None),
                "6": getattr(gpf, "figure11_malicious_sweep", None),
            }
            for fig_id in requested:
                fn = func_map.get(fig_id)
                if fn:
                    try:
                        fn()
                        for ext in ["png", "svg", "pdf"]:
                            for candidate in Path("new_res").glob(f"figure{fig_id}*.{ext}"):
                                if candidate.exists():
                                    generated.append(candidate)
                    except Exception:
                        pass
        except ImportError:
            pass

        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for fig_path in generated:
                zf.write(fig_path, fig_path.name)
            if not generated:
                zf.writestr("README.txt", f"No figures generated for: {figures}\nRun simulations first.")

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=figures_{figures.replace(',','_')}.zip"},
    )
