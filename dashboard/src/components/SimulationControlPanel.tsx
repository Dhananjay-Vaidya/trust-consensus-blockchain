import type { SimulationConfig } from "../types";
import { useState } from "react";
import { Play, Stop, CircleNotch } from "@phosphor-icons/react";
import { useSimulationStore } from "../store/simulationStore";
const attacks = [
  ["none", "None - baseline"],
  ["nma", "NMA - noise manipulation"],
  ["cra", "CRA - collusion"],
  ["aaa", "AAA - adaptive adversary"],
  ["bfi", "BFI - Byzantine faults"],
  ["tdp", "TDP - delayed poisoning"],
];
export function SimulationControlPanel() {
  const {
    config,
    status,
    replayRunId,
    setConfig,
    startSimulation,
    stopSimulation,
  } = useSimulationStore();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const running = status === "running";
  const start = async () => {
    setBusy(true);
    setError("");
    try {
      await startSimulation();
    } catch {
      setError(
        "Could not start the experiment. Check the simulation engine connection.",
      );
    } finally {
      setBusy(false);
    }
  };
  const stop = async () => {
    setBusy(true);
    try {
      await stopSimulation();
    } catch {
      setError("Could not stop the run. Try again.");
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <div className="config-header">
        <h2>{replayRunId ? "Next experiment setup" : "Experiment setup"}</h2>
        <p>
          {replayRunId
            ? "These settings apply to your next run."
            : "Configure a reproducible run."}
        </p>
      </div>
      <div className="config-form">
        <div className="field">
          <label>Learning agent</label>
          <div className="segmented">
            {(["rl", "drl", "marl"] as const).map((a) => (
              <button
                key={a}
                disabled={running || busy}
                onClick={() => setConfig({ agent: a })}
                aria-pressed={config.agent === a}
              >
                {a.toUpperCase()}
              </button>
            ))}
          </div>
          <span className="field-help">
            {config.agent === "rl"
              ? "Q-learning agent"
              : config.agent === "drl"
                ? "Deep reinforcement learning"
                : "Multi-agent reinforcement learning"}
          </span>
        </div>
        <div className="field">
          <label htmlFor="attack">Attack model</label>
          <select
            id="attack"
            value={config.attack}
            disabled={running || busy}
            onChange={(e) =>
              setConfig({ attack: e.target.value as typeof config.attack })
            }
          >
            {attacks.map(([v, l]) => (
              <option key={v} value={v}>
                {l}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor="consensus">Consensus protocol</label>
          <select
            id="consensus"
            value={config.consensus}
            disabled={running || busy}
            onChange={(e) =>
              setConfig({
                consensus: e.target.value as typeof config.consensus,
              })
            }
          >
            <option value="tdcb">TDCB - trust-driven</option>
            <option value="pbft">PBFT</option>
            <option value="static_dpos">Static DPoS</option>
            <option value="majority">Majority vote</option>
            <option value="random">Random delegation</option>
          </select>
        </div>
        <div className="config-divider" />
        {(
          [
            { key: "nodes", label: "Network nodes", min: 4, max: 128, step: 4 },
            {
              key: "episodes",
              label: "Training episodes",
              min: 1,
              max: 500,
              step: 1,
            },
            {
              key: "steps_per_episode",
              label: "Steps per episode",
              min: 1,
              max: 200,
              step: 1,
            },
          ] as const
        ).map(({ key, label, min, max, step }) => (
          <div className="field" key={key}>
            <label htmlFor={key}>
              {label}
              <output htmlFor={key}>{config[key]}</output>
            </label>
            <input
              id={key}
              type="range"
              min={min}
              max={max}
              step={step}
              value={config[key]}
              disabled={running || busy}
              onChange={(e) => setConfig({ [key]: Number(e.target.value) })}
            />
          </div>
        ))}
        <div className="field">
          <label htmlFor="malicious">
            Malicious nodes
            <output htmlFor="malicious">
              {Math.round(config.malicious_fraction * 100)}%
            </output>
          </label>
          <input
            id="malicious"
            type="range"
            min={5}
            max={49}
            value={Math.round(config.malicious_fraction * 100)}
            disabled={running || busy}
            onChange={(e) =>
              setConfig({ malicious_fraction: Number(e.target.value) / 100 })
            }
          />
          <span className="field-help">
            {Math.floor(config.nodes * config.malicious_fraction)} of{" "}
            {config.nodes} nodes configured as adversarial.
          </span>
        </div>
        <details className="advanced">
          <summary>Reproducibility & encryption</summary>
          <div className="field">
            <label htmlFor="seed">Random seed</label>
            <input
              id="seed"
              type="number"
              value={config.seed}
              disabled={running || busy}
              onChange={(e) => setConfig({ seed: Number(e.target.value) })}
            />
          </div>
          <div className="field">
            <label htmlFor="trust-backend">Trust backend</label>
            <select
              id="trust-backend"
              value={config.trust_backend}
              disabled={running || busy}
              onChange={(e) =>
                setConfig({ trust_backend: e.target.value as SimulationConfig["trust_backend"] })
              }
            >
              <option value="sleeper_guard">SleeperGuard (proposed)</option>
              <option value="legacy_beta">Legacy Beta (base protocol)</option>
              <option value="none">None (unweighted)</option>
            </select>
          </div>
          <div className="field">
            <label htmlFor="tally-backend">Tally backend</label>
            <select
              id="tally-backend"
              value={config.tally_backend}
              disabled={running || busy}
              onChange={(e) =>
                setConfig({ tally_backend: e.target.value as SimulationConfig["tally_backend"] })
              }
            >
              <option value="plain">Plaintext</option>
              <option value="he">Homomorphic (CKKS, TenSEAL)</option>
            </select>
          </div>
          <p className="field-help">
            The HE tally needs TenSEAL and fails loudly without it (no mock). It is
            ~100x slower per step; the decryptor still learns the margins (see
            docs/SECURITY_MODEL.md).
          </p>
        </details>
      </div>
      <div className="config-actions">
        {error && (
          <div role="alert" className="form-error">
            {error}
          </div>
        )}
        <button
          className={`primary-button ${running ? "danger-button" : ""}`}
          disabled={busy}
          onClick={() => void (running ? stop() : start())}
        >
          {busy ? (
            <CircleNotch size={16} />
          ) : running ? (
            <Stop size={16} weight="fill" />
          ) : (
            <Play size={16} weight="fill" />
          )}
          {busy
            ? "Please wait..."
            : running
              ? "Stop experiment"
              : "Start experiment"}
        </button>
        <p>
          {running
            ? "Streaming results from simulation engine"
            : "Results are saved automatically"}
        </p>
      </div>
    </>
  );
}
