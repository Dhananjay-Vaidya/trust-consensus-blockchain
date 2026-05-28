import { useSimulationWebSocket } from '../hooks/useSimulationWebSocket';
import { useSimulationStore } from '../store/simulationStore';

export function SimulationControls() {
  const {
    config,
    status,
    runId,
    replayRunId,
    currentEpisode,
    totalEpisodes,
    setConfig,
    startSimulation,
    stopSimulation,
  } = useSimulationStore();

  const streamMode = replayRunId && replayRunId === runId ? 'replay' : 'live';
  const { connectionState } = useSimulationWebSocket(runId, streamMode);

  const isRunning = status === 'running';
  const progress = totalEpisodes > 0 ? Math.round((currentEpisode / totalEpisodes) * 100) : 0;

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <h3>Simulation Controls</h3>
          <p>Launch a run, watch live stream state, and stop long experiments safely.</p>
        </div>
        <div className={`status-pill status-${status}`}>{status} / {connectionState}</div>
      </div>

      <div className="form-grid">
        <label className="field">
          <span>Agent</span>
          <select value={config.agent} disabled={isRunning} onChange={(event) => setConfig({ agent: event.target.value as typeof config.agent })}>
            <option value="rl">RL</option>
            <option value="drl">DRL</option>
            <option value="marl">MARL</option>
          </select>
        </label>
        <label className="field">
          <span>Attack</span>
          <select value={config.attack} disabled={isRunning} onChange={(event) => setConfig({ attack: event.target.value as typeof config.attack })}>
            <option value="none">None</option>
            <option value="nma">NMA</option>
            <option value="cra">CRA</option>
            <option value="aaa">AAA</option>
            <option value="bfi">BFI</option>
            <option value="tdp">TDP</option>
          </select>
        </label>
        <label className="field">
          <span>Consensus</span>
          <select value={config.consensus} disabled={isRunning} onChange={(event) => setConfig({ consensus: event.target.value as typeof config.consensus })}>
            <option value="tdcb">TDCB</option>
            <option value="pbft">PBFT</option>
            <option value="static_dpos">Static DPoS</option>
            <option value="majority">Majority</option>
            <option value="random">Random</option>
          </select>
        </label>
        <label className="field">
          <span>Nodes</span>
          <input type="number" min={4} max={128} value={config.nodes} disabled={isRunning} onChange={(event) => setConfig({ nodes: Number(event.target.value) })} />
        </label>
        <label className="field">
          <span>Episodes</span>
          <input type="number" min={1} max={500} value={config.episodes} disabled={isRunning} onChange={(event) => setConfig({ episodes: Number(event.target.value) })} />
        </label>
        <label className="field">
          <span>Steps / Episode</span>
          <input type="number" min={1} max={200} value={config.steps_per_episode} disabled={isRunning} onChange={(event) => setConfig({ steps_per_episode: Number(event.target.value) })} />
        </label>
        <label className="field">
          <span>Malicious Fraction</span>
          <input type="number" min={0.05} max={0.49} step={0.01} value={config.malicious_fraction} disabled={isRunning} onChange={(event) => setConfig({ malicious_fraction: Number(event.target.value) })} />
        </label>
        <label className="field">
          <span>Seed</span>
          <input type="number" value={config.seed} disabled={isRunning} onChange={(event) => setConfig({ seed: Number(event.target.value) })} />
        </label>
        <label className="field field-toggle">
          <span>FHE Enabled</span>
          <input type="checkbox" checked={config.fhe_enabled} disabled={isRunning} onChange={(event) => setConfig({ fhe_enabled: event.target.checked })} />
        </label>
      </div>

      <div className="progress-shell">
        <div className="progress-meta">
          <span>Episode {currentEpisode} / {totalEpisodes}</span>
          <span>{progress}%</span>
        </div>
        <div className="progress-bar">
          <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
        </div>
      </div>

      <div className="button-row">
        <button className="button button-primary" disabled={isRunning} onClick={() => void startSimulation()}>
          Start Simulation
        </button>
        <button className="button button-danger" disabled={!isRunning} onClick={() => void stopSimulation()}>
          Stop Simulation
        </button>
      </div>

      {runId && <div className="mono subtle">Run ID: {runId}</div>}
    </section>
  );
}
