import { create } from "zustand";

import { apiClient } from "../api/client";
import type {
  EpisodeSummary,
  ResultRunMetadata,
  SimulationConfig,
  StepEvent,
} from "../types";

const DEFAULT_CONFIG: SimulationConfig = {
  agent: "marl",
  attack: "cra",
  consensus: "tdcb",
  nodes: 16,
  episodes: 50,
  steps_per_episode: 30,
  malicious_fraction: 0.3,
  seed: 42,
  fhe_enabled: false,
  scenario: null,
};

interface SimulationStore {
  runId: string | null;
  streamVersion: number;
  replayRunId: string | null;
  status: "idle" | "running" | "completed" | "error" | "stopped";
  config: SimulationConfig;
  currentEpisode: number;
  totalEpisodes: number;
  latestStep: StepEvent | null;
  episodeHistory: EpisodeSummary[];
  trustScores: Record<string, number>;
  isMalicious: Record<string, boolean>;
  isDetected: Record<string, boolean>;
  delegateNodes: string[];
  webSocketState: "idle" | "connecting" | "open" | "closed" | "error";
  selectedComparisonRuns: string[];
  activeRuns: ResultRunMetadata[];
  selectedNodeId: string | null;

  setConfig: (partial: Partial<SimulationConfig>) => void;
  setWebSocketState: (state: SimulationStore["webSocketState"]) => void;
  startSimulation: () => Promise<void>;
  stopSimulation: () => Promise<void>;
  beginReplay: (runId: string) => void;
  toggleComparisonRun: (runId: string) => void;
  handleStepEvent: (event: StepEvent) => void;
  handleEpisodeEnd: (event: StepEvent) => void;
  handleSimulationEnd: (event: StepEvent) => void;
  selectNode: (nodeId: string | null) => void;
}

export const useSimulationStore = create<SimulationStore>((set, get) => ({
  runId: null,
  streamVersion: 0,
  status: "idle",
  config: DEFAULT_CONFIG,
  currentEpisode: 0,
  totalEpisodes: 0,
  latestStep: null,
  episodeHistory: [],
  trustScores: {},
  isMalicious: {},
  isDetected: {},
  delegateNodes: [],
  webSocketState: "idle",
  replayRunId: null,
  selectedComparisonRuns: [],
  activeRuns: [],
  selectedNodeId: null,

  setConfig: (partial) =>
    set((state) => ({ config: { ...state.config, ...partial } })),
  setWebSocketState: (webSocketState) => set({ webSocketState }),
  selectNode: (nodeId) => set({ selectedNodeId: nodeId }),

  startSimulation: async () => {
    const config = get().config;
    set({
      status: "running",
      currentEpisode: 0,
      totalEpisodes: config.episodes,
      latestStep: null,
      episodeHistory: [],
      trustScores: {},
      isMalicious: {},
      isDetected: {},
      delegateNodes: [],
      replayRunId: null,
      selectedNodeId: null,
    });
    try {
      const response = await apiClient.post("/simulation/start", config);
      set({
        runId: response.data.run_id,
        streamVersion: get().streamVersion + 1,
      });
    } catch (error) {
      set({ status: "error", runId: null });
      throw error;
    }
  },

  stopSimulation: async () => {
    if (get().replayRunId) {
      set({ status: "stopped", runId: null, replayRunId: null });
      return;
    }
    const runId = get().runId;
    if (runId) {
      await apiClient.post(`/simulation/${runId}/stop`);
    }
    set({ status: "stopped" });
  },

  beginReplay: (runId) => {
    set({
      runId,
      replayRunId: runId,
      streamVersion: get().streamVersion + 1,
      status: "running",
      currentEpisode: 0,
      totalEpisodes: Number(runId.split("_")[1]) || 0,
      latestStep: null,
      episodeHistory: [],
      trustScores: {},
      isMalicious: {},
      isDetected: {},
      delegateNodes: [],
    });
  },

  toggleComparisonRun: (runId) =>
    set((state) => ({
      selectedComparisonRuns: state.selectedComparisonRuns.includes(runId)
        ? state.selectedComparisonRuns.filter((value) => value !== runId)
        : state.selectedComparisonRuns.length < 6
          ? [...state.selectedComparisonRuns, runId]
          : state.selectedComparisonRuns,
    })),

  handleStepEvent: (event) =>
    set({
      latestStep: event,
      currentEpisode: event.episode + 1,
      trustScores: event.trust_scores,
      isMalicious: event.is_malicious,
      isDetected: event.is_detected,
      delegateNodes: event.delegate_nodes,
    }),

  handleEpisodeEnd: (event) =>
    set((state) => ({
      latestStep: event,
      currentEpisode: event.episode + 1,
      trustScores: event.trust_scores,
      isMalicious: event.is_malicious,
      isDetected: event.is_detected,
      delegateNodes: event.delegate_nodes,
      episodeHistory: [
        ...state.episodeHistory,
        {
          run_id: event.run_id,
          episode: event.episode,
          f1_score: event.f1_score,
          precision: event.precision,
          recall: event.recall,
          reward: event.reward,
          blockchain_length: event.blockchain_length,
          byzantine_detections: event.byzantine_detections,
          transactions_verified: event.transactions_verified,
          trust_separation: event.trust_separation,
          fhe_overhead_ms: event.fhe_overhead_ms,
        },
      ],
    })),

  handleSimulationEnd: () =>
    set((state) => ({
      status: state.status === "stopped" ? "stopped" : "completed",
      webSocketState: "closed",
    })),
}));
