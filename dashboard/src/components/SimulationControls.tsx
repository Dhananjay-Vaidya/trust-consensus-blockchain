import React from 'react';
import { useSimulationStore } from '../store/simulationStore';
import { useSimulationWebSocket } from '../hooks/useSimulationWebSocket';

export function SimulationControls() {
  const {
    config, status, runId, currentEpisode, totalEpisodes,
    setConfig, startSimulation, stopSimulation,
  } = useSimulationStore();

  useSimulationWebSocket(runId);

  const isRunning = status === 'running';
  const progress = totalEpisodes > 0
    ? Math.round((currentEpisode / totalEpisodes) * 100) : 0;

  const statusColor = {
    idle: 'text-muted',
    running: 'text-accent status-pulse',
    completed: 'text-success',
    error: 'text-danger',
  }[status];

  return (
    <div className="bg-surface rounded-xl p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-text-primary font-semibold text-lg">Simulation Controls</h2>
        <span className={`text-sm font-medium uppercase tracking-wide ${statusColor}`}>
          {status}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <label className="flex flex-col gap-1">
          <span className="text-xs text-muted">Agent</span>
          <select
            className="bg-bg border border-slate-700 rounded-lg px-2 py-1.5 text-sm text-text-primary"
            value={config.agent}
            disabled={isRunning}
            onChange={(e) => setConfig({ agent: e.target.value as 'rl' | 'drl' | 'marl' })}
          >
            <option value="rl">RL</option>
            <option value="drl">DRL (DDQN)</option>
            <option value="marl">MARL</option>
          </select>
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-muted">Attack</span>
          <select
            className="bg-bg border border-slate-700 rounded-lg px-2 py-1.5 text-sm text-text-primary"
            value={config.attack}
            disabled={isRunning}
            onChange={(e) => setConfig({ attack: e.target.value as SimulationControls['config']['attack'] })}
          >
            <option value="none">None</option>
            <option value="nma">NMA</option>
            <option value="cra">CRA</option>
            <option value="aaa">AAA</option>
            <option value="bfi">BFI</option>
            <option value="tdp">TDP</option>
          </select>
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-muted">Consensus</span>
          <select
            className="bg-bg border border-slate-700 rounded-lg px-2 py-1.5 text-sm text-text-primary"
            value={config.consensus}
            disabled={isRunning}
            onChange={(e) => setConfig({ consensus: e.target.value as 'tdcb' | 'pbft' | 'static_dpos' | 'majority' | 'random' })}
          >
            <option value="tdcb">TDCB</option>
            <option value="pbft">PBFT</option>
            <option value="static_dpos">Static DPoS</option>
            <option value="majority">Majority Vote</option>
            <option value="random">Random</option>
          </select>
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-muted">Nodes (4–128)</span>
          <input
            type="number" min={4} max={128}
            className="bg-bg border border-slate-700 rounded-lg px-2 py-1.5 text-sm text-text-primary"
            value={config.nodes}
            disabled={isRunning}
            onChange={(e) => setConfig({ nodes: Number(e.target.value) })}
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-muted">Episodes</span>
          <input
            type="number" min={1} max={500}
            className="bg-bg border border-slate-700 rounded-lg px-2 py-1.5 text-sm text-text-primary"
            value={config.episodes}
            disabled={isRunning}
            onChange={(e) => setConfig({ episodes: Number(e.target.value) })}
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-muted">Steps / Episode</span>
          <input
            type="number" min={5} max={200}
            className="bg-bg border border-slate-700 rounded-lg px-2 py-1.5 text-sm text-text-primary"
            value={config.steps_per_episode}
            disabled={isRunning}
            onChange={(e) => setConfig({ steps_per_episode: Number(e.target.value) })}
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-muted">Malicious Fraction</span>
          <input
            type="number" min={0.05} max={0.49} step={0.01}
            className="bg-bg border border-slate-700 rounded-lg px-2 py-1.5 text-sm text-text-primary"
            value={config.malicious_fraction}
            disabled={isRunning}
            onChange={(e) => setConfig({ malicious_fraction: Number(e.target.value) })}
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-muted">Seed</span>
          <input
            type="number"
            className="bg-bg border border-slate-700 rounded-lg px-2 py-1.5 text-sm text-text-primary"
            value={config.seed}
            disabled={isRunning}
            onChange={(e) => setConfig({ seed: Number(e.target.value) })}
          />
        </label>

        <label className="flex flex-col gap-1 justify-end">
          <span className="text-xs text-muted">FHE Enabled</span>
          <div className="flex items-center gap-2 h-8">
            <input
              type="checkbox"
              className="w-4 h-4 accent-accent"
              checked={config.fhe_enabled}
              disabled={isRunning}
              onChange={(e) => setConfig({ fhe_enabled: e.target.checked })}
            />
            <span className="text-sm text-text-primary">
              {config.fhe_enabled ? 'On' : 'Off'}
            </span>
          </div>
        </label>
      </div>

      {/* Progress bar */}
      {(isRunning || status === 'completed') && (
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-muted">
            <span>Episode {currentEpisode} / {totalEpisodes}</span>
            <span>{progress}%</span>
          </div>
          <div className="w-full bg-bg rounded-full h-2">
            <div
              className="bg-accent h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex gap-3">
        <button
          className="flex-1 py-2 rounded-lg font-medium text-sm bg-success text-white
                     disabled:opacity-40 disabled:cursor-not-allowed hover:brightness-110 transition"
          disabled={isRunning}
          onClick={startSimulation}
        >
          Start Simulation
        </button>
        {isRunning && (
          <button
            className="px-5 py-2 rounded-lg font-medium text-sm bg-danger text-white
                       hover:brightness-110 transition"
            onClick={stopSimulation}
          >
            Stop
          </button>
        )}
      </div>
    </div>
  );
}

// needed only to satisfy TS in the select onChange cast
type SimulationControlsConfig = {
  config: { attack: 'nma' | 'cra' | 'aaa' | 'bfi' | 'tdp' | 'none' };
};
// eslint-disable-next-line @typescript-eslint/no-unused-vars
type _Unused = SimulationControlsConfig;
