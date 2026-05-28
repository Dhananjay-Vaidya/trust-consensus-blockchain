import { useMemo } from 'react';
import {
  CartesianGrid, Legend, Line, LineChart,
  PolarAngleAxis, PolarGrid, Radar, RadarChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';

import { useCompareRuns, useResults } from '../hooks/useResults';
import { useSimulationStore } from '../store/simulationStore';
import { Badge, badgeVariant } from '../components/ui/Badge';
import type { ResultRunMetadata } from '../types';

const RUN_COLOURS = ['var(--accent)', 'var(--green)', 'var(--amber)', 'var(--purple)', 'var(--cyan)', 'var(--pink)'];

const TT = {
  contentStyle: { background: 'var(--bg-elevated)', border: '1px solid var(--border-strong)', borderRadius: 8 },
  labelStyle: { color: 'var(--text-secondary)', fontSize: 11 },
};

export function CompareRunsPage() {
  const { data: runs = [] } = useResults();
  const selectedComparisonRuns = useSimulationStore((s) => s.selectedComparisonRuns);
  const toggleComparisonRun    = useSimulationStore((s) => s.toggleComparisonRun);

  const selectedRuns = useMemo(
    () => (runs as ResultRunMetadata[]).filter((r) => selectedComparisonRuns.includes(r.run_id)),
    [runs, selectedComparisonRuns],
  );

  const comparison = useCompareRuns(selectedComparisonRuns, 'F1 Score');

  const lineData = useMemo(() => {
    if (!comparison.data) return [];
    const maxLen = Math.max(0, ...Object.values(comparison.data.series).map((s) => s.length));
    return Array.from({ length: maxLen }, (_, i) => {
      const row: Record<string, number> = { ep: i + 1 };
      selectedRuns.forEach((r) => { row[r.run_id.slice(0, 8)] = comparison.data!.series[r.run_id]?.[i] ?? 0; });
      return row;
    });
  }, [comparison.data, selectedRuns]);

  const radarData = useMemo(() => [
    { metric: 'Final F1',    ...Object.fromEntries(selectedRuns.map((r) => [r.run_id.slice(0,8), r.final_f1 ?? 0])) },
    { metric: 'Node Scale',  ...Object.fromEntries(selectedRuns.map((r) => [r.run_id.slice(0,8), Math.min(Number(r.nodes)/128, 1)])) },
    { metric: 'Episodes',    ...Object.fromEntries(selectedRuns.map((r) => [r.run_id.slice(0,8), Math.min(r.episodes/500, 1)])) },
    { metric: 'Throughput',  ...Object.fromEntries(selectedRuns.map((r) => [r.run_id.slice(0,8), 0.7])) },
    { metric: 'Convergence', ...Object.fromEntries(selectedRuns.map((r) => [r.run_id.slice(0,8), 0.65])) },
    { metric: 'Trust Sep.',  ...Object.fromEntries(selectedRuns.map((r) => [r.run_id.slice(0,8), r.final_f1 ?? 0])) },
  ], [selectedRuns]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Run chips */}
      <div>
        <div style={{ fontSize: 12, color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>
          Selected Runs (max 6)
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {(runs as ResultRunMetadata[]).slice(0, 20).map((r) => {
            const sel = selectedComparisonRuns.includes(r.run_id);
            const colIdx = selectedComparisonRuns.indexOf(r.run_id);
            const colour = colIdx >= 0 ? RUN_COLOURS[colIdx] : 'var(--text-muted)';
            return (
              <button key={r.run_id} onClick={() => toggleComparisonRun(r.run_id)}
                style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 12px',
                  borderRadius: 'var(--radius-xl)', cursor: 'pointer',
                  background: sel ? `${colour}18` : 'var(--bg-panel)',
                  border: `1px solid ${sel ? colour : 'var(--border)'}`,
                  color: sel ? colour : 'var(--text-secondary)', fontSize: 11, fontWeight: 500 }}>
                {sel && <span style={{ width: 8, height: 8, borderRadius: '50%', background: colour, flexShrink: 0 }} />}
                {r.run_id.slice(0, 8)}
                <Badge label={r.agent.toUpperCase()} variant={badgeVariant(r.agent)} />
                <Badge label={r.attack.toUpperCase()} variant={badgeVariant(r.attack)} />
              </button>
            );
          })}
          {runs.length === 0 && (
            <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>No completed runs. Run simulations first.</span>
          )}
        </div>
      </div>

      {selectedRuns.length < 2 && (
        <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)', fontSize: 13 }}>
          Select at least 2 runs above to compare.
        </div>
      )}

      {selectedRuns.length >= 2 && (
        <>
          {/* F1 Line Chart */}
          <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: '14px 16px' }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 10 }}>
              F1 Score Trajectory
            </div>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={lineData}>
                <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
                <XAxis dataKey="ep" stroke="var(--text-muted)" tick={{ fontSize: 10 }} />
                <YAxis domain={[0, 1.05]} stroke="var(--text-muted)" tick={{ fontSize: 10 }} />
                <Tooltip {...TT} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                {selectedRuns.map((r, i) => (
                  <Line key={r.run_id} type="monotone" dataKey={r.run_id.slice(0, 8)}
                    stroke={RUN_COLOURS[i]} strokeWidth={2} dot={false}
                    name={`${r.run_id.slice(0,8)} (${r.agent}/${r.attack})`} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Radar + Table */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
            <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: '14px 16px' }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 10 }}>
                Radar Comparison
              </div>
              <ResponsiveContainer width="100%" height={260}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="var(--border)" />
                  <PolarAngleAxis dataKey="metric" tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
                  <Tooltip {...TT} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  {selectedRuns.map((r, i) => (
                    <Radar key={r.run_id} name={r.run_id.slice(0, 8)}
                      dataKey={r.run_id.slice(0, 8)}
                      stroke={RUN_COLOURS[i]} fill={RUN_COLOURS[i]} fillOpacity={0.12} />
                  ))}
                </RadarChart>
              </ResponsiveContainer>
            </div>

            <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: '14px 16px', overflowX: 'auto' }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 10 }}>
                Summary Table
              </div>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
                <thead>
                  <tr>
                    <th style={{ padding: '6px 8px', textAlign: 'left', color: 'var(--text-secondary)', borderBottom: '1px solid var(--border)' }}>Metric</th>
                    {selectedRuns.map((r, i) => (
                      <th key={r.run_id} style={{ padding: '6px 8px', textAlign: 'center', borderBottom: '1px solid var(--border)', color: RUN_COLOURS[i] }}>
                        {r.run_id.slice(0, 8)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[
                    { label: 'Final F1', vals: selectedRuns.map((r) => r.final_f1?.toFixed(4) ?? '—') },
                    { label: 'Episodes', vals: selectedRuns.map((r) => String(r.episodes)) },
                    { label: 'Nodes',    vals: selectedRuns.map((r) => String(r.nodes)) },
                    { label: 'Attack',   vals: selectedRuns.map((r) => r.attack.toUpperCase()) },
                    { label: 'Agent',    vals: selectedRuns.map((r) => r.agent.toUpperCase()) },
                  ].map(({ label, vals }) => {
                    const numVals = vals.map((v) => parseFloat(v) || 0);
                    const best = Math.max(...numVals);
                    return (
                      <tr key={label} style={{ borderBottom: '1px solid var(--border)' }}>
                        <td style={{ padding: '6px 8px', color: 'var(--text-secondary)' }}>{label}</td>
                        {vals.map((v, i) => {
                          const isBest = numVals[i] === best && label === 'Final F1' && best > 0;
                          return (
                            <td key={i} style={{ padding: '6px 8px', textAlign: 'center',
                              fontWeight: isBest ? 700 : 400,
                              color: isBest ? 'var(--green)' : 'var(--text-primary)' }}>
                              {v}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
