import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Lightning,
  Heartbeat,
  Truck,
  Car,
  Broadcast,
  Bank,
  CaretDown,
  CaretUp,
} from "@phosphor-icons/react";
import { useSimulationStore } from "../store/simulationStore";
import type { SimulationConfig } from "../types";
const scenarios = [
  {
    id: "grid",
    name: "Smart grid",
    icon: Lightning,
    nodes: 32,
    episodes: 100,
    malicious: 0.2,
    attack: "cra",
    desc: "Metering and control nodes in an electricity distribution network.",
    threat:
      "Coordinated reputation manipulation among compromised metering nodes.",
  },
  {
    id: "hospital",
    name: "Healthcare IoT",
    icon: Heartbeat,
    nodes: 24,
    episodes: 100,
    malicious: 0.15,
    attack: "tdp",
    desc: "Connected monitoring devices and medical data systems.",
    threat:
      "Initially cooperative nodes activate malicious behavior after building trust.",
  },
  {
    id: "logistics",
    name: "Supply chain",
    icon: Truck,
    nodes: 16,
    episodes: 80,
    malicious: 0.25,
    attack: "cra",
    desc: "RFID, GPS, and provenance records across a logistics network.",
    threat:
      "Colluding nodes manipulate reputation to influence provenance verification.",
  },
  {
    id: "vehicles",
    name: "Connected vehicles",
    icon: Car,
    nodes: 64,
    episodes: 120,
    malicious: 0.2,
    attack: "bfi",
    desc: "Vehicle and roadside participants in a V2X network.",
    threat:
      "Byzantine participants disrupt consensus with adversarial activity.",
  },
  {
    id: "manet",
    name: "Tactical networks",
    icon: Broadcast,
    nodes: 32,
    episodes: 100,
    malicious: 0.3,
    attack: "aaa",
    desc: "Mobile ad hoc nodes with changing communication conditions.",
    threat:
      "An adaptive adversary changes behavior as the trust system responds.",
  },
  {
    id: "finance",
    name: "Financial terminals",
    icon: Bank,
    nodes: 16,
    episodes: 60,
    malicious: 0.15,
    attack: "cra",
    desc: "Distributed terminal nodes and transaction audit records.",
    threat:
      "Coordinated reputation manipulation influences delegate selection.",
  },
] as const;
export function ScenariosPage() {
  const [expanded, setExpanded] = useState<string | null>(null);
  const setConfig = useSimulationStore((s) => s.setConfig);
  const navigate = useNavigate();
  return (
    <div className="scenario-workspace">
      <div className="research-callout">
        <p>
          These presets provide illustrative deployment contexts for the
          simulation. They do not represent validated deployments or guarantee a
          particular detection score.
        </p>
      </div>
      <div className="scenario-grid">
        {scenarios.map((s) => (
          <article className="scenario-card" key={s.id}>
            <div className="scenario-card-header">
              <span className="scenario-symbol">
                <s.icon size={23} />
              </span>
              <span className="neutral-tag">{s.attack.toUpperCase()}</span>
            </div>
            <h2>{s.name}</h2>
            <p>{s.desc}</p>
            <dl className="scenario-specs">
              <div>
                <dt>Nodes</dt>
                <dd>{s.nodes}</dd>
              </div>
              <div>
                <dt>Episodes</dt>
                <dd>{s.episodes}</dd>
              </div>
              <div>
                <dt>Malicious</dt>
                <dd>{Math.round(s.malicious * 100)}%</dd>
              </div>
            </dl>
            <div className="scenario-actions">
              <button
                className="quiet-button"
                onClick={() => {
                  setConfig({
                    nodes: s.nodes,
                    episodes: s.episodes,
                    malicious_fraction: s.malicious,
                    attack: s.attack as SimulationConfig["attack"],
                  });
                  navigate("/");
                }}
              >
                Load configuration
              </button>
              <button
                className="text-button"
                aria-expanded={expanded === s.id}
                onClick={() => setExpanded(expanded === s.id ? null : s.id)}
                aria-label={`Threat model for ${s.name}`}
              >
                {expanded === s.id ? (
                  <CaretUp size={18} />
                ) : (
                  <CaretDown size={18} />
                )}
              </button>
            </div>
            {expanded === s.id && (
              <div className="scenario-detail">
                <h3>Threat model</h3>
                <p>{s.threat}</p>
                <p>
                  Measure outcomes using saved run metrics and matched baseline
                  experiments.
                </p>
              </div>
            )}
          </article>
        ))}
      </div>
    </div>
  );
}
