import { useSimulationStore } from "../store/simulationStore";
import { useSimulationWebSocket } from "../hooks/useSimulationWebSocket";
import { Suspense, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
const descriptions: Record<string, [string, string]> = {
  "/metrics": [
    "Metrics explorer",
    "Inspect recorded episode metrics and trace model behavior over time.",
  ],
  "/attack-lab": [
    "Attack laboratory",
    "Examine adversarial strategies and configure the threat model.",
  ],
  "/scenarios": [
    "Scenario library",
    "Explore deployment contexts and load reproducible experiment configurations.",
  ],
  "/experiments": [
    "Experiment results",
    "Browse recorded runs, replay event streams, and download source data.",
  ],
  "/compare": [
    "Compare runs",
    "Evaluate recorded results across agents and attack configurations.",
  ],
  "/explainer": [
    "System architecture",
    "Follow the path from transaction authorization to adaptive consensus.",
  ],
  "/export": [
    "Export & present",
    "Prepare experiment data and supporting material for your presentation.",
  ],
};
const sections: Record<string, string> = {
  "/metrics": "§2 · Part I, Workspace",
  "/attack-lab": "§3 · Part I, Workspace",
  "/scenarios": "§4 · Part I, Workspace",
  "/experiments": "§5 · Part II, Research",
  "/compare": "§6 · Part II, Research",
  "/explainer": "§7 · Part II, Research",
  "/export": "§8 · Part II, Research",
};
export function AppLayout() {
  const runId = useSimulationStore((s) => s.runId);
  const replay = useSimulationStore((s) => s.replayRunId);
  const streamVersion = useSimulationStore((s) => s.streamVersion);
  useSimulationWebSocket(runId, replay ? "replay" : "live", streamVersion);
  const [presentation, setPresentation] = useState(false);
  const { pathname } = useLocation();
  const heading = descriptions[pathname];
  return (
    <div className={`app-shell${presentation ? " presentation-mode" : ""}`}>
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <Sidebar />
      <div className="app-body">
        <TopBar
          presentation={presentation}
          onPresentation={() => setPresentation((p) => !p)}
        />
        <main
          id="main-content"
          className={`main-content${pathname === "/" ? " live-main" : " secondary-page"}`}
        >
          {heading && (
            <div className="page-heading">
              <div className="eyebrow">{sections[pathname] ?? "TDCB laboratory"}</div>
              <h1>{heading[0]}</h1>
              <p>{heading[1]}</p>
            </div>
          )}
          <Suspense
            fallback={<div className="loading-state">Loading workspace...</div>}
          >
            <Outlet />
          </Suspense>
          <footer className="workspace-footer">
            <span>Trust-driven delegated consensus</span>
            <span>ABAC / TDCB / Reinforcement learning</span>
          </footer>
        </main>
      </div>
    </div>
  );
}
