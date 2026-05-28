from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routers import export, health, results, simulation

app = FastAPI(
    title="Blockchain IoT Trust Simulation API",
    description=(
        "API for launching blockchain-IoT trust simulations, "
        "streaming live step events, replaying completed runs, and browsing saved results."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(simulation.router)
app.include_router(results.router)
app.include_router(export.router)

dashboard_dist = Path("dashboard/dist")
assets_dir = dashboard_dist / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="dashboard-assets")


@app.get("/", include_in_schema=False)
async def serve_dashboard_index():
    """Serve the built dashboard SPA when available, otherwise fall back to a small API message."""
    index_path = dashboard_dist / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Dashboard build not found. Use /docs for API docs."}


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_dashboard_spa(full_path: str):
    """Serve the built dashboard SPA for client-side routes while preserving API endpoints."""
    if full_path.startswith(("health", "docs", "openapi.json", "simulation", "results", "redoc")):
        return {"detail": "Not Found"}
    index_path = dashboard_dist / "index.html"
    requested = dashboard_dist / full_path
    if requested.exists() and requested.is_file():
        return FileResponse(requested)
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Dashboard build not found. Use /docs for API docs."}
