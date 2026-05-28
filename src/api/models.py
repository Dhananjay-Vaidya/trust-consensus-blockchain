from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class SimulationStartRequest(BaseModel):
    """Request payload used to start a simulation run."""

    agent: Literal["rl", "drl", "marl"] = Field(
        default="marl",
        description="Learning agent family used to adapt delegation behaviour.",
        examples=["marl"],
    )
    attack: Literal["nma", "cra", "aaa", "bfi", "tdp", "none"] = Field(
        default="cra",
        description="Attack model injected into the trust system.",
        examples=["cra"],
    )
    consensus: Literal["tdcb", "pbft", "static_dpos", "majority", "random"] = Field(
        default="tdcb",
        description="Consensus mechanism used for the run.",
        examples=["tdcb"],
    )
    nodes: int = Field(
        default=16,
        ge=4,
        le=128,
        description="Number of IoT nodes in the simulated network.",
        examples=[16],
    )
    episodes: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Total number of training episodes to execute.",
        examples=[50],
    )
    steps_per_episode: int = Field(
        default=30,
        ge=1,
        le=200,
        description="Simulation steps per episode.",
        examples=[30],
    )
    malicious_fraction: float = Field(
        default=0.30,
        ge=0.05,
        le=0.49,
        description="Fraction of malicious nodes in the system.",
        examples=[0.30],
    )
    seed: int = Field(
        default=42,
        description="Random seed for deterministic execution.",
        examples=[42],
    )
    fhe_enabled: bool = Field(
        default=False,
        description="Enable the optional FHE evaluation path.",
        examples=[False],
    )
    scenario: Optional[str] = Field(
        default=None,
        description="Optional scenario YAML path for preset overrides.",
        examples=["experiments/scenarios/smart_grid.yaml"],
    )


class RunMetadata(BaseModel):
    """Stable metadata describing a simulation run."""

    run_id: str = Field(..., description="Unique identifier for the run.", examples=["2f687d7f-1eb1-4d9b-a8db-cf6d3914d930"])
    agent: str = Field(..., description="Agent used for this run.", examples=["marl"])
    attack: str = Field(..., description="Attack mode used for this run.", examples=["cra"])
    consensus: str = Field(..., description="Consensus mode used for this run.", examples=["tdcb"])
    nodes: int = Field(..., description="Number of nodes in the run.", examples=[16])
    episodes: int = Field(..., description="Configured episode count.", examples=[50])
    steps_per_episode: int = Field(..., description="Configured step count per episode.", examples=[30])
    malicious_fraction: float = Field(..., description="Configured malicious node ratio.", examples=[0.30])
    started_at: Optional[float] = Field(None, description="Unix timestamp when the run started.", examples=[1779980000.0])
    completed_at: Optional[float] = Field(None, description="Unix timestamp when the run ended, if available.", examples=[1779980123.0])
    status: Literal["idle", "running", "completed", "error", "stopped"] = Field(
        ...,
        description="Current lifecycle state for the run.",
        examples=["running"],
    )


class SimulationStartResponse(BaseModel):
    """Response returned after a run is accepted."""

    run_id: str = Field(..., description="Unique identifier assigned to the run.", examples=["2f687d7f-1eb1-4d9b-a8db-cf6d3914d930"])
    status: Literal["running"] = Field(..., description="Initial status returned by the API.", examples=["running"])
    metadata: RunMetadata


class SimulationStatusResponse(BaseModel):
    """Current status snapshot for a running or completed run."""

    run_id: str = Field(..., description="Unique identifier for the run.", examples=["2f687d7f-1eb1-4d9b-a8db-cf6d3914d930"])
    status: Literal["idle", "running", "completed", "error", "stopped"] = Field(..., description="Lifecycle state.", examples=["completed"])
    episode: int = Field(..., description="Current zero-based episode index.", examples=[12])
    total_episodes: int = Field(..., description="Configured total episode count.", examples=[50])
    progress_pct: float = Field(..., description="Completion percentage for the run.", examples=[24.0])
    current_f1: float = Field(..., description="Latest available F1 score.", examples=[0.845])
    current_reward: float = Field(..., description="Latest available reward value.", examples=[71.2])
    started_at: Optional[float] = Field(None, description="Unix timestamp when execution started.", examples=[1779980000.0])
    elapsed_seconds: float = Field(..., description="Elapsed wall-clock seconds since start.", examples=[28.4])
    error: Optional[str] = Field(None, description="Error string when the run fails.", examples=["Simulation stopped by user"])


class StepEventPayload(BaseModel):
    """Per-step or end-of-episode simulation event pushed over WebSocket."""

    type: Literal["step", "episode_end", "simulation_end", "error"] = Field(..., description="Event category.", examples=["step"])
    run_id: str = Field(..., description="Unique run identifier.", examples=["2f687d7f-1eb1-4d9b-a8db-cf6d3914d930"])
    episode: int = Field(..., description="Current zero-based episode index.", examples=[3])
    step: int = Field(..., description="Current zero-based step index within the episode.", examples=[17])
    trust_scores: Dict[str, float] = Field(..., description="Current node trust scores keyed by node id.")
    is_malicious: Dict[str, bool] = Field(..., description="Ground-truth malicious labels keyed by node id.")
    is_detected: Dict[str, bool] = Field(..., description="Detection flags keyed by node id.")
    delegate_nodes: List[str] = Field(..., description="Delegates used for the current consensus round.", examples=[["Node_1", "Node_2"]])
    transactions_verified: int = Field(..., description="Transactions verified for the current event.", examples=[21])
    transactions_rejected: int = Field(..., description="Transactions rejected for the current event.", examples=[4])
    byzantine_detections: int = Field(..., description="Number of Byzantine detections recorded for the event.", examples=[2])
    f1_score: float = Field(..., description="Current F1 score.", examples=[0.7917])
    precision: float = Field(..., description="Current precision value.", examples=[0.8])
    recall: float = Field(..., description="Current recall value.", examples=[0.75])
    reward: float = Field(..., description="Current step reward or episode reward.", examples=[74.4])
    blockchain_length: int = Field(..., description="Current blockchain length.", examples=[12])
    trust_separation: float = Field(..., description="Difference between average honest and malicious trust.", examples=[0.21])
    action_taken: int = Field(..., description="Discrete action chosen by the agent.", examples=[4])
    action_description: str = Field(..., description="Human-readable action summary.", examples=["dr×1.1 td×1.0 ct+0.00"])
    fhe_overhead_ms: Optional[float] = Field(None, description="Measured FHE overhead in milliseconds when enabled.", examples=[0.37])
    timestamp: float = Field(..., description="Unix timestamp for the event.", examples=[1779980001.2])


class EpisodeSummaryPayload(BaseModel):
    """Compact episode summary returned for charts and tabular displays."""

    run_id: str = Field(..., description="Unique run identifier.", examples=["2f687d7f-1eb1-4d9b-a8db-cf6d3914d930"])
    episode: int = Field(..., description="Completed episode index.", examples=[12])
    f1_score: float = Field(..., description="Episode final F1 score.", examples=[0.84])
    precision: float = Field(..., description="Episode final precision.", examples=[0.82])
    recall: float = Field(..., description="Episode final recall.", examples=[0.79])
    reward: float = Field(..., description="Episode cumulative reward.", examples=[83.1])
    blockchain_length: int = Field(..., description="Blockchain length after the episode.", examples=[18])
    byzantine_detections: int = Field(..., description="Total Byzantine detections at this point.", examples=[7])
    transactions_verified: int = Field(..., description="Transactions verified during the episode end event.", examples=[0])
    trust_separation: float = Field(..., description="Honest-minus-malicious trust separation.", examples=[0.19])
    fhe_overhead_ms: Optional[float] = Field(None, description="Average FHE overhead for the episode.", examples=[0.28])


class ResultRunMetadata(BaseModel):
    """Metadata for a completed run discovered from saved CSVs."""

    run_id: str = Field(..., description="Run identifier derived from the CSV name.")
    agent: str = Field(..., description="Agent used by the run.")
    attack: str = Field(..., description="Attack mode used by the run.")
    nodes: str = Field(..., description="Node count encoded in the file name.")
    final_f1: Optional[float] = Field(None, description="Final F1 score from the CSV, when available.")
    episodes: int = Field(..., description="Number of rows in the episode metrics file.")
    completed_at: float = Field(..., description="Last modification time of the CSV.")
    filename: str = Field(..., description="Filename of the episode metrics CSV.")


class CompareRunsResponse(BaseModel):
    """Response payload for the multi-run comparison endpoint."""

    metric: str = Field(..., description="Metric requested for the comparison.", examples=["F1 Score"])
    series: Dict[str, List[float]] = Field(..., description="Per-run metric series keyed by run id.")
    finals: Dict[str, Optional[float]] = Field(..., description="Final metric values keyed by run id.")


SimulationConfig = SimulationStartRequest
SimulationStatus = SimulationStatusResponse
StepEvent = StepEventPayload
