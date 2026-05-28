import { useMemo, useState } from 'react';
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, ComposedChart,
  Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';

import { useResults } from '../hooks/useResults';
import { apiClient } from '../api/client';
import { useQuery } from '@tanstack/react-query';
import type { ResultRunMetadata } from '../types';
import { Badge, badgeVariant } from '../components/ui/Badge';

const TT = {
  contentStyle: { background: 'var(--bg-elevated)', border: '1px solid var(--border-strong)', borderRadius: 8 },
  labelStyle: { color: 'var(--text-secondary)', fontSize: 11 },
};

function Panel({ title, children, h = 200 }: { title: string; children: React.ReactNode; h?: number }) {
  return (
    <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: '12px 14px' }}>
      <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-secondary)', marginBottom: 8 }}>{title}</div>
      <div style={{ height: h }}>{children}</div>
    </div>
  );
}

export function MetricsExplorerPage() {
  const { data: runs = [] } = useResults();
  const [selectedRunId, setSelectedRunId] = useState<string>('');
  const [scrubber, setScrubber] = useState(100);

  const { data: metrics = [] } = useQuery({
    queryKey: ['metrics', selectedRunId],
    enabled: !!selectedRunId,
    queryFn: async () => {
      const r = await apiClient.get<Record<string, number>[]>(`/results/${selectedRunId}/metrics`);
      return r.data;
    },
  });

  const scraped = useMemo(() => metrics.slice(0, Math.ceil(metrics.length * scrubber / 100)), [metrics, scrubber]);

  const chartData = useMemo(() => scraped.map((row, i) => ({
    ep: i + 1,
    f1: Number((row['F1 Score'] ?? 0).toFixed(4)),
    precision: Number((row['Precision'] ?? 0).toFixed(4)),
    recall: Number((row['Recall'] ?? 0).toFixed(4)),
    reward: Number((row['Reward'] ?? 0).toFixed(2)),
    blocks: row['Blockchain Length'] ?? 0,
    detections: row['Byzantine Detections'] ?? 0,
    trust_sep: Number((row['Trust Separation'] ?? 0).toFixed(4)),
  })), [scraped]);

  const selectedRun = runs.find((r: ResultRunMetadata) => r.run_id === selectedRunId);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Run Selector */}
      <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
        <select value={selectedRunId} onChange={(e) => setSelectedRunId(e.target.value)}
          style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', padding: '8px 12px', color: 'var(--text-primary)', fontSize: 13, minWidth: 320 }}>
          <option value="">Select a completed run…</option>
          {runs.map((r: ResultRunMetadata) => (
            <option key={r.run_id} value={r.run_id}>
              {r.run_id.slice(0, 8)} | {r.agent.toUpperCase()} | {r.attack.toUpperCase()} | {r.nodes}n | F1={r.final_f1?.toFixed(3) ?? '?'}
            </option>
          ))}
        </select>
        {selectedRun && (
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            <Badge label={selectedRun.agent.toUpperCase()} variant={badgeVariant(selectedRun.agent)} />
            <Badge label={selectedRun.attack.toUpperCase()} variant={badgeVariant(selectedRun.attack)} />
            <Badge label={`${selectedRun.nodes} nodes`} variant="muted" />
            <Badge label={`${selectedRun.episodes} episodes`} variant="muted" />
          </div>
        )}
      </div>

      {/* Scrubber */}
      {metrics.length > 0 && (
        <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: '12px 14px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
            <span style={{ fontSize: 11, color: 'var(--text-secondary)', fontWeight: 600 }}>EPISODE SCRUBBER</span>
            <span style={{ fontSize: 11, color: 'var(--accent)' }}>Episode {Math.ceil(metrics.length * scrubber / 100)} / {metrics.length}</span>
          </div>
          <input type="range" min={1} max={100} value={scrubber}
            onChange={(e) => setScrubber(Number(e.target.value))}
            style={{ width: '100%', accentColor: 'var(--accent)' }} />
        </div>
      )}

      {chartData.length === 0 && (
        <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 40, fontSize: 13 }}>
          Select a completed run to explore its metrics.
        </div>
      )}

      {chartData.length > 0 && (
        <>
          {/* 2×3 chart grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <Panel title="F1 / Precision / Recall" h={200}>
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData}>
                  <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
                  <XAxis dataKey="ep" stroke="var(--text-muted)" tick={{ fontSize: 10 }} />
                  <YAxis domain={[0, 1]} stroke="var(--text-muted)" tick={{ fontSize: 10 }} />
                  <Tooltip {...TT} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Line type="monotone" dataKey="f1" stroke="var(--accent)" strokeWidth={2} dot={false} name="F1" />
                  <Line type="monotone" dataKey="precision" stroke="var(--green)" strokeWidth={1.5} strokeDasharray="4 2" dot={false} name="Prec" />
                  <Line type="monotone" dataKey="recall" stroke="var(--cyan)" strokeWidth={1.5} strokeDasharray="4 2" dot={false} name="Recall" />
                </ComposedChart>
              </ResponsiveContainer>
            </Panel>

            <Panel title="Cumulative Reward" h={200}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
                  <XAxis dataKey="ep" stroke="var(--text-muted)" tick={{ fontSize: 10 }} />
                  <YAxis stroke="var(--text-muted)" tick={{ fontSize: 10 }} />
                  <Tooltip {...TT} />
                  <Area type="monotone" dataKey="reward" stroke="var(--purple)" fill="var(--purple)" fillOpacity={0.2} dot={false} name="Reward" />
                </AreaChart>
              </ResponsiveContainer>
            </Panel>

            <Panel title="Trust Separation" h={200}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
                  <XAxis dataKey="ep" stroke="var(--text-muted)" tick={{ fontSize: 10 }} />
                  <YAxis domain={[-1, 1]} stroke="var(--text-muted)" tick={{ fontSize: 10 }} />
                  <Tooltip {...TT} />
                  <Area type="monotone" dataKey="trust_sep" stroke="var(--green)" fill="var(--green)" fillOpacity={0.2} dot={false} name="Separation" />
                </AreaChart>
              </ResponsiveContainer>
            </Panel>

            <Panel title="Blockchain Growth" h={200}>
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData}>
                  <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
                  <XAxis dataKey="ep" stroke="var(--text-muted)" tick={{ fontSize: 10 }} />
                  <YAxis stroke="var(--text-muted)" tick={{ fontSize: 10 }} />
                  <Tooltip {...TT} />
                  <Line type="monotone" dataKey="blocks" stroke="var(--accent)" strokeWidth={2} dot={false} name="Blocks" />
                </ComposedChart>
              </ResponsiveContainer>
            </Panel>

            <Panel title="Byzantine Detections" h={200}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
                  <XAxis dataKey="ep" stroke="var(--text-muted)" tick={{ fontSize: 10 }} />
                  <YAxis stroke="var(--text-muted)" tick={{ fontSize: 10 }} allowDecimals={false} />
                  <Tooltip {...TT} />
                  <Bar dataKey="detections" fill="var(--red)" opacity={0.8} radius={[2, 2, 0, 0]} name="Detected" />
                </BarChart>
              </ResponsiveContainer>
            </Panel>

            <Panel title="F1 Histogram" h={200}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={(() => {
                  const bins = Array.from({ length: 10 }, (_, i) => ({ range: `${(i / 10).toFixed(1)}`, count: 0 }));
                  chartData.forEach((d) => { const idx = Math.min(9, Math.floor(d.f1 * 10)); bins[idx].count++; });
                  return bins;
                })()}>
                  <XAxis dataKey="range" stroke="var(--text-muted)" tick={{ fontSize: 10 }} />
                  <YAxis stroke="var(--text-muted)" tick={{ fontSize: 10 }} allowDecimals={false} />
                  <Tooltip {...TT} />
                  <Bar dataKey="count" fill="var(--accent)" opacity={0.7} radius={[2, 2, 0, 0]} name="Count" />
                </BarChart>
              </ResponsiveContainer>
            </Panel>
          </div>
        </>
      )}
    </div>
  );
}
