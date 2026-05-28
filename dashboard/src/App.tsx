import { Navigate, Route, Routes } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

import { AppLayout } from './layout/AppLayout';
import { LiveSimulationPage }   from './pages/LiveSimulationPage';
import { MetricsExplorerPage }  from './pages/MetricsExplorerPage';
import { AttackLabPage }        from './pages/AttackLabPage';
import { ScenariosPage }        from './pages/ScenariosPage';
import { ResultsBrowserPage }   from './pages/ResultsBrowserPage';
import { CompareRunsPage }      from './pages/CompareRunsPage';
import { SystemExplainerPage }  from './pages/SystemExplainerPage';
import { ExportPage }           from './pages/ExportPage';
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts';

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
            background: 'var(--bg-elevated)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-strong)',
            fontFamily: 'var(--font-sans)',
            fontSize: 13,
          },
        }}
      />
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/"           element={<LiveSimulationPage />}  />
          <Route path="/metrics"    element={<MetricsExplorerPage />} />
          <Route path="/attack-lab" element={<AttackLabPage />}       />
          <Route path="/scenarios"  element={<ScenariosPage />}       />
          <Route path="/results"    element={<ResultsBrowserPage />}  />
          <Route path="/compare"    element={<CompareRunsPage />}     />
          <Route path="/explainer"  element={<SystemExplainerPage />} />
          <Route path="/export"     element={<ExportPage />}          />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}
