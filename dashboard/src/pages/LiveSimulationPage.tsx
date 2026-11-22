import { Graph, ArrowSquareOut } from "@phosphor-icons/react";
import { Link } from "react-router-dom";
import { EventFeed } from "../components/EventFeed";
import { LiveMetricsPanel } from "../components/LiveMetricsPanel";
import { NodeDetailPanel } from "../components/NodeDetailPanel";
import { SimulationControlPanel } from "../components/SimulationControlPanel";
import { TrustNetworkGraph } from "../components/TrustNetworkGraph";
import { useSimulationStore } from "../store/simulationStore";
export function LiveSimulationPage() {
  const trust = useSimulationStore((s) => s.trustScores);
  const delegates = useSimulationStore((s) => s.delegateNodes);
  const latest = useSimulationStore((s) => s.latestStep);
  const status = useSimulationStore((s) => s.status);
  const replay = useSimulationStore((s) => s.replayRunId);
  return (
    <>
      <div className="page-heading live-heading">
        <div>
          <div className="eyebrow">Experiment workspace</div>
          <h1>Live simulation</h1>
          <p>
            Observe how trust shapes consensus under adversarial conditions.
          </p>
          {replay && (
            <p className="replay-source">
              Replay source: <code>{replay}</code>
            </p>
          )}
        </div>
        <Link to="/experiments" className="quiet-button">
          Saved experiments
          <ArrowSquareOut size={17} />
        </Link>
      </div>
      <div className="live-workspace">
        <aside className="configuration-panel">
          <SimulationControlPanel />
        </aside>
        <div className="observation-panel">
          <section className="network-panel">
            <div className="panel-heading">
              <div>
                <h2>
                  <Graph size={19} />
                  Trust network
                </h2>
                <p>Trust state and schematic delegate relationships</p>
              </div>
              <span
                className={`state-label ${status === "running" ? "is-running" : ""}`}
              >
                <span className="status-dot" />
                {status === "running"
                  ? replay
                    ? "Replay stream"
                    : "Live stream"
                  : status === "completed"
                    ? "Run completed"
                    : status === "stopped"
                      ? "Run stopped"
                      : status === "error"
                        ? "Connection error"
                        : "Awaiting experiment"}
              </span>
            </div>
            <div className="network-canvas">
              <TrustNetworkGraph />
              <NodeDetailPanel />
            </div>
            <div className="network-summary">
              <span>
                <strong>{Object.keys(trust).length || "--"}</strong> observed
                nodes
              </span>
              <span>
                <strong>
                  {(Object.keys(trust).length ? delegates.length : null) ??
                    "--"}
                </strong>{" "}
                active delegates
              </span>
              <span>
                <strong>{latest?.blockchain_length ?? "--"}</strong> chain
                length
              </span>
              <span className="network-hint">Select a node to inspect</span>
            </div>
          </section>
          <LiveMetricsPanel />
        </div>
        <section className="event-panel">
          <EventFeed />
        </section>
      </div>
    </>
  );
}
