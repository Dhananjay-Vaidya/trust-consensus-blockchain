import { useLocation } from "react-router-dom";
import { CornersOut, CornersIn } from "@phosphor-icons/react";
import { useSimulationStore } from "../store/simulationStore";
const titles: Record<string, string> = {
  "/": "Live simulation",
  "/metrics": "Metrics explorer",
  "/attack-lab": "Attack laboratory",
  "/scenarios": "Scenario library",
  "/experiments": "Experiment results",
  "/compare": "Compare runs",
  "/explainer": "System architecture",
  "/export": "Export & present",
};
export function TopBar({
  presentation,
  onPresentation,
}: {
  presentation: boolean;
  onPresentation: () => void;
}) {
  const { pathname } = useLocation();
  const status = useSimulationStore((s) => s.status);
  const episode = useSimulationStore((s) => s.currentEpisode);
  const total = useSimulationStore((s) => s.totalEpisodes);
  return (
    <header className="topbar">
      <div className="breadcrumb">
        <span>Research workspace</span>
        <span className="breadcrumb-slash">/</span>
        <strong>{titles[pathname] ?? "Dashboard"}</strong>
      </div>
      <div className="topbar-actions">
        {status === "running" && (
          <span className="running-label">
            <span className="status-dot online" />
            Episode {episode} / {total || "?"}
          </span>
        )}
        <button
          className={`quiet-button ${presentation ? "selected" : ""}`}
          onClick={onPresentation}
          aria-pressed={presentation}
          title="Hide navigation for presentation"
        >
          {presentation ? <CornersIn size={18} /> : <CornersOut size={18} />}
          <span>{presentation ? "Exit presentation" : "Present"}</span>
        </button>
      </div>
    </header>
  );
}
