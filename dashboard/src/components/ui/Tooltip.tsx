import { useState, type ReactNode } from 'react';

interface TooltipProps {
  content: string | ReactNode;
  children: ReactNode;
}

export function Tooltip({ content, children }: TooltipProps) {
  const [visible, setVisible] = useState(false);
  return (
    <span
      style={{ position: 'relative', display: 'inline-flex' }}
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
    >
      {children}
      {visible && (
        <span style={{
          position: 'absolute', bottom: '100%', left: '50%',
          transform: 'translateX(-50%)', marginBottom: 6,
          background: 'var(--bg-elevated)', border: '1px solid var(--border-strong)',
          borderRadius: 'var(--radius-sm)', padding: '5px 10px',
          fontSize: 11, color: 'var(--text-primary)',
          whiteSpace: 'nowrap', zIndex: 1000,
          pointerEvents: 'none',
          boxShadow: '0 4px 16px rgba(0,0,0,0.4)',
        }}>
          {content}
          <span style={{
            position: 'absolute', top: '100%', left: '50%',
            transform: 'translateX(-50%)',
            borderLeft: '5px solid transparent',
            borderRight: '5px solid transparent',
            borderTop: '5px solid var(--border-strong)',
          }} />
        </span>
      )}
    </span>
  );
}
