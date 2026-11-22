import { useState } from "react";
import { Link } from "react-router-dom";
import { Flask, Graph, ChartLine } from "@phosphor-icons/react";
import { useSimulationStore } from "../store/simulationStore";
import { useResults } from "../hooks/useResults";
import type { SimulationConfig } from "../types";
const attacks = [
  {
    id: "nma",
    name: "Noise manipulation",
    category: "Low-level manipulation",
    description:
      "Perturbs trust evidence to study how noisy or misleading observations affect delegation.",
    behavior: "Malicious nodes manipulate activity and trust evidence.",
    focus: "Detection under noisy trust observations",
  },
  {
    id: "cra",
    name: "Collusive reputation attack",
    category: "Coordinated collusion",
    description:
      "Models cooperating malicious nodes that manipulate reputation to influence trust-based delegate selection.",
    behavior: "Adversaries coordinate reputation updates.",
    focus: "Trust separation under coordinated manipulation",
  },
  {
    id: "aaa",
    name: "Adaptive adversarial attack",
    category: "Adaptive behavior",
    description:
      "Models an adversary that changes behavior in response to the trust system.",
    behavior: "Attack behavior adapts as the simulation progresses.",
    focus: "Agent response to changing adversarial strategies",
  },
  {
    id: "bfi",
    name: "Byzantine fault injection",
    category: "Byzantine behavior",
    description:
      "Introduces adversarial behavior intended to disrupt transaction verification and consensus.",
    behavior:
      "Malicious participants generate conflicting or invalid activity.",
    focus: "Consensus resilience and malicious-node detection",
  },
  {
    id: "tdp",
    name: "Time-delayed poisoning",
    category: "Delayed activation",
    description:
      "Models initially cooperative nodes that activate malicious behavior after a configured delay.",
    behavior: "The default activation episode is 25.",
    focus: "Trust recovery following adversarial activation",
  },
] as const;
export function AttackLabPage() {
  const [active, setActive] = useState<(typeof attacks)[number]["id"]>("cra");
  const info = attacks.find((a) => a.id === active)!;
  const setConfig = useSimulationStore((s) => s.setConfig);
  const { data: runs = [] } = useResults();
  const matching = runs.filter((r) => r.attack === active);
  return (
    <div className="attack-workspace">
      <div className="attack-selector" role="group" aria-label="Attack model">
        {attacks.map((a) => (
          <button
            key={a.id}
            className={`attack-choice ${active === a.id ? "selected" : ""}`}
            aria-pressed={active === a.id}
            onClick={() => setActive(a.id)}
          >
            <span>{a.id.toUpperCase()}</span>
            <small>{a.name}</small>
          </button>
        ))}
      </div>
      <div className="attack-layout">
        <section className="data-panel attack-description">
          <div className="eyebrow">{info.category}</div>
          <h2>{info.name}</h2>
          <p>{info.description}</p>
          <div className="model-flow">
            <span>
              <Graph size={23} />
              Trust evidence
            </span>
            <span className="flow-connector" />
            <span className="adversary-block">
              <Flask size={23} />
              {active.toUpperCase()}
            </span>
            <span className="flow-connector" />
            <span>
              <ChartLine size={23} />
              Measured response
            </span>
          </div>
          <dl className="description-list">
            <div>
              <dt>Modeled behavior</dt>
              <dd>{info.behavior}</dd>
            </div>
            <div>
              <dt>Evaluation focus</dt>
              <dd>{info.focus}</dd>
            </div>
          </dl>
          <Link
            to="/"
            className="quiet-button"
            onClick={() =>
              setConfig({ attack: active as SimulationConfig["attack"] })
            }
          >
            Configure this experiment
          </Link>
        </section>
        <section className="data-panel evidence-panel">
          <h3>Recorded evidence</h3>
          <p>
            Final F1 scores from saved experiments using {active.toUpperCase()}.
            These runs may use different node counts, seeds, and training
            budgets.
          </p>
          <div className="evidence-count">
            {matching.length}
            <small>saved experiments</small>
          </div>
          {!matching.length ? (
            <p>No recorded runs for this attack yet.</p>
          ) : (
            <div className="agent-evidence">
              {["rl", "drl", "marl"].map((agent) => {
                const rows = matching.filter(
                  (r) => r.agent === agent && r.final_f1 !== null,
                );
                return (
                  <div key={agent}>
                    <span>{agent.toUpperCase()}</span>
                    <strong>
                      {rows.length
                        ? (
                            rows.reduce((v, r) => v + (r.final_f1 ?? 0), 0) /
                            rows.length
                          ).toFixed(3)
                        : "--"}
                    </strong>
                    <small>{rows.length} runs / mean final F1</small>
                  </div>
                );
              })}
            </div>
          )}
          <Link className="quiet-button" to="/experiments">
            Inspect source experiments
          </Link>
        </section>
      </div>
      <div className="research-callout">
        <Flask size={21} />
        <p>
          Attack profiles describe the simulation model. Performance summaries
          come from saved runs; they are not controlled comparisons. Use matched
          configurations and repeated seeds for paper results.
        </p>
      </div>
    </div>
  );
}
