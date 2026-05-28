import type { ReactNode } from 'react';

interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}

export function SectionHeader({ title, subtitle, actions }: SectionHeaderProps) {
  return (
    <div style={{
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      paddingBottom: 10, marginBottom: 14,
      borderBottom: '1px solid var(--border)',
    }}>
      <div>
        <span style={{
          fontSize: 11, fontWeight: 600,
          textTransform: 'uppercase', letterSpacing: '0.1em',
          color: 'var(--text-secondary)',
        }}>
          {title}
        </span>
        {subtitle && (
          <p style={{ margin: '2px 0 0', fontSize: 12, color: 'var(--text-muted)' }}>{subtitle}</p>
        )}
      </div>
      {actions && <div style={{ display: 'flex', gap: 8 }}>{actions}</div>}
    </div>
  );
}
