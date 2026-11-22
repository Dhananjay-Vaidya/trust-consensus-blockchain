"""Live simulation runner for the dashboard, backed by the oracle-free HonestEnv.

Endpoints and the event schema are unchanged; new optional fields report the honest metrics,
quarantine events and HE timing.  Each dashboard "episode" is a fresh ``HonestEnv`` with seed
``seed + episode`` (A8).  Learning agents (rl -> tabular Q, drl -> D3P, marl -> factored
independent learners) keep learning across episodes; no ground truth reaches them.
``is_malicious`` / F1 in events are post-hoc labels from ``src.metrics`` for display only.
Attack switches requested mid-run take effect at the next episode (attacks are part of the world).
"""
from __future__ import annotations

import asyncio
import json
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from src.api.models import RunMetadata, SimulationConfig, SimulationStatusResponse

MAX_CONCURRENT = 4
RESULTS_DIR = Path("experiments/results")

_runs: Dict[str, Dict[str, Any]] = {}
_threads: Dict[str, threading.Thread] = {}

_CONSENSUS_TO_BASELINE = {"tdcb": None, "pbft": "pbft", "static_dpos": "static_dpos",
                          "majority": "majority", "random": "random_delegates"}


def _build_run_id(cfg: SimulationConfig) -> str:
    malicious_pct = int(cfg.malicious_fraction * 100)
    return f"{cfg.nodes}_{cfg.episodes}_{cfg.agent}_{cfg.attack}_{malicious_pct}_seed{cfg.seed}"


def _make_run_state(run_id: str, cfg: SimulationConfig) -> Dict[str, Any]:
    return {
        "run_id": run_id, "config": cfg, "status": "running", "episode": 0,
        "total_episodes": cfg.episodes, "current_f1": 0.0, "current_reward": 0.0,
        "started_at": time.time(), "completed_at": None, "stop_flag": threading.Event(),
        "queue": None, "loop": None, "error": None, "paused": False,
    }


def _make_controller(agent: str, seed: int):
    from src.agents.d3p import D3PController
    from src.agents.factored import FactoredController
    from src.agents.simple import TabularQController

    return {"rl": TabularQController, "drl": D3PController, "marl": FactoredController}[agent](seed=seed)


def _base_config(cfg: SimulationConfig, attack: str, episode: int):
    from src.agents.baselines import BASELINES
    from src.config.run_config import RunConfig

    ov: Dict[str, Any] = dict(
        seed=cfg.seed + episode, num_nodes=cfg.nodes, committee_size=cfg.nodes,
        steps=cfg.steps_per_episode, t_switch=max(1, cfg.steps_per_episode // 2),
        malicious_fraction=cfg.malicious_fraction, attack=attack,
        trust_backend=cfg.trust_backend, tally_backend="he" if cfg.fhe_enabled else cfg.tally_backend,
        he_sign_iters=cfg.he_sign_iters,
    )
    b = _CONSENSUS_TO_BASELINE.get(cfg.consensus)
    if b is not None:
        ov.update(BASELINES[b])
        ov["committee_size"] = min(int(ov.get("committee_size", cfg.nodes)), cfg.nodes)
    return RunConfig().with_overrides(**ov)


def _run_simulation_thread(run_id: str, loop: asyncio.AbstractEventLoop, queue: asyncio.Queue) -> None:
    from src.env.honest_env import HonestEnv
    from src.metrics.ground_truth_metrics import display_labels, node_labels, summarize

    state = _runs[run_id]
    cfg: SimulationConfig = state["config"]
    stop: threading.Event = state["stop_flag"]
    ctrl = _make_controller(cfg.agent, cfg.seed) if cfg.consensus == "tdcb" else None
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    prefix = f"{cfg.nodes}_{cfg.episodes}_{cfg.agent}_{cfg.attack}_{int(cfg.malicious_fraction * 100)}"
    stream = open(RESULTS_DIR / f"{run_id}_stream.jsonl", "w", encoding="utf-8")
    ep_rows = []
    blocks = 0
    attack = cfg.attack

    def emit(ev: Dict[str, Any]) -> None:
        stream.write(json.dumps(ev) + "\n")
        stream.flush()
        if not stop.is_set():
            asyncio.run_coroutine_threadsafe(queue.put(ev), loop)

    try:
        for ep in range(cfg.episodes):
            if stop.is_set():
                raise InterruptedError("Simulation stopped by user")
            attack = state.pop("override_attack", None) or state.pop("inject_attack", None) or attack
            env = HonestEnv(_base_config(cfg, attack, ep))
            obs = env.observation()
            knobs = ctrl.act(obs, explore=True) if ctrl else None
            acc = []
            ep_reward = 0.0
            while not env.done:
                while state.get("paused") and not stop.is_set():
                    time.sleep(0.1)
                if stop.is_set():
                    raise InterruptedError("Simulation stopped by user")
                rec = env.step(knobs)
                acc.append(rec.reward)
                ep_reward += rec.reward
                blocks += int(rec.accept.any())
                if ctrl and (env.t % ctrl.control_every == 0 or env.done):
                    nobs = env.observation()
                    ctrl.observe_transition(obs, knobs, float(np.mean(acc)), nobs, env.done)
                    acc, obs = [], nobs
                    if not env.done:
                        knobs = ctrl.act(obs, explore=True)
                lab = node_labels(env, rec.step)
                tp = int((lab & rec.flagged).sum())
                prec = tp / max(1, int(rec.flagged.sum()))
                recall = tp / max(1, int(lab.sum())) if lab.any() else 0.0
                f1 = 2 * prec * recall / (prec + recall) if prec + recall > 0 else 0.0
                hon = ~np.array(list(display_labels(env).values()))
                sep = float(rec.trust[hon].mean() - rec.trust[~hon].mean()) if (~hon).any() and hon.any() else 0.0
                kn = rec.knobs
                emit({
                    "type": "step", "run_id": run_id, "episode": ep, "step": rec.step,
                    "trust_scores": {n: float(t) for n, t in zip(env.nodes, rec.trust)},
                    "is_malicious": display_labels(env),
                    "is_detected": {n: bool(f) for n, f in zip(env.nodes, rec.flagged)},
                    "delegate_nodes": [env.nodes[i] for i in rec.committee_idx],
                    "transactions_verified": int(rec.accept.sum()),
                    "transactions_rejected": int((~rec.accept).sum()),
                    "byzantine_detections": len(rec.alarms),
                    "f1_score": float(f1), "precision": float(prec), "recall": float(recall),
                    "reward": float(rec.reward), "blockchain_length": blocks, "trust_separation": sep,
                    "action_taken": 0,
                    "action_description": (f"k={len(rec.committee_idx)} audit={kn.audit_rate} "
                                           f"temp={kn.temperature} margin={kn.theta_margin:+.2f}"),
                    "fhe_overhead_ms": float(rec.he_ms) if (cfg.fhe_enabled or cfg.tally_backend == "he") else None,
                    "timestamp": time.time(),
                    # honest-metric extensions
                    "quarantined": [env.nodes[i] for i in np.flatnonzero(rec.quarantined)],
                    "quarantine_events": [env.nodes[i] for i in rec.alarms],
                    "audited": int(rec.n_audited),
                    "audited_error": None if np.isnan(rec.audited_err) else float(rec.audited_err),
                    "aborted": bool(rec.aborted),
                    "he_flips": int(rec.he_flips),
                    "trust_backend": cfg.trust_backend, "tally_backend": cfg.tally_backend,
                })
                state["episode"], state["current_f1"], state["current_reward"] = ep, f1, rec.reward
            m = summarize(env)
            ep_rows.append({"Episode": ep + 1, "Cumulative Reward": ep_reward, "F1 Score": m["det_f1"],
                            "Precision": m["det_precision"], "Recall": m["det_recall"], "MCC": m["det_mcc"],
                            "Blockchain Length": blocks, "Throughput": m["throughput_tps"],
                            "Detection Delay": m["delay_mean"],
                            "Honest Quarantines per 1000": m["honest_quarantines_per_1000"],
                            "Invalid Commit Rate": m["invalid_commit_rate"],
                            "Valid Reject Rate": m["valid_reject_rate"],
                            "HE ms per step": m["he_ms_per_step"]})
            pd.DataFrame(ep_rows).to_csv(RESULTS_DIR / f"{prefix}_seed{cfg.seed}_episode_metrics.csv", index=False)
            emit({"type": "episode_end", "run_id": run_id, "episode": ep, "step": env.t - 1,
                  "trust_scores": {n: float(t) for n, t in zip(env.nodes, env.records[-1].trust)},
                  "is_malicious": display_labels(env),
                  "is_detected": {n: bool(f) for n, f in zip(env.nodes, env.records[-1].flagged)},
                  "delegate_nodes": [], "transactions_verified": 0, "transactions_rejected": 0,
                  "byzantine_detections": int(sum(len(r.alarms) for r in env.records)),
                  "f1_score": float(m["det_f1"]), "precision": float(m["det_precision"]),
                  "recall": float(m["det_recall"]), "reward": ep_reward, "blockchain_length": blocks,
                  "trust_separation": 0.0, "action_taken": 0, "action_description": "episode_end",
                  "fhe_overhead_ms": m["he_ms_per_step"] if (cfg.fhe_enabled or cfg.tally_backend == "he") else None,
                  "timestamp": time.time(), "honest_metrics": {k: (None if isinstance(v, float) and np.isnan(v) else v)
                                                               for k, v in m.items()}})
        state["status"] = "completed"
    except InterruptedError as exc:
        state["status"] = "stopped"
        state["error"] = str(exc)
    except Exception as exc:
        state["status"] = "error"
        state["error"] = str(exc)
        asyncio.run_coroutine_threadsafe(queue.put({
            "type": "error", "run_id": run_id, "episode": 0, "step": 0, "trust_scores": {},
            "is_malicious": {},
            "is_detected": {}, "delegate_nodes": [], "transactions_verified": 0, "transactions_rejected": 0,
            "byzantine_detections": 0, "f1_score": 0.0, "precision": 0.0, "recall": 0.0, "reward": 0.0,
            "blockchain_length": 0, "trust_separation": 0.0, "action_taken": 0,
            "action_description": f"ERROR: {exc}", "fhe_overhead_ms": None, "timestamp": time.time()}), loop)
    finally:
        stream.close()
        state["completed_at"] = time.time()
        asyncio.run_coroutine_threadsafe(queue.put(None), loop)


async def start_simulation(cfg: SimulationConfig) -> tuple[str, asyncio.Queue]:
    """Start a simulation asynchronously and return its run id and event queue."""
    if len([r for r in _runs.values() if r["status"] == "running"]) >= MAX_CONCURRENT:
        raise RuntimeError(f"Maximum {MAX_CONCURRENT} concurrent simulations reached")
    run_id = _build_run_id(cfg)
    if run_id in _runs and _runs[run_id]["status"] == "running":
        raise RuntimeError(f"Run {run_id} is already active")
    queue: asyncio.Queue = asyncio.Queue(maxsize=0)
    loop = asyncio.get_event_loop()
    state = _make_run_state(run_id, cfg)
    state["queue"], state["loop"] = queue, loop
    _runs[run_id] = state
    thread = threading.Thread(target=_run_simulation_thread, args=(run_id, loop, queue), daemon=True)
    _threads[run_id] = thread
    thread.start()
    return run_id, queue


def stop_simulation(run_id: str) -> bool:
    state = _runs.get(run_id)
    if not state:
        return False
    state["stop_flag"].set()
    return True


def get_status(run_id: str) -> Optional[SimulationStatusResponse]:
    state = _runs.get(run_id)
    if not state:
        return None
    elapsed = time.time() - (state["started_at"] or time.time())
    progress = ((state["episode"] + 1) / max(1, state["total_episodes"])) * 100
    return SimulationStatusResponse(
        run_id=run_id, status=state["status"], episode=state["episode"],
        total_episodes=state["total_episodes"], progress_pct=round(min(progress, 100.0), 1),
        current_f1=state["current_f1"], current_reward=state["current_reward"],
        started_at=state["started_at"], elapsed_seconds=round(elapsed, 1), error=state["error"],
    )


def get_metadata(run_id: str) -> Optional[RunMetadata]:
    state = _runs.get(run_id)
    if not state:
        return None
    cfg: SimulationConfig = state["config"]
    return RunMetadata(
        run_id=run_id, agent=cfg.agent, attack=cfg.attack, consensus=cfg.consensus, nodes=cfg.nodes,
        episodes=cfg.episodes, steps_per_episode=cfg.steps_per_episode,
        malicious_fraction=cfg.malicious_fraction, started_at=state["started_at"],
        completed_at=state["completed_at"], status=state["status"],
    )


def list_runs() -> list[RunMetadata]:
    return [m for m in (get_metadata(r) for r in _runs) if m is not None]
