import { useNavigate } from 'react-router-dom';

import { RunResultsTable } from '../components/RunResultsTable';
import { useResults } from '../hooks/useResults';
import { useSimulationStore } from '../store/simulationStore';

export function ResultsBrowserPage() {
  const navigate = useNavigate();
  const { data: runs = [] } = useResults();
  const selectedComparisonRuns = useSimulationStore((state) => state.selectedComparisonRuns);
  const toggleComparisonRun = useSimulationStore((state) => state.toggleComparisonRun);
  const beginReplay = useSimulationStore((state) => state.beginReplay);

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <div className="eyebrow">Saved experiments</div>
          <h2>Results Browser</h2>
          <p>Review completed runs, download CSV metrics, and replay event streams over WebSocket.</p>
        </div>
      </header>

      <RunResultsTable
        runs={runs}
        selectedRunIds={selectedComparisonRuns}
        onToggleRun={toggleComparisonRun}
        onReplayRun={(runId) => {
          beginReplay(runId);
          navigate('/');
        }}
      />
    </div>
  );
}
