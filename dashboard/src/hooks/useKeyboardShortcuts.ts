import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useSimulationStore } from "../store/simulationStore";
export function useKeyboardShortcuts() {
  const navigate = useNavigate();
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (
        target.isContentEditable ||
        ["INPUT", "SELECT", "TEXTAREA"].includes(target.tagName)
      )
        return;
      if (e.key === "Escape") {
        useSimulationStore.getState().selectNode(null);
        return;
      }
      if (e.altKey && !e.ctrlKey && !e.metaKey) {
        const routes: Record<string, string> = {
          "1": "/",
          "2": "/metrics",
          "3": "/attack-lab",
          "4": "/scenarios",
          "5": "/experiments",
          "6": "/compare",
          "7": "/explainer",
          "8": "/export",
        };
        if (routes[e.key]) {
          e.preventDefault();
          navigate(routes[e.key]);
        }
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [navigate]);
}
