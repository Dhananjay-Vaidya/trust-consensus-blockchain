import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useResults } from '../hooks/useResults';
import { useSimulationStore } from '../store/simulationStore';
import { Badge, badgeVariant } from '../components/ui/Badge';
import { MetricCard } from '../components/ui/MetricCard';
import type { ResultRunMetadata } from '../types';

type SortKey = keyof ResultRunMetadata;
type SortDir = 'asc' | 'desc';

export function ResultsBrowserPage() {
  const navigate = useNavigate();
  const { data: runs = [], refetch } = useResults();
  const selectedComparisonRuns = useSimulationStore((s) => s.selectedComparisonRuns);
  const toggleComparisonRun    = useSimulationStore((s) => s.toggleComparisonRun);
  const beginReplay            = useSimulationStore((s) => s.beginReplay);

  const [sortKey, setSortKey] = useState<SortKey>('final_f1');
  const [sortDir, setSortDir] = useState<SortDir>('desc');
  const [agentFilter, setAgentFilter]   = useState('all');
  const [attackFilter, setAttackFilter] = useState('all');
  const [search, setSearch]             = useState('');

  const handleSort = (k: SortKey) => {
    if (k === sortKey) { setSortDir((d) => d === 'asc' ? 'desc' : 'asc'); }
    else { setSortKey(k); setSortDir('desc'); }
  };

  const filtered = useMemo(() => {
    let r = runs as ResultRunMetadata[];
    if (agentFilter !== 'all') r = r.filter((x) => x.agent === agentFilter);
    if (attackFilter !== 'all') r = r.filter((x) => x.attack === attackFilter);
    if (search) r = r.filter((x) => x.run_id.includes(search));
    return [...r].sort((a, b) => {
      const va = a[sortKey] ?? 0;
      const vb = b[sortKey] ?? 0;
      const cmp = va < vb ? -1 : va > vb ? 1 : 0;
      return sortDir === 'asc' ? cmp : -cmp;
    });
  }, [runs, agentFilter, attackFilter, search, sortKey, sortDir]);

  const bestF1  = Math.max(0, ...runs.map((r: ResultRunMetadata) => r.final_f1 ?? 0));
  const bestRun = (runs as ResultRunMetadata[]).find((r) => r.final_f1 === bestF1);

  const Th = ({ label, sk }: { label: string; sk: SortKey }) => (
    <th onClick={() => handleSort(sk)} style={{
      padding: '8px 10px', textAlign: 'left', fontSize: 10, fontWeight: 600,
      textTransform: 'uppercase', letterSpacing: '0.08em',
      borderBottom: '1px solid var(--border)', cursor: 'pointer', whiteSpace: 'nowrap',
      color: sortKey === sk ? 'var(--accent)' : 'var(--text-secondary)',
    }}>
      {label} {sortKey === sk ? (sortDir === 'asc' ? '↑' : '↓') : ''}
    </th>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Summary cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 10 }}>
        <MetricCard label="Total Runs" value={runs.length} color="var(--accent)" />
        <MetricCard label="Best F1" value={bestF1.toFixed(4)} color="var(--green)"
          deltaLabel={bestRun ? `(${bestRun.run_id.slice(0,8)})` : undefined} />
        <MetricCard label="Agents Tested" value={new Set(runs.map((r: ResultRunMetadata) => r.agent)).size} color="var(--cyan)" />
        <MetricCard label="Attacks Tested" value={new Set(runs.map((r: ResultRunMetadata) => r.attack)).size} color="var(--amber)" />
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
        <input placeholder="Search run ID…" value={search} onChange={(e) => setSearch(e.target.value)}
          style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)',
            padding: '6px 12px', color: 'var(--text-primary)', fontSize: 12, width: 180 }} />
        {(['all','rl','drl','marl'] as const).map((a) => (
          <button key={a} onClick={() => setAgentFilter(a)}
            style={{ padding: '6px 12px', borderRadius: 'var(--radius-sm)', fontSize: 11, fontWeight: 600, cursor: 'pointer',
              background: agentFilter === a ? 'var(--accent-dim)' : 'var(--bg-panel)',
              border: `1px solid ${agentFilter === a ? 'var(--accent)' : 'var(--border)'}`,
              color: agentFilter === a ? 'var(--accent)' : 'var(--text-secondary)' }}>
            {a.toUpperCase()}
          </button>
        ))}
        {(['all','nma','cra','aaa','bfi','tdp','none'] as const).map((a) => (
          <button key={a} onClick={() => setAttackFilter(a)}
            style={{ padding: '6px 12px', borderRadius: 'var(--radius-sm)', fontSize: 11, fontWeight: 600, cursor: 'pointer',
              background: attackFilter === a ? 'var(--red-dim)' : 'var(--bg-panel)',
              border: `1px solid ${attackFilter === a ? 'var(--red)' : 'var(--border)'}`,
              color: attackFilter === a ? 'var(--red)' : 'var(--text-secondary)' }}>
            {a.toUpperCase()}
          </button>
        ))}
        <button onClick={() => void refetch()}
          style={{ marginLeft: 'auto', padding: '6px 14px', borderRadius: 'var(--radius-sm)',
            background: 'var(--bg-panel)', border: '1px solid var(--border)',
            color: 'var(--text-secondary)', fontSize: 12, cursor: 'pointer' }}>
          ↻ Refresh
        </button>
      </div>

      {/* Table */}
      <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
            <thead>
              <tr style={{ background: 'var(--bg-elevated)' }}>
                <th style={{ padding: '8px 10px', borderBottom: '1px solid var(--border)', width: 32 }} />
                <Th label="Run ID" sk="run_id" />
                <Th label="Agent" sk="agent" />
                <Th label="Attack" sk="attack" />
                <Th label="Nodes" sk="nodes" />
                <Th label="Final F1" sk="final_f1" />
                <Th label="Episodes" sk="episodes" />
                <th style={{ padding: '8px 10px', textAlign: 'left', fontSize: 10, fontWeight: 600,
                  textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-secondary)',
                  borderBottom: '1px solid var(--border)' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={8} style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
                    No runs found. Start a simulation to generate results.
                  </td>
                </tr>
              )}
              {filtered.map((run: ResultRunMetadata) => (
                <tr key={run.run_id} style={{ borderBottom: '1px solid var(--border)', transition: 'background 120ms' }}
                  onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = 'var(--bg-hover)'; }}
                  onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = 'transparent'; }}>
                  <td style={{ padding: '8px 10px' }}>
                    <input type="checkbox"
                      checked={selectedComparisonRuns.includes(run.run_id)}
                      onChange={() => toggleComparisonRun(run.run_id)}
                      style={{ accentColor: 'var(--accent)' }} />
                  </td>
                  <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--accent)' }}>
                    {run.run_id.slice(0, 16)}
                  </td>
                  <td style={{ padding: '8px 10px' }}><Badge label={run.agent.toUpperCase()} variant={badgeVariant(run.agent)} /></td>
                  <td style={{ padding: '8px 10px' }}><Badge label={run.attack.toUpperCase()} variant={badgeVariant(run.attack)} /></td>
                  <td style={{ padding: '8px 10px', color: 'var(--text-secondary)' }}>{run.nodes}</td>
                  <td style={{ padding: '8px 10px', fontWeight: 600,
                    color: (run.final_f1 ?? 0) > 0.9 ? 'var(--green)' : (run.final_f1 ?? 0) > 0.75 ? 'var(--amber)' : 'var(--red)' }}>
                    {run.final_f1?.toFixed(4) ?? '—'}
                  </td>
                  <td style={{ padding: '8px 10px', color: 'var(--text-secondary)' }}>{run.episodes}</td>
                  <td style={{ padding: '8px 10px' }}>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <button onClick={() => { beginReplay(run.run_id); navigate('/'); }}
                        style={{ padding: '4px 10px', borderRadius: 'var(--radius-sm)', fontSize: 11,
                          background: 'var(--bg-active)', border: '1px solid var(--border)',
                          color: 'var(--text-secondary)', cursor: 'pointer' }}>
                        ▶ Replay
                      </button>
                      <a href={`/results/${run.run_id}/download`}
                        style={{ padding: '4px 10px', borderRadius: 'var(--radius-sm)', fontSize: 11,
                          background: 'var(--bg-active)', border: '1px solid var(--border)', color: 'var(--text-secondary)',
                          textDecoration: 'none', display: 'inline-flex', alignItems: 'center' }}>
                        ↓ CSV
                      </a>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {selectedComparisonRuns.length >= 2 && (
        <div style={{
          position: 'fixed', bottom: 24, left: '50%', transform: 'translateX(-50%)',
          background: 'var(--bg-elevated)', border: '1px solid var(--accent-border)',
          borderRadius: 'var(--radius-xl)', padding: '12px 24px',
          display: 'flex', alignItems: 'center', gap: 14,
          boxShadow: '0 8px 32px rgba(79,142,247,0.2)', zIndex: 200,
          animation: 'slide-in-up 200ms ease-out',
        }}>
          <span style={{ fontSize: 13, color: 'var(--text-primary)' }}>
            {selectedComparisonRuns.length} runs selected
          </span>
          <button onClick={() => navigate('/compare')}
            style={{ padding: '8px 20px', borderRadius: 'var(--radius-md)', background: 'var(--accent)',
              color: 'white', fontWeight: 600, fontSize: 13, border: 'none', cursor: 'pointer' }}>
            Compare →
          </button>
        </div>
      )}
    </div>
  );
}
