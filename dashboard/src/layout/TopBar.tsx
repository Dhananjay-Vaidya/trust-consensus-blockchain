import { useLocation } from 'react-router-dom';

import { useSimulationStore } from '../store/simulationStore';

const ROUTE_TITLES: Record<string, string> = {
  '/':           'Live Simulation',
  '/metrics':    'Metrics Explorer',
  '/attack-lab': 'Attack Lab',
  '/scenarios':  'Scenarios',
  '/results':    'Results Browser',
  '/compare':    'Compare Runs',
  '/explainer':  'System Explainer',
  '/export':     'Export',
};

export function TopBar() {
  const { pathname } = useLocation();
  const status         = useSimulationStore((s) => s.status);
  const currentEpisode = useSimulationStore((s) => s.currentEpisode);
  const totalEpisodes  = useSimulationStore((s) => s.totalEpisodes);
  const latestStep     = useSimulationStore((s) => s.latestStep);

  const title = ROUTE_TITLES[pathname] ?? 'Dashboard';
  const progress = totalEpisodes > 0 ? (currentEpisode / totalEpisodes) * 100 : 0;
  const isRunning = status === 'running';

  return (
    <header style={{
      position: 'fixed', top: 0,
      left: 'var(--sidebar-w)', right: 0,
      height: 'var(--topbar-h)',
      background: 'rgba(10,13,20,0.85)',
      backdropFilter: 'blur(12px)',
      borderBottom: '1px solid var(--border)',
      display: 'flex', alignItems: 'center',
      padding: '0 20px', gap: 20, zIndex: 90,
    }}>
      {/* Breadcrumb */}
      <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', flexShrink: 0 }}>
        {title}
      </span>

      {/* Live run indicator */}
      {isRunning && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flex: 1, minWidth: 0 }}>
          <span style={{ fontSize: 12, color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
            Episode {currentEpisode} / {totalEpisodes}
          </span>
          <div style={{ width: 160, height: 4, background: 'var(--bg-active)', borderRadius: 2, flexShrink: 0 }}>
            <div style={{
              height: '100%', background: 'var(--accent)', borderRadius: 2,
              width: `${progress}%`, transition: 'width 0.3s',
            }} />
          </div>
          {latestStep && (
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--green)', whiteSpace: 'nowrap' }}>
              F1 {latestStep.f1_score.toFixed(3)}
            </span>
          )}
        </div>
      )}

      <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
        <span style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          TDCB-Sim v2.0
        </span>
      </div>
    </header>
  );
}
