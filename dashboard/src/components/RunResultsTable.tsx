import type { ResultRunMetadata } from '../types';

interface RunResultsTableProps {
  runs: ResultRunMetadata[];
  selectedRunIds: string[];
  onToggleRun: (runId: string) => void;
  onReplayRun: (runId: string) => void;
}

export function RunResultsTable({ runs, selectedRunIds, onToggleRun, onReplayRun }: RunResultsTableProps) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <h3>Completed Runs</h3>
          <p>Browse completed results, replay runs, and mark runs for comparison.</p>
        </div>
      </div>
      <div className="table-shell">
        <table className="results-table">
          <thead>
            <tr>
              <th>Select</th>
              <th>Run ID</th>
              <th>Agent</th>
              <th>Attack</th>
              <th>Nodes</th>
              <th>Final F1</th>
              <th>Episodes</th>
              <th>Replay</th>
              <th>CSV</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr key={run.run_id}>
                <td>
                  <input
                    type="checkbox"
                    checked={selectedRunIds.includes(run.run_id)}
                    onChange={() => onToggleRun(run.run_id)}
                  />
                </td>
                <td className="mono">{run.run_id}</td>
                <td>{run.agent.toUpperCase()}</td>
                <td>{run.attack.toUpperCase()}</td>
                <td>{run.nodes}</td>
                <td>{run.final_f1?.toFixed(4) ?? 'N/A'}</td>
                <td>{run.episodes}</td>
                <td>
                  <button className="button button-secondary" onClick={() => onReplayRun(run.run_id)}>
                    Replay
                  </button>
                </td>
                <td>
                  <a className="button button-ghost" href={`/results/${run.run_id}/download`}>
                    Download
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
