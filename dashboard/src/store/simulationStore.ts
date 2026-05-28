import { create } from 'zustand';
import axios from 'axios';
import type { SimulationConfig, StepEvent, EpisodeSummary } from '../types';

const DEFAULT_CONFIG: SimulationConfig = {
  agent: 'marl',
  attack: 'cra',
  consensus: 'tdcb',
  nodes: 16,
  episodes: 50,
  steps_per_episode: 30,
  malicious_fraction: 0.30,
  seed: 42,
  fhe_enabled: false,
  scenario: null,
};

interface SimulationStore {
  runId: string | null;
  status: 'idle' | 'running' | 'completed' | 'error';
  config: SimulationConfig;
  currentEpisode: number;
  totalEpisodes: number;
  latestStep: StepEvent | null;
  episodeHistory: EpisodeSummary[];
  trustScores: Record<string, number>;
  isMalicious: Record<string, boolean>;
  isDetected: Record<string, boolean>;
  delegateNodes: string[];
  ws: WebSocket | null;

  // Actions
  setConfig: (config: Partial<SimulationConfig>) => void;
  startSimulation: () => Promise<void>;
  stopSimulation: () => void;
  handleStepEvent: (event: StepEvent) => void;
  handleEpisodeEnd: (event: StepEvent) => void;
  setWs: (ws: WebSocket | null) => void;
  setStatus: (status: SimulationStore['status']) => void;
  reset: () => void;
}

export const useSimulationStore = create<SimulationStore>((set, get) => ({
  runId: null,
  status: 'idle',
  config: DEFAULT_CONFIG,
  currentEpisode: 0,
  totalEpisodes: 0,
  latestStep: null,
  episodeHistory: [],
  trustScores: {},
  isMalicious: {},
  isDetected: {},
  delegateNodes: [],
  ws: null,

  setConfig: (partial) =>
    set((s) => ({ config: { ...s.config, ...partial } })),

  startSimulation: async () => {
    const { config } = get();
    set({ status: 'running', episodeHistory: [], latestStep: null,
          currentEpisode: 0, totalEpisodes: config.episodes });
    try {
      const res = await axios.post('/simulation/start', config);
      set({ runId: res.data.run_id });
    } catch (e) {
      set({ status: 'error', runId: null });
    }
  },

  stopSimulation: () => {
    const { runId, ws } = get();
    if (ws) { ws.close(); }
    if (runId) {
      axios.post(`/simulation/${runId}/stop`).catch(() => {});
    }
    set({ status: 'completed', ws: null });
  },

  handleStepEvent: (event) => {
    set({
      latestStep: event,
      currentEpisode: event.episode,
      trustScores: event.trust_scores,
      isMalicious: event.is_malicious,
      isDetected: event.is_detected,
      delegateNodes: event.delegate_nodes,
    });
  },

  handleEpisodeEnd: (event) => {
    const summary: EpisodeSummary = {
      episode: event.episode,
      f1_score: event.f1_score,
      precision: event.precision,
      recall: event.recall,
      reward: event.reward,
      blockchain_length: event.blockchain_length,
      byzantine_detections: event.byzantine_detections,
      transactions_verified: event.transactions_verified,
      trust_separation: event.trust_separation,
    };
    set((s) => ({
      episodeHistory: [...s.episodeHistory, summary],
      currentEpisode: event.episode + 1,
    }));
  },

  setWs: (ws) => set({ ws }),
  setStatus: (status) => set({ status }),

  reset: () =>
    set({
      runId: null,
      status: 'idle',
      currentEpisode: 0,
      totalEpisodes: 0,
      latestStep: null,
      episodeHistory: [],
      trustScores: {},
      isMalicious: {},
      isDetected: {},
      delegateNodes: [],
      ws: null,
    }),
}));
