"""Existing API endpoints still work on top of the honest environment."""
from __future__ import annotations

import time

from fastapi.testclient import TestClient

import src.api.simulation_runner as runner

from src.api.main import app

runner.STEP_DELAY_S = 0.0


def test_start_status_and_stream_endpoints():
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        body = {"agent": "drl", "attack": "tdp", "consensus": "tdcb", "nodes": 8, "episodes": 2,
                "steps_per_episode": 20, "malicious_fraction": 0.25, "seed": 7,
                "trust_backend": "sleeper_guard", "tally_backend": "plain"}
        r = client.post("/simulation/start", json=body)
        assert r.status_code == 200, r.text
        run_id = r.json()["run_id"]
        for _ in range(2400):
            st = client.get(f"/simulation/{run_id}/status").json()
            if st["status"] != "running":
                break
            time.sleep(0.05)
        assert st["status"] == "completed", st
        assert client.get("/results/").status_code == 200


def test_baseline_consensus_and_legacy_backend_run():
    with TestClient(app) as client:
        body = {"agent": "rl", "attack": "cra", "consensus": "pbft", "nodes": 8, "episodes": 1,
                "steps_per_episode": 10, "malicious_fraction": 0.25, "seed": 8, "trust_backend": "legacy_beta"}
        run_id = client.post("/simulation/start", json=body).json()["run_id"]
        for _ in range(2400):
            st = client.get(f"/simulation/{run_id}/status").json()
            if st["status"] != "running":
                break
            time.sleep(0.05)
        assert st["status"] == "completed", st
