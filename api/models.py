from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class SimulationConfig(BaseModel):
    agent: Literal["rl", "drl", "marl"] = "marl"
    attack: Literal["nma", "cra", "aaa", "bfi", "tdp", "none"] = "cra"
    consensus: Literal["tdcb", "pbft", "static_dpos", "majority", "random"] = "tdcb"
    nodes: int = Field(16, ge=4, le=128)
    episodes: int = Field(50, ge=1, le=500)
    steps_per_episode: int = Field(30, ge=5, le=200)
    malicious_fraction: float = Field(0.30, ge=0.05, le=0.49)
    seed: int = 42
    fhe_enabled: bool = False
    scenario: Optional[str] = None


class SimulationStatus(BaseModel):
    run_id: str
    status: Literal["idle", "running", "completed", "error"]
    episode: int
    total_episodes: int
    progress_pct: float
    current_f1: float
    current_reward: float
    started_at: Optional[float]
    elapsed_seconds: float


class StepEvent(BaseModel):
    type: Literal["step", "episode_end", "simulation_end", "error"]
    run_id: str
    episode: int
    step: int
    trust_scores: Dict[str, float]
    is_malicious: Dict[str, bool]
    is_detected: Dict[str, bool]
    delegate_nodes: List[str]
    transactions_verified: int
    transactions_rejected: int
    byzantine_detections: int
    f1_score: float
    precision: float
    recall: float
    reward: float
    blockchain_length: int
    trust_separation: float
    action_taken: int
    action_description: str
    fhe_overhead_ms: Optional[float] = None
    timestamp: float
