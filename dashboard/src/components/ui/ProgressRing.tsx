interface ProgressRingProps {
  value: number;
  size?: number;
  strokeWidth?: number;
  color?: string;
}

export function ProgressRing({ value, size = 48, strokeWidth = 4, color = 'var(--accent)' }: ProgressRingProps) {
  const r = (size - strokeWidth) / 2;
  const circ = 2 * Math.PI * r;
  const dash = (Math.min(100, Math.max(0, value)) / 100) * circ;
  const center = size / 2;
  return (
    <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
      <circle cx={center} cy={center} r={r} fill="none"
        stroke="var(--border-strong)" strokeWidth={strokeWidth} />
      <circle cx={center} cy={center} r={r} fill="none"
        stroke={color} strokeWidth={strokeWidth}
        strokeDasharray={`${dash} ${circ}`}
        strokeLinecap="round"
        style={{ transition: 'stroke-dasharray 0.4s ease' }}
      />
      <text x={center} y={center}
        textAnchor="middle" dominantBaseline="middle"
        fontSize={size * 0.22} fontWeight={600}
        fill="var(--text-primary)"
        style={{ transform: `rotate(90deg)`, transformOrigin: `${center}px ${center}px` }}
      >
        {Math.round(value)}%
      </text>
    </svg>
  );
}
