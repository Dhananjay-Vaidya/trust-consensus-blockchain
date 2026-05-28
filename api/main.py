from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routers import health, simulation, results

app = FastAPI(
    title="Blockchain IoT Trust Simulation API",
    description="Real-time simulation streaming and results API",
    version="1.0.0",
)

# CORS: allow all origins so the React dev server (port 3000) can connect
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

# Serve built React app at /app if dashboard/dist exists
_dashboard_dist = Path("dashboard/dist")
if _dashboard_dist.exists():
    app.mount("/app", StaticFiles(directory=str(_dashboard_dist), html=True), name="dashboard")


@app.get("/health")
async def root_health():
    from api import simulation_runner as runner
    active = len([r for r in runner._runs.values() if r["status"] == "running"])
    return {"status": "ok", "active_runs": active}
