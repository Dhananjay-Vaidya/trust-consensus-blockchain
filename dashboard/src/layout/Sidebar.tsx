import { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';

import { useSimulationStore } from '../store/simulationStore';

const NAV_ITEMS = [
  { icon: '⬡', label: 'Live Simulation',   to: '/',           end: true },
  { icon: '📊', label: 'Metrics Explorer', to: '/metrics'         },
  { icon: '🔬', label: 'Attack Lab',        to: '/attack-lab'      },
  { icon: '🏛', label: 'Scenarios',         to: '/scenarios'       },
  { icon: '📁', label: 'Results',           to: '/results'         },
  { icon: '⚖', label: 'Compare Runs',      to: '/compare'         },
  { icon: '📐', label: 'System Explainer',  to: '/explainer'       },
  { icon: '📄', label: 'Export',            to: '/export'          },
];

export function Sidebar() {
  const runId    = useSimulationStore((s) => s.runId);
  const status   = useSimulationStore((s) => s.status);
  const [apiOnline, setApiOnline] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    const check = async () => {
      try {
        const r = await fetch('/health');
        setApiOnline(r.ok);
      } catch { setApiOnline(false); }
    };
    check();
    const id = setInterval(check, 5000);
    return () => clearInterval(id);
  }, []);

  return (
    <aside style={{
      position: 'fixed', top: 0, left: 0, height: '100vh',
      width: collapsed ? 52 : 'var(--sidebar-w)',
      background: 'var(--bg-surface)', borderRight: '1px solid var(--border)',
      display: 'flex', flexDirection: 'column',
      transition: 'width 200ms ease', zIndex: 100, overflow: 'hidden',
    }}>
      {/* Logo */}
      <div style={{
        padding: collapsed ? '18px 14px' : '18px 18px 14px',
        display: 'flex', alignItems: 'center', gap: 10,
        borderBottom: '1px solid var(--border)',
        cursor: 'pointer', flexShrink: 0,
      }} onClick={() => setCollapsed((c) => !c)}>
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <polygon points="12,2 22,7 22,17 12,22 2,17 2,7"
            stroke="var(--accent)" strokeWidth="1.5" fill="var(--accent-dim)" />
          <text x="12" y="15.5" textAnchor="middle" fontSize="8" fontWeight="700"
            fill="var(--accent)" fontFamily="var(--font-mono)">TC</text>
        </svg>
        {!collapsed && (
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.2 }}>
              TDCB·Sim
            </div>
            <div style={{ fontSize: 10, color: 'var(--text-secondary)' }}>v2.0</div>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: '8px 0', overflowY: 'auto' }}>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            title={collapsed ? item.label : undefined}
            style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: 10,
              padding: collapsed ? '10px 14px' : '10px 16px',
              fontSize: 12, fontWeight: 500,
              color: isActive ? 'var(--accent)' : 'var(--text-secondary)',
              background: isActive ? 'var(--accent-dim)' : 'transparent',
              borderLeft: isActive ? '2px solid var(--accent)' : '2px solid transparent',
              textDecoration: 'none', transition: 'all 120ms',
              whiteSpace: 'nowrap', overflow: 'hidden',
            })}
            onMouseEnter={(e) => {
              const el = e.currentTarget as HTMLElement;
              if (!el.style.color.includes('accent')) {
                el.style.background = 'var(--bg-hover)';
              }
            }}
            onMouseLeave={(e) => {
              const el = e.currentTarget as HTMLElement;
              if (!el.style.color.includes('accent')) {
                el.style.background = 'transparent';
              }
            }}
          >
            <span style={{ fontSize: 15, flexShrink: 0 }}>{item.icon}</span>
            {!collapsed && item.label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      {!collapsed && (
        <div style={{
          padding: '12px 16px', borderTop: '1px solid var(--border)',
          fontSize: 11, color: 'var(--text-secondary)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
            <span style={{
              width: 7, height: 7, borderRadius: '50%', flexShrink: 0,
              background: apiOnline ? 'var(--green)' : 'var(--red)',
              animation: apiOnline ? 'pulse-dot 2s ease-in-out infinite' : 'none',
            }} />
            API: {apiOnline ? 'connected' : 'offline'}
          </div>
          {runId && status === 'running' && (
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--accent)' }}>
              ▶ {runId.slice(0, 8)}…
            </div>
          )}
        </div>
      )}
    </aside>
  );
}
