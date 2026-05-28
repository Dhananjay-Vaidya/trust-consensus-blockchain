type StatusType = 'idle' | 'running' | 'paused' | 'completed' | 'error' | 'stopped';

const STATUS_COLORS: Record<StatusType, string> = {
  idle:      'var(--text-muted)',
  running:   'var(--green)',
  paused:    'var(--amber)',
  completed: 'var(--accent)',
  error:     'var(--red)',
  stopped:   'var(--red)',
};

interface StatusPillProps {
  status: StatusType;
}

export function StatusPill({ status }: StatusPillProps) {
  const color = STATUS_COLORS[status] ?? STATUS_COLORS.idle;
  const isPulsing = status === 'running';
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      fontSize: 12, color, fontWeight: 500,
      background: `${color}18`, border: `1px solid ${color}35`,
      padding: '4px 10px', borderRadius: 999,
    }}>
      <span style={{
        width: 7, height: 7, borderRadius: '50%', background: color,
        animation: isPulsing ? 'pulse-dot 1.4s ease-in-out infinite' : 'none',
        flexShrink: 0,
      }} />
      {status.toUpperCase()}
    </span>
  );
}
