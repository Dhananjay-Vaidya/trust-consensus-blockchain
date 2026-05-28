export interface SimulationConfig {
  agent: 'rl' | 'drl' | 'marl';
  attack: 'nma' | 'cra' | 'aaa' | 'bfi' | 'tdp' | 'none';
  consensus: 'tdcb' | 'pbft' | 'static_dpos' | 'majority' | 'random';
  nodes: number;
  episodes: number;
  steps_per_episode: number;
  malicious_fraction: number;
  seed: number;
  fhe_enabled: boolean;
  scenario: string | null;
}

export interface StepEvent {
  type: 'step' | 'episode_end' | 'simulation_end' | 'error';
  run_id: string;
  episode: number;
  step: number;
  trust_scores: Record<string, number>;
  is_malicious: Record<string, boolean>;
  is_detected: Record<string, boolean>;
  delegate_nodes: string[];
  transactions_verified: number;
  transactions_rejected: number;
  byzantine_detections: number;
  f1_score: number;
  precision: number;
  recall: number;
  reward: number;
  blockchain_length: number;
  trust_separation: number;
  action_taken: number;
  action_description: string;
  fhe_overhead_ms: number | null;
  timestamp: number;
}

export interface EpisodeSummary {
  episode: number;
  f1_score: number;
  precision: number;
  recall: number;
  reward: number;
  blockchain_length: number;
  byzantine_detections: number;
  transactions_verified: number;
  trust_separation: number;
}

export interface SimulationStatus {
  run_id: string;
  status: 'idle' | 'running' | 'completed' | 'error';
  episode: number;
  total_episodes: number;
  progress_pct: number;
  current_f1: number;
  current_reward: number;
  started_at: number | null;
  elapsed_seconds: number;
}

export interface ResultRow {
  run_id: string;
  agent: string;
  attack: string;
  nodes: string;
  final_f1: number | null;
  episodes: number;
  completed_at: number;
  filename: string;
}
