import { useMemo } from 'react';
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, ComposedChart,
  Legend, Line, ReferenceArea, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from 'recharts';

import { useSimulationStore } from '../store/simulationStore';
import { MetricCard } from './ui/MetricCard';

const TOOLTIP_STYLE = {
  contentStyle: { background: 'var(--bg-elevated)', border: '1px solid var(--border-strong)', borderRadius: 8 },
  labelStyle: { color: 'var(--text-secondary)', fontSize: 11 },
  itemStyle: { fontSize: 12 },
};

export function LiveMetricsPanel() {
  const episodeHistory = useSimulationStore((s) => s.episodeHistory);
  const latestStep     = useSimulationStore((s) => s.latestStep);
  const config         = useSimulationStore((s) => s.config);

  const window100 = episodeHistory.slice(-100);

  const metricsData = useMemo(() => window100.map((ep) => ({
    ep: ep.episode + 1,
    f1: Number(ep.f1_score.toFixed(4)),
    precision: Number(ep.precision.toFixed(4)),
    recall: Number(ep.recall.toFixed(4)),
    reward: Number(Math.max(0, Math.min(1, ep.reward / 200)).toFixed(4)),
  })), [window100]);

  const trustData = useMemo(() => {
    const byEp: Record<number, { honest: number; malicious: number }> = {};
    window100.forEach((ep) => {
      byEp[ep.episode] = { honest: ep.trust_separation > 0 ? 0.6 + ep.trust_separation / 2 : 0.5,
                           malicious: 0.5 - ep.trust_separation / 2 };
    });
    return Object.entries(byEp).map(([ep, v]) => ({ ep: Number(ep) + 1, ...v }));
  }, [window100]);

  const detectionData = useMemo(() => episodeHistory.slice(-20).map((ep) => ({
    ep: ep.episode + 1,
    detected: ep.byzantine_detections,
    verified: ep.transactions_verified,
  })), [episodeHistory]);

  const trend = useMemo(() => window100.map((ep) => ep.f1_score), [window100]);
  const last = episodeHistory[episodeHistory.length - 1];
  const prev = episodeHistory[episodeHistory.length - 2];
  const f1Delta = last && prev ? last.f1_score - prev.f1_score : undefined;

  // Attack reference area — highlight non-'none' attack runs
  const hasAttack = config.attack !== 'none';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, overflow: 'auto' }}>
      {/* KPI Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 10 }}>
        <MetricCard label="F1 Score" color="var(--accent)"
          value={latestStep ? latestStep.f1_score.toFixed(3) : '—'}
          delta={f1Delta} trend={trend} />
        <MetricCard label="Precision" color="var(--green)"
          value={latestStep ? latestStep.precision.toFixed(3) : '—'} />
        <MetricCard label="Recall" color="var(--cyan)"
          value={latestStep ? latestStep.recall.toFixed(3) : '—'} />
        <MetricCard label="TPS" color="var(--amber)"
          value={latestStep ? latestStep.transactions_verified : '—'} unit="tx/ep" />
      </div>

      {/* Reward + F1 ComposedChart */}
      <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: '12px 14px' }}>
        <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 8, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
          Episode Metrics
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <ComposedChart data={metricsData}>
            <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
            <XAxis dataKey="ep" stroke="var(--text-muted)" tick={{ fontSize: 10 }} />
            <YAxis yAxisId="left" domain={[0, 1]} stroke="var(--text-muted)" tick={{ fontSize: 10 }} />
            <YAxis yAxisId="right" orientation="right" domain={[0, 1]} stroke="var(--purple)" tick={{ fontSize: 10 }} />
            <Tooltip {...TOOLTIP_STYLE} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            {hasAttack && metricsData.length > 0 && (
              <ReferenceArea yAxisId="left"
                x1={metricsData[0]?.ep} x2={metricsData[metricsData.length - 1]?.ep}
                fill="var(--red)" fillOpacity={0.04} />
            )}
            <Line yAxisId="left" type="monotone" dataKey="f1" stroke="var(--accent)" strokeWidth={2} dot={false} name="F1" />
            <Line yAxisId="left" type="monotone" dataKey="precision" stroke="var(--green)" strokeWidth={1.5} strokeDasharray="4 2" dot={false} name="Precision" />
            <Line yAxisId="left" type="monotone" dataKey="recall" stroke="var(--cyan)" strokeWidth={1.5} strokeDasharray="4 2" dot={false} name="Recall" />
            <Area yAxisId="right" type="monotone" dataKey="reward" stroke="var(--purple)" fill="var(--purple)" fillOpacity={0.15} strokeWidth={1} dot={false} name="Reward" />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Trust Separation */}
      <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: '12px 14px' }}>
        <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 8, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
          Trust Separation
        </div>
        <ResponsiveContainer width="100%" height={150}>
          <AreaChart data={trustData}>
            <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
            <XAxis dataKey="ep" stroke="var(--text-muted)" tick={{ fontSize: 10 }} />
            <YAxis domain={[0, 1]} stroke="var(--text-muted)" tick={{ fontSize: 10 }} />
            <Tooltip {...TOOLTIP_STYLE} />
            <Area type="monotone" dataKey="honest" stroke="var(--green)" fill="var(--green)" fillOpacity={0.25} strokeWidth={1.5} name="Honest avg" />
            <Area type="monotone" dataKey="malicious" stroke="var(--red)" fill="var(--red)" fillOpacity={0.2} strokeWidth={1.5} name="Malicious avg" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Detection */}
      {detectionData.length > 0 && (
        <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: '12px 14px' }}>
          <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 8, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Byzantine Detections (last 20 ep)
          </div>
          <ResponsiveContainer width="100%" height={120}>
            <BarChart data={detectionData}>
              <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
              <XAxis dataKey="ep" stroke="var(--text-muted)" tick={{ fontSize: 10 }} />
              <YAxis stroke="var(--text-muted)" tick={{ fontSize: 10 }} allowDecimals={false} />
              <Tooltip {...TOOLTIP_STYLE} />
              <Bar dataKey="detected" fill="var(--red)" opacity={0.8} radius={[3, 3, 0, 0]} name="Byzantine" />
              <Bar dataKey="verified" fill="var(--green)" opacity={0.5} radius={[3, 3, 0, 0]} name="Verified tx" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
