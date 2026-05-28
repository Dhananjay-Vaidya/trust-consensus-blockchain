import { useMemo } from 'react';
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import type { CompareRunsPayload, ResultRunMetadata } from '../types';

interface RunComparisonChartsProps {
  selectedRuns: ResultRunMetadata[];
  comparison: CompareRunsPayload | undefined;
}

export function RunComparisonCharts({ selectedRuns, comparison }: RunComparisonChartsProps) {
  const lineData = useMemo(() => {
    if (!comparison) return [];
    const maxLen = Math.max(0, ...Object.values(comparison.series).map((series) => series.length));
    return Array.from({ length: maxLen }, (_, index) => {
      const row: Record<string, number> = { episode: index + 1 };
      for (const run of selectedRuns) {
        row[run.run_id] = comparison.series[run.run_id]?.[index] ?? 0;
      }
      return row;
    });
  }, [comparison, selectedRuns]);

  const radarData = useMemo(() => {
    return selectedRuns.map((run) => ({
      runId: run.run_id,
      finalF1: run.final_f1 ?? 0,
      normalizedEpisodes: Math.min(run.episodes / 100, 1),
      nodes: Math.min(Number(run.nodes) / 64, 1),
    }));
  }, [selectedRuns]);

  return (
    <div className="compare-grid">
      <section className="panel">
        <div className="panel-header">
          <div>
            <h3>Metric Overlay</h3>
            <p>Episode-wise comparison for the selected metric.</p>
          </div>
        </div>
        <div className="chart-shell">
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={lineData}>
              <CartesianGrid stroke="#243146" strokeDasharray="3 3" />
              <XAxis dataKey="episode" stroke="#7f8ea3" />
              <YAxis stroke="#7f8ea3" domain={[0, 1.05]} />
              <Tooltip />
              <Legend />
              {selectedRuns.map((run, index) => (
                <Line
                  key={run.run_id}
                  type="monotone"
                  dataKey={run.run_id}
                  stroke={['#5cc7ff', '#6ee7b7', '#fbbf24', '#f472b6'][index % 4]}
                  strokeWidth={2}
                  dot={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h3>Final Metric Radar</h3>
            <p>Compact multi-run summary using normalized axes.</p>
          </div>
        </div>
        <div className="chart-shell">
          <ResponsiveContainer width="100%" height={320}>
            <RadarChart outerRadius={110} data={[
              { metric: 'Final F1', ...Object.fromEntries(radarData.map((d) => [d.runId, d.finalF1])) },
              { metric: 'Episodes', ...Object.fromEntries(radarData.map((d) => [d.runId, d.normalizedEpisodes])) },
              { metric: 'Node Scale', ...Object.fromEntries(radarData.map((d) => [d.runId, d.nodes])) },
            ]}>
              <PolarGrid stroke="#243146" />
              <PolarAngleAxis dataKey="metric" stroke="#a7b6cb" />
              {selectedRuns.map((run, index) => (
                <Radar
                  key={run.run_id}
                  name={run.run_id}
                  dataKey={run.run_id}
                  stroke={['#5cc7ff', '#6ee7b7', '#fbbf24', '#f472b6'][index % 4]}
                  fill={['#5cc7ff', '#6ee7b7', '#fbbf24', '#f472b6'][index % 4]}
                  fillOpacity={0.15}
                />
              ))}
              <Legend />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  );
}
