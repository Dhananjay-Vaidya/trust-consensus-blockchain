type Variant = 'green' | 'red' | 'amber' | 'purple' | 'cyan' | 'blue' | 'muted';

interface BadgeProps {
  label: string;
  variant?: Variant;
}

const VARIANT_STYLES: Record<Variant, { bg: string; color: string }> = {
  green:  { bg: 'var(--green-dim)',  color: 'var(--green)'  },
  red:    { bg: 'var(--red-dim)',    color: 'var(--red)'    },
  amber:  { bg: 'var(--amber-dim)', color: 'var(--amber)'  },
  purple: { bg: 'var(--purple-dim)',color: 'var(--purple)' },
  cyan:   { bg: 'var(--cyan-dim)',  color: 'var(--cyan)'   },
  blue:   { bg: 'var(--accent-dim)',color: 'var(--accent)' },
  muted:  { bg: 'rgba(255,255,255,0.06)', color: 'var(--text-secondary)' },
};

export function Badge({ label, variant = 'muted' }: BadgeProps) {
  const { bg, color } = VARIANT_STYLES[variant];
  return (
    <span style={{
      background: bg, color,
      fontSize: 10, fontWeight: 500,
      padding: '3px 9px', borderRadius: 999,
      display: 'inline-block', lineHeight: 1.6,
      letterSpacing: '0.04em',
      border: `1px solid ${color}40`,
    }}>
      {label}
    </span>
  );
}

export function badgeVariant(name: string): Variant {
  const map: Record<string, Variant> = {
    nma: 'amber', cra: 'red', aaa: 'purple', bfi: 'red', tdp: 'amber',
    rl: 'cyan', drl: 'blue', marl: 'green',
    none: 'muted',
    tdcb: 'blue', pbft: 'cyan', static_dpos: 'purple', majority: 'amber', random: 'muted',
  };
  return map[name.toLowerCase()] ?? 'muted';
}
