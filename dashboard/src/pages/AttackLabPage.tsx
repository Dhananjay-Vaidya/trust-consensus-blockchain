import { useState } from 'react';
import {
  Legend, PolarAngleAxis, PolarGrid, Radar, RadarChart, ResponsiveContainer, Tooltip,
} from 'recharts';
import toast from 'react-hot-toast';

import { useSimulationStore } from '../store/simulationStore';
import { Badge, badgeVariant } from '../components/ui/Badge';
import { apiClient } from '../api/client';

const ATTACKS = ['nma', 'cra', 'aaa', 'bfi', 'tdp'] as const;
type Attack = typeof ATTACKS[number];

const ATTACK_INFO: Record<Attack, { full: string; category: string; desc: string; realWorld: string; f1Impact: string }> = {
  nma: { full: 'Negligible Malicious Activity', category: 'Low-level', desc: 'Nodes submit slightly incorrect votes at low frequency, attempting to stay below detection thresholds while gradually eroding consensus accuracy.', realWorld: 'Mimics insider threats in industrial IoT', f1Impact: 'F1 typically drops to 0.85–0.90' },
  cra: { full: 'Coordinated Reputation Attack', category: 'Collusion', desc: 'A cluster of malicious nodes mutually inflate each other\'s trust scores while collectively downvoting honest delegates, undermining trust-weighted consensus.', realWorld: 'Maps to Sybil-based collusion in P2P networks', f1Impact: 'F1 typically drops to 0.70–0.80' },
  aaa: { full: 'Adaptive Adversarial Attack', category: 'Adaptive', desc: 'The adversary dynamically switches between five sub-strategies based on detection pressure, making it the hardest attack to defend against.', realWorld: 'Advanced persistent threats (APT) in SCADA', f1Impact: 'F1 typically drops to 0.65–0.75' },
  bfi: { full: 'Byzantine Fault Injection', category: 'Byzantine', desc: 'Malicious nodes inject forked block proposals and conflicting votes, exploiting the consensus voting phase to accept invalid transactions.', realWorld: 'Maps to 51% attack variant in IoT chains', f1Impact: 'F1 typically drops to 0.60–0.75' },
  tdp: { full: 'Time-Delayed Poisoning', category: 'Sleeper', desc: 'Nodes behave honestly for the first N episodes (building high trust), then simultaneously activate to exploit their accumulated reputation.', realWorld: 'Ukraine Power Grid attack pattern (2015)', f1Impact: 'F1 drops sharply after episode 25 to 0.60–0.75' },
};

function AttackDiagram({ attack }: { attack: Attack }) {
  const W = 320; const H = 120;
  if (attack === 'tdp') {
    return (
      <svg width={W} height={H} style={{ display: 'block' }}>
        <rect x={10} y={40} width={120} height={40} rx={6} fill="var(--green-dim)" stroke="var(--green)" strokeWidth={1} />
        <text x={70} y={63} textAnchor="middle" fill="var(--green)" fontSize={11} fontFamily="var(--font-mono)">DORMANT (ep 0–24)</text>
        <line x1={130} y1={60} x2={180} y2={60} stroke="var(--amber)" strokeWidth={2} markerEnd="url(#arr)" />
        <text x={155} y={52} textAnchor="middle" fill="var(--amber)" fontSize={9}>ACTIVATE</text>
        <rect x={182} y={40} width={120} height={40} rx={6} fill="var(--red-dim)" stroke="var(--red)" strokeWidth={1} />
        <text x={242} y={63} textAnchor="middle" fill="var(--red)" fontSize={11} fontFamily="var(--font-mono)">ATTACK (ep 25+)</text>
        <defs><marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="var(--amber)" /></marker></defs>
      </svg>
    );
  }
  if (attack === 'cra') {
    return (
      <svg width={W} height={H}>
        {[0,1,2].map((i) => {
          const cx = 80 + i * 30; const cy = 60;
          return <g key={i}>
            <circle cx={cx} cy={cy} r={14} fill="var(--red-dim)" stroke="var(--red)" strokeWidth={1.5} />
            <text x={cx} y={cy+4} textAnchor="middle" fontSize={9} fill="var(--red)" fontFamily="var(--font-mono)">M{i}</text>
            {i < 2 && <path d={`M${cx+14},${cy} Q${cx+20},${cy-20} ${cx+16},${cy}`} fill="none" stroke="var(--amber)" strokeWidth={1} strokeDasharray="3 2" />}
          </g>;
        })}
        <circle cx={230} cy={40} r={12} fill="var(--green-dim)" stroke="var(--green)" strokeWidth={1} />
        <text x={230} y={44} textAnchor="middle" fontSize={9} fill="var(--green)" fontFamily="var(--font-mono)">H1</text>
        <line x1={134} y1={55} x2={218} y2={45} stroke="var(--red)" strokeWidth={1} strokeDasharray="4 2" />
        <text x={175} y={42} textAnchor="middle" fontSize={8} fill="var(--red)">downvote</text>
        <text x={100} y={100} textAnchor="middle" fontSize={9} fill="var(--text-secondary)">Malicious cluster mutually boosts trust</text>
      </svg>
    );
  }
  // Generic diagram for other attacks
  return (
    <svg width={W} height={H}>
      {[0,1,2,3].map((i) => {
        const cx = 60 + i * 65; const cy = 55;
        const isMal = i === 1 || i === 3;
        return (
          <g key={i}>
            <circle cx={cx} cy={cy} r={18} fill={isMal ? 'var(--red-dim)' : 'var(--green-dim)'}
              stroke={isMal ? 'var(--red)' : 'var(--green)'} strokeWidth={1.5} />
            <text x={cx} y={cy+4} textAnchor="middle" fontSize={9} fill={isMal ? 'var(--red)' : 'var(--green)'}>
              {isMal ? 'MAL' : 'HON'}
            </text>
          </g>
        );
      })}
      <text x={W/2} y={H-8} textAnchor="middle" fontSize={9} fill="var(--text-secondary)">
        {ATTACK_INFO[attack].category} attack pattern
      </text>
    </svg>
  );
}

const RADAR_DATA = [
  { axis: 'F1 Drop',          nma: 0.15, cra: 0.25, aaa: 0.35, bfi: 0.30, tdp: 0.28 },
  { axis: 'Stealth',          nma: 0.80, cra: 0.55, aaa: 0.70, bfi: 0.45, tdp: 0.85 },
  { axis: 'Trust Disruption', nma: 0.20, cra: 0.75, aaa: 0.60, bfi: 0.50, tdp: 0.65 },
  { axis: 'Recovery Time',    nma: 0.10, cra: 0.60, aaa: 0.55, bfi: 0.40, tdp: 0.70 },
  { axis: 'Adaptability',     nma: 0.20, cra: 0.40, aaa: 0.95, bfi: 0.30, tdp: 0.50 },
];

const COLOURS: Record<Attack, string> = { nma: 'var(--amber)', cra: 'var(--red)', aaa: 'var(--purple)', bfi: 'var(--pink)', tdp: 'var(--cyan)' };

export function AttackLabPage() {
  const [activeTab, setActiveTab] = useState<Attack>('cra');
  const runId  = useSimulationStore((s) => s.runId);
  const status = useSimulationStore((s) => s.status);
  const isRunning = status === 'running';

  const injectAttack = async () => {
    if (!runId) return;
    try {
      await apiClient.post(`/simulation/${runId}/inject_attack`, { attack: activeTab, intensity: 1 });
      toast(`⚡ ${activeTab.toUpperCase()} injected`, { icon: '⚡', style: { background: 'var(--amber-dim)', color: 'var(--amber)' } });
    } catch {
      toast.error('Injection failed — is a simulation running?');
    }
  };

  const info = ATTACK_INFO[activeTab];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Attack Tabs */}
      <div style={{ display: 'flex', gap: 6 }}>
        {ATTACKS.map((a) => (
          <button key={a} onClick={() => setActiveTab(a)}
            style={{
              padding: '8px 16px', borderRadius: 'var(--radius-md)', cursor: 'pointer',
              fontWeight: 600, fontSize: 12, textTransform: 'uppercase',
              border: `1px solid ${activeTab === a ? COLOURS[a] : 'var(--border)'}`,
              background: activeTab === a ? `${COLOURS[a]}18` : 'var(--bg-panel)',
              color: activeTab === a ? COLOURS[a] : 'var(--text-secondary)',
            }}>
            {a.toUpperCase()}
          </button>
        ))}
      </div>

      {/* Attack Anatomy */}
      <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: 18 }}>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 10 }}>
          <span style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>{info.full}</span>
          <Badge label={info.category} variant={badgeVariant(activeTab)} />
        </div>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: 14 }}>{info.desc}</p>
        <AttackDiagram attack={activeTab} />
        <div style={{ display: 'flex', gap: 10, marginTop: 10, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 11, color: 'var(--amber)', background: 'var(--amber-dim)', padding: '3px 10px', borderRadius: 999 }}>
            🌍 {info.realWorld}
          </span>
          <span style={{ fontSize: 11, color: 'var(--text-secondary)', background: 'var(--bg-elevated)', padding: '3px 10px', borderRadius: 999 }}>
            📊 {info.f1Impact}
          </span>
        </div>
      </div>

      {/* Live Inject */}
      <div style={{ background: 'var(--bg-panel)', border: `1px solid ${isRunning ? 'var(--red)' : 'var(--border)'}`, borderRadius: 'var(--radius-lg)', padding: 18 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 10 }}>
          Live Injection {!isRunning && <span style={{ color: 'var(--text-muted)' }}> — start a simulation first</span>}
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <button onClick={() => void injectAttack()} disabled={!isRunning}
            style={{
              padding: '10px 20px', borderRadius: 'var(--radius-md)', fontWeight: 600, fontSize: 13, border: 'none',
              background: isRunning ? 'var(--red)' : 'var(--bg-active)',
              color: isRunning ? 'white' : 'var(--text-muted)',
              cursor: isRunning ? 'pointer' : 'not-allowed',
            }}>
            ⚡ Inject {activeTab.toUpperCase()} Now
          </button>
          {runId && <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>run: {runId.slice(0, 8)}</span>}
        </div>
      </div>

      {/* Radar */}
      <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: 18 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 10 }}>
          Attack Profile Comparison
        </div>
        <ResponsiveContainer width="100%" height={320}>
          <RadarChart data={RADAR_DATA}>
            <PolarGrid stroke="var(--border)" />
            <PolarAngleAxis dataKey="axis" tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} />
            <Tooltip contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-strong)', borderRadius: 8 }} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            {ATTACKS.map((a) => (
              <Radar key={a} name={a.toUpperCase()} dataKey={a}
                stroke={COLOURS[a]} fill={COLOURS[a]} fillOpacity={0.12} />
            ))}
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Defence Matrix */}
      <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: 18 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 10 }}>
          Defence Effectiveness Matrix (Simulated)
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
          <thead>
            <tr>
              <th style={{ padding: '8px 12px', textAlign: 'left', color: 'var(--text-secondary)', borderBottom: '1px solid var(--border)' }}>Attack</th>
              {(['rl', 'drl', 'marl'] as const).map((a) => (
                <th key={a} style={{ padding: '8px 12px', textAlign: 'center', color: 'var(--text-secondary)', borderBottom: '1px solid var(--border)' }}>
                  <Badge label={a.toUpperCase()} variant={badgeVariant(a)} />
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {([
              ['nma', 0.94, 0.95, 0.97],
              ['cra', 0.78, 0.82, 0.91],
              ['aaa', 0.71, 0.76, 0.88],
              ['bfi', 0.74, 0.79, 0.89],
              ['tdp', 0.72, 0.77, 0.87],
            ] as [Attack, number, number, number][]).map(([atk, rl, drl, marl]) => (
              <tr key={atk}>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid var(--border)' }}>
                  <Badge label={atk.toUpperCase()} variant={badgeVariant(atk)} />
                </td>
                {[rl, drl, marl].map((v, i) => (
                  <td key={i} style={{
                    padding: '8px 12px', textAlign: 'center', borderBottom: '1px solid var(--border)',
                    background: v > 0.90 ? 'var(--green-dim)' : v > 0.80 ? 'var(--amber-dim)' : 'var(--red-dim)',
                    color: v > 0.90 ? 'var(--green)' : v > 0.80 ? 'var(--amber)' : 'var(--red)',
                    fontWeight: 600,
                  }}>
                    {v.toFixed(2)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
