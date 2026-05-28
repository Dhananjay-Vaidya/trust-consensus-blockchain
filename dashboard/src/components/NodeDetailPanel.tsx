import { useMemo } from 'react';

import { useSimulationStore } from '../store/simulationStore';
import { Badge, badgeVariant } from './ui/Badge';
import { Divider } from './ui/Divider';

function betaPdf(x: number, a: number, b: number): number {
  if (x <= 0 || x >= 1) return 0;
  // Approximate Beta PDF using log-gamma
  const logB = lgamma(a) + lgamma(b) - lgamma(a + b);
  return Math.exp((a - 1) * Math.log(x) + (b - 1) * Math.log(1 - x) - logB);
}

function lgamma(x: number): number {
  // Lanczos approximation
  const g = 7;
  const c = [0.99999999999980993,676.5203681218851,-1259.1392167224028,771.32342877765313,-176.61502916214059,12.507343278686905,-0.13857109526572012,9.9843695780195716e-6,1.5056327351493116e-7];
  if (x < 0.5) return Math.log(Math.PI / Math.sin(Math.PI * x)) - lgamma(1 - x);
  x -= 1;
  let a = c[0];
  for (let i = 1; i < g + 2; i++) a += c[i] / (x + i);
  const t = x + g + 0.5;
  return 0.5 * Math.log(2 * Math.PI) + (x + 0.5) * Math.log(t) - t + Math.log(a);
}

function BetaPlot({ alpha, beta, trust }: { alpha: number; beta: number; trust: number }) {
  const N = 60;
  const pts = useMemo(() => {
    const maxY = betaPdf(alpha > 1 ? (alpha - 1) / (alpha + beta - 2) : 0.01, alpha, beta) || 1;
    return Array.from({ length: N }, (_, i) => {
      const x = (i + 0.5) / N;
      const y = betaPdf(x, alpha, beta) / maxY;
      return { px: (x * 250).toFixed(1), py: (80 - y * 75).toFixed(1) };
    });
  }, [alpha, beta]);

  const polyline = pts.map((p) => `${p.px},${p.py}`).join(' ');
  const fill = pts.map((p) => `${p.px},${p.py}`).concat(['250,80', '0,80']).join(' ');
  const trustX = trust * 250;

  return (
    <svg width={250} height={80} style={{ display: 'block', margin: '8px 0' }}>
      <polygon points={fill} fill="var(--accent)" fillOpacity={0.15} />
      <polyline points={polyline} fill="none" stroke="var(--accent)" strokeWidth={1.5} />
      <line x1={trustX} y1={0} x2={trustX} y2={80} stroke="var(--green)" strokeWidth={1} strokeDasharray="3 2" />
      <text x={trustX + 3} y={12} fontSize={8} fill="var(--green)">{trust.toFixed(2)}</text>
      <text x={2} y={78} fontSize={8} fill="var(--text-muted)">0</text>
      <text x={230} y={78} fontSize={8} fill="var(--text-muted)">1</text>
      <text x={4} y={10} fontSize={9} fill="var(--text-secondary)">α={alpha.toFixed(1)} β={beta.toFixed(1)}</text>
    </svg>
  );
}

export function NodeDetailPanel() {
  const selectedNodeId = useSimulationStore((s) => s.selectedNodeId);
  const trustScores    = useSimulationStore((s) => s.trustScores);
  const isMalicious    = useSimulationStore((s) => s.isMalicious);
  const isDetected     = useSimulationStore((s) => s.isDetected);
  const delegateNodes  = useSimulationStore((s) => s.delegateNodes);
  const selectNode     = useSimulationStore((s) => s.selectNode);

  if (!selectedNodeId) return null;

  const trust   = trustScores[selectedNodeId] ?? 0.5;
  const mal     = isMalicious[selectedNodeId] ?? false;
  const det     = isDetected[selectedNodeId] ?? false;
  const isDelegate = delegateNodes.includes(selectedNodeId);

  // Derive α,β from trust: trust = α/(α+β), confidence = α+β
  const conf  = 10;
  const alpha = trust * conf;
  const beta  = (1 - trust) * conf;

  return (
    <div style={{
      position: 'absolute', right: 0, top: 0, bottom: 0, width: 300,
      background: 'var(--bg-elevated)', borderLeft: '1px solid var(--border)',
      overflowY: 'auto', zIndex: 20, padding: 14,
      animation: 'slide-in-right 250ms ease-out',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
        <div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
            {selectedNodeId}
          </div>
          <div style={{ display: 'flex', gap: 5, marginTop: 5, flexWrap: 'wrap' }}>
            <Badge label={mal ? 'Malicious' : 'Honest'} variant={mal ? 'red' : 'green'} />
            {isDelegate && <Badge label="Delegate" variant="blue" />}
            {det && <Badge label="Detected" variant="amber" />}
          </div>
        </div>
        <button onClick={() => selectNode(null)}
          style={{ background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--text-secondary)', fontSize: 16, padding: 2 }}>✕</button>
      </div>

      <Divider />

      {/* Trust Score */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 10, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4 }}>
          Trust Profile
        </div>
        <div style={{
          fontSize: 32, fontWeight: 700, lineHeight: 1.1,
          color: trust > 0.7 ? 'var(--green)' : trust > 0.4 ? 'var(--amber)' : 'var(--red)',
        }}>
          {trust.toFixed(3)}
        </div>
        <BetaPlot alpha={alpha} beta={beta} trust={trust} />
      </div>

      <Divider />

      {/* ABAC */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 10, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>
          ABAC Role
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
          <Badge label={mal ? 'user_role' : 'admin_role'} variant={badgeVariant('none')} />
          {!mal && <Badge label="security_clearance" variant="blue" />}
          <Badge label={trust > 0.6 ? 'write: ✓' : 'write: ✗'} variant={trust > 0.6 ? 'green' : 'red'} />
        </div>
      </div>

      <Divider />

      {/* Stats */}
      <div>
        <div style={{ fontSize: 10, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>
          Network Stats
        </div>
        <table style={{ width: '100%', fontSize: 11, borderCollapse: 'collapse' }}>
          <tbody>
            {[
              ['Delegate status', isDelegate ? '✓ Active' : '—'],
              ['Detection state', det ? '⚠ Flagged' : 'Clean'],
              ['Ground truth', mal ? 'Malicious' : 'Honest'],
            ].map(([k, v]) => (
              <tr key={k}>
                <td style={{ padding: '4px 0', color: 'var(--text-secondary)' }}>{k}</td>
                <td style={{ padding: '4px 0', textAlign: 'right', color: 'var(--text-primary)' }}>{v}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
