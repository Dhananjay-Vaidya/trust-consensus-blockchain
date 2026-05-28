import type { ReactNode } from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  delta?: number;
  deltaLabel?: string;
  color?: string;
  icon?: ReactNode;
  trend?: number[];
}

function Sparkline({ data, color }: { data: number[]; color: string }) {
  if (data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const w = 60; const h = 24;
  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * w;
    const y = h - ((v - min) / range) * h;
    return `${x},${y}`;
  }).join(' ');
  return (
    <svg width={w} height={h} style={{ display: 'block', marginTop: 4 }}>
      <polyline points={pts} fill="none" stroke={color} strokeWidth={1.5} strokeOpacity={0.6} />
    </svg>
  );
}

export function MetricCard({ label, value, unit, delta, deltaLabel, color = 'var(--accent)', icon, trend }: MetricCardProps) {
  return (
    <div style={{
      background: 'var(--bg-panel)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)', padding: '1rem 1.25rem',
      display: 'flex', flexDirection: 'column', gap: 4,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        {icon && <span style={{ color, opacity: 0.8, fontSize: 16 }}>{icon}</span>}
        <span style={{ fontSize: 11, color: 'var(--text-secondary)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
          {label}
        </span>
      </div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
        <span style={{ fontSize: 22, fontWeight: 600, color, lineHeight: 1.2 }}>
          {typeof value === 'number' ? value.toLocaleString() : value}
        </span>
        {unit && <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{unit}</span>}
      </div>
      {trend && <Sparkline data={trend} color={color} />}
      {delta !== undefined && (
        <span style={{
          fontSize: 11, fontWeight: 500,
          color: delta >= 0 ? 'var(--green)' : 'var(--red)',
        }}>
          {delta >= 0 ? '+' : ''}{delta.toFixed(3)}{deltaLabel ? ` ${deltaLabel}` : ''}
        </span>
      )}
    </div>
  );
}
