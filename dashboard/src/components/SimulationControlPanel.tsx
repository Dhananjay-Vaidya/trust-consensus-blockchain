import { useState } from 'react';
import toast from 'react-hot-toast';

import { useSimulationStore } from '../store/simulationStore';
import { useSimulationWebSocket } from '../hooks/useSimulationWebSocket';
import { StatusPill } from './ui/StatusPill';
import { Tooltip } from './ui/Tooltip';
import { Divider } from './ui/Divider';

const SCENARIOS = [
  { name: 'Smart Grid',          nodes: 32, attack: 'cra' as const, episodes: 100, malicious: 0.20 },
  { name: 'Hospital IoT',        nodes: 24, attack: 'tdp' as const, episodes: 100, malicious: 0.15 },
  { name: 'Supply Chain',        nodes: 16, attack: 'cra' as const, episodes: 80,  malicious: 0.25 },
  { name: 'Autonomous Vehicles', nodes: 64, attack: 'bfi' as const, episodes: 120, malicious: 0.20 },
  { name: 'Defence MANET',       nodes: 32, attack: 'aaa' as const, episodes: 100, malicious: 0.30 },
  { name: 'Fintech ATM',         nodes: 16, attack: 'cra' as const, episodes: 60,  malicious: 0.15 },
];

const ATTACK_DESC: Record<string, string> = {
  none: 'No Attack — baseline run',
  nma:  'Negligible Malicious Activity — low-level trust manipulation',
  cra:  'Coordinated Reputation Attack — colluding nodes boost each other',
  aaa:  'Adaptive Adversarial Attack — switches strategy dynamically',
  bfi:  'Byzantine Fault Injection — Sybil node injection',
  tdp:  'Time-Delayed Poisoning — sleeper agents activate later',
};

export function SimulationControlPanel() {
  const { config, status, runId, setConfig, startSimulation, stopSimulation } =
    useSimulationStore();
  const { connectionState } = useSimulationWebSocket(runId);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [scenarioOpen, setScenarioOpen] = useState(false);
  const [activeScenario, setActiveScenario] = useState<string | null>(null);

  const isRunning = status === 'running';

  const handleStart = async () => {
    try {
      await startSimulation();
      toast.success(`▶ Simulation started`);
    } catch {
      toast.error('Failed to start simulation');
    }
  };

  const handleStop = async () => {
    await stopSimulation();
    toast('Simulation stopped', { icon: '⏹' });
  };

  const loadScenario = (s: typeof SCENARIOS[number]) => {
    setConfig({ nodes: s.nodes, attack: s.attack, episodes: s.episodes, malicious_fraction: s.malicious });
    setActiveScenario(s.name);
  };

  const S: React.CSSProperties = {
    display: 'flex', flexDirection: 'column',
    height: '100%', background: 'var(--bg-surface)',
    borderRight: '1px solid var(--border)',
    overflowY: 'auto', padding: '12px 14px', gap: 0,
  };

  const fieldStyle: React.CSSProperties = {
    display: 'flex', flexDirection: 'column', gap: 5, marginBottom: 10,
  };

  const labelStyle: React.CSSProperties = {
    fontSize: 11, color: 'var(--text-secondary)', fontWeight: 500,
    display: 'flex', justifyContent: 'space-between',
  };

  const inputStyle: React.CSSProperties = {
    background: 'var(--bg-elevated)', border: '1px solid var(--border)',
    borderRadius: 'var(--radius-sm)', padding: '6px 10px',
    color: 'var(--text-primary)', fontSize: 13, width: '100%',
  };

  return (
    <div style={S}>
      {/* Header */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
          Simulation Controls
        </div>
        <StatusPill status={status as 'idle' | 'running' | 'paused' | 'completed' | 'error'} />
        <span style={{ fontSize: 10, color: 'var(--text-muted)', marginLeft: 8 }}>{connectionState}</span>
      </div>

      <Divider />

      {/* Agent Selector */}
      <div style={{ marginBottom: 10 }}>
        <div style={{ ...labelStyle, marginBottom: 6 }}>Agent</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 6 }}>
          {(['rl', 'drl', 'marl'] as const).map((a) => (
            <button key={a} disabled={isRunning}
              onClick={() => setConfig({ agent: a })}
              style={{
                padding: '8px 4px', borderRadius: 'var(--radius-sm)', cursor: 'pointer',
                background: config.agent === a ? 'var(--accent-dim)' : 'var(--bg-elevated)',
                border: `1px solid ${config.agent === a ? 'var(--accent)' : 'var(--border)'}`,
                color: config.agent === a ? 'var(--accent)' : 'var(--text-secondary)',
                fontSize: 11, fontWeight: 600, textTransform: 'uppercase',
              }}>
              {a.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Attack Selector */}
      <div style={{ marginBottom: 10 }}>
        <div style={{ ...labelStyle, marginBottom: 6 }}>Attack Type</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
          {(['none', 'nma', 'cra', 'aaa', 'bfi', 'tdp'] as const).map((atk) => (
            <Tooltip key={atk} content={ATTACK_DESC[atk]}>
              <button disabled={isRunning}
                onClick={() => setConfig({ attack: atk })}
                style={{
                  padding: '5px 10px', borderRadius: 'var(--radius-sm)', cursor: 'pointer',
                  background: config.attack === atk ? 'var(--red-dim)' : 'var(--bg-elevated)',
                  border: `1px solid ${config.attack === atk ? 'var(--red)' : 'var(--border)'}`,
                  color: config.attack === atk ? 'var(--red)' : 'var(--text-secondary)',
                  fontSize: 11, fontWeight: 600, textTransform: 'uppercase',
                }}>
                {atk.toUpperCase()}
              </button>
            </Tooltip>
          ))}
        </div>
      </div>

      {/* Consensus */}
      <div style={fieldStyle}>
        <label style={labelStyle}>Consensus</label>
        <select disabled={isRunning} value={config.consensus} style={inputStyle}
          onChange={(e) => setConfig({ consensus: e.target.value as typeof config.consensus })}>
          <option value="tdcb">TDCB (default)</option>
          <option value="pbft">PBFT</option>
          <option value="static_dpos">Static DPoS</option>
          <option value="majority">Majority Vote</option>
          <option value="random">Random</option>
        </select>
      </div>

      <Divider />

      {/* Scenarios */}
      <button onClick={() => setScenarioOpen((o) => !o)}
        style={{ background: 'none', border: 'none', padding: '4px 0', cursor: 'pointer',
          color: 'var(--text-secondary)', fontSize: 11, textAlign: 'left',
          display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
        <span>📌 Real-World Scenarios</span>
        <span>{scenarioOpen ? '▲' : '▼'}</span>
      </button>
      {scenarioOpen && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 10 }}>
          {SCENARIOS.map((s) => (
            <button key={s.name} disabled={isRunning}
              onClick={() => loadScenario(s)}
              style={{
                padding: '6px 10px', borderRadius: 'var(--radius-sm)', cursor: 'pointer',
                textAlign: 'left', fontSize: 11,
                background: activeScenario === s.name ? 'var(--accent-dim)' : 'var(--bg-elevated)',
                border: `1px solid ${activeScenario === s.name ? 'var(--accent-border)' : 'var(--border)'}`,
                color: activeScenario === s.name ? 'var(--accent)' : 'var(--text-primary)',
              }}>
              {s.name}
              <span style={{ color: 'var(--text-muted)', marginLeft: 6 }}>
                {s.nodes}n · {s.attack.toUpperCase()}
              </span>
            </button>
          ))}
        </div>
      )}

      {/* Sliders / number inputs */}
      {([
        { key: 'nodes',            label: 'Nodes',           min: 4,   max: 128, step: 4   },
        { key: 'episodes',         label: 'Episodes',        min: 10,  max: 500, step: 10  },
        { key: 'steps_per_episode',label: 'Steps / Episode', min: 5,   max: 100, step: 5   },
      ] as const).map(({ key, label, min, max, step }) => (
        <div key={key} style={fieldStyle}>
          <label style={labelStyle}>
            <span>{label}</span>
            <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
              {config[key]}
            </span>
          </label>
          <input type="range" min={min} max={max} step={step} disabled={isRunning}
            value={config[key]}
            onChange={(e) => setConfig({ [key]: Number(e.target.value) })}
            style={{ width: '100%', accentColor: 'var(--accent)', cursor: 'pointer' }}
          />
        </div>
      ))}

      <div style={fieldStyle}>
        <label style={labelStyle}>
          <span>Malicious Fraction</span>
          <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
            {Math.round(config.malicious_fraction * 100)}%
          </span>
        </label>
        <input type="range" min={5} max={49} step={1} disabled={isRunning}
          value={Math.round(config.malicious_fraction * 100)}
          onChange={(e) => setConfig({ malicious_fraction: Number(e.target.value) / 100 })}
          style={{ width: '100%', accentColor: 'var(--red)', cursor: 'pointer' }}
        />
      </div>

      <div style={fieldStyle}>
        <label style={labelStyle}>Seed</label>
        <input type="number" disabled={isRunning} value={config.seed} style={inputStyle}
          onChange={(e) => setConfig({ seed: Number(e.target.value) })} />
      </div>

      {/* Advanced Options */}
      <button onClick={() => setAdvancedOpen((o) => !o)}
        style={{ background: 'none', border: 'none', padding: '4px 0', cursor: 'pointer',
          color: 'var(--text-secondary)', fontSize: 11, textAlign: 'left',
          display: 'flex', justifyContent: 'space-between', margin: '6px 0' }}>
        <span>⚙ Advanced Options</span>
        <span>{advancedOpen ? '▲' : '▼'}</span>
      </button>
      {advancedOpen && (
        <div style={{ background: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', padding: 10, marginBottom: 10 }}>
          <div style={fieldStyle}>
            <label style={{ ...labelStyle, cursor: 'pointer' }}>
              <span>FHE Enabled</span>
              <input type="checkbox" checked={config.fhe_enabled} disabled={isRunning}
                onChange={(e) => setConfig({ fhe_enabled: e.target.checked })}
                style={{ accentColor: 'var(--accent)' }} />
            </label>
          </div>
        </div>
      )}

      <Divider />

      {/* Run ID */}
      {runId && (
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)',
          marginBottom: 10, cursor: 'pointer', wordBreak: 'break-all' }}
          onClick={() => { navigator.clipboard.writeText(runId); toast.success('Copied run ID'); }}>
          {runId.slice(0, 8)}…
        </div>
      )}

      {/* Buttons */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 'auto' }}>
        <button data-start disabled={isRunning} onClick={() => void handleStart()}
          style={{
            padding: '11px 16px', borderRadius: 'var(--radius-md)',
            background: isRunning ? 'var(--bg-active)' : 'var(--green)',
            color: 'white', fontWeight: 600, fontSize: 13, border: 'none',
            opacity: isRunning ? 0.5 : 1, cursor: isRunning ? 'not-allowed' : 'pointer',
          }}>
          ▶ Start Simulation
        </button>
        {isRunning && (
          <button onClick={() => void handleStop()}
            style={{ padding: '11px 16px', borderRadius: 'var(--radius-md)',
              background: 'var(--red)', color: 'white', fontWeight: 600, fontSize: 13, border: 'none' }}>
            ⏹ Stop
          </button>
        )}
      </div>
    </div>
  );
}
