import { useMemo } from 'react';

import { useNavigate } from 'react-router-dom';

import { RunComparisonCharts } from '../components/RunComparisonCharts';
import { RunResultsTable } from '../components/RunResultsTable';
import { useCompareRuns, useResults } from '../hooks/useResults';
import { useSimulationStore } from '../store/simulationStore';

export function CompareRunsPage() {
  const navigate = useNavigate();
  const { data: runs = [] } = useResults();
  const selectedComparisonRuns = useSimulationStore((state) => state.selectedComparisonRuns);
  const toggleComparisonRun = useSimulationStore((state) => state.toggleComparisonRun);
  const beginReplay = useSimulationStore((state) => state.beginReplay);

  const selectedRuns = useMemo(
    () => runs.filter((run) => selectedComparisonRuns.includes(run.run_id)),
    [runs, selectedComparisonRuns],
  );

  const comparison = useCompareRuns(selectedComparisonRuns, 'F1 Score');

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <div className="eyebrow">Multi-run analysis</div>
          <h2>Compare Completed Runs</h2>
          <p>Overlay result trajectories and inspect normalized radar summaries across selected runs.</p>
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

      <RunComparisonCharts selectedRuns={selectedRuns} comparison={comparison.data} />
    </div>
  );
}
