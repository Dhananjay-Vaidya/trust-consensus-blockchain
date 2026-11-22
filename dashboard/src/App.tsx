import { lazy } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { Toaster } from "react-hot-toast";

import { AppLayout } from "./layout/AppLayout";
const LiveSimulationPage = lazy(() =>
  import("./pages/LiveSimulationPage").then((module) => ({
    default: module.LiveSimulationPage,
  })),
);
const MetricsExplorerPage = lazy(() =>
  import("./pages/MetricsExplorerPage").then((module) => ({
    default: module.MetricsExplorerPage,
  })),
);
const AttackLabPage = lazy(() =>
  import("./pages/AttackLabPage").then((module) => ({
    default: module.AttackLabPage,
  })),
);
const ScenariosPage = lazy(() =>
  import("./pages/ScenariosPage").then((module) => ({
    default: module.ScenariosPage,
  })),
);
const ResultsBrowserPage = lazy(() =>
  import("./pages/ResultsBrowserPage").then((module) => ({
    default: module.ResultsBrowserPage,
  })),
);
const CompareRunsPage = lazy(() =>
  import("./pages/CompareRunsPage").then((module) => ({
    default: module.CompareRunsPage,
  })),
);
const SystemExplainerPage = lazy(() =>
  import("./pages/SystemExplainerPage").then((module) => ({
    default: module.SystemExplainerPage,
  })),
);
const ExportPage = lazy(() =>
  import("./pages/ExportPage").then((module) => ({
    default: module.ExportPage,
  })),
);
import { useKeyboardShortcuts } from "./hooks/useKeyboardShortcuts";

function ShortcutsProvider() {
  useKeyboardShortcuts();
  return null;
}

export default function App() {
  return (
    <>
      <ShortcutsProvider />
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: "var(--bg-elevated)",
            color: "var(--text-primary)",
            border: "1px solid var(--border-strong)",
            fontFamily: "var(--font-sans)",
            fontSize: 13,
          },
        }}
      />
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<LiveSimulationPage />} />
          <Route path="/metrics" element={<MetricsExplorerPage />} />
          <Route path="/attack-lab" element={<AttackLabPage />} />
          <Route path="/scenarios" element={<ScenariosPage />} />
          <Route path="/experiments" element={<ResultsBrowserPage />} />
          <Route path="/compare" element={<CompareRunsPage />} />
          <Route path="/explainer" element={<SystemExplainerPage />} />
          <Route path="/export" element={<ExportPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}
