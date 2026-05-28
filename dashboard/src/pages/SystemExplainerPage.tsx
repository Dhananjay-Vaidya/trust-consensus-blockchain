import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

const COMPONENTS = [
  {
    id: 'abac',
    name: 'ABAC',
    full: 'Attribute-Based Access Control',
    color: 'var(--cyan)',
    summary: 'ABAC enforces fine-grained access policies based on node attributes (role, clearance, location) and real-time trust scores. Only nodes meeting all policy criteria can submit transactions to the blockchain.',
    equation: 'Decision = ∧{ policy_i(attrs, trust) | policy_i ∈ PolicySet }',
    params: [
      { name: 'trust_threshold', default: '0.6', range: '0–1', effect: 'Minimum trust for write access' },
      { name: 'policy_count',    default: '3',   range: '1–10', effect: 'Number of ABAC policies enforced' },
    ],
  },
  {
    id: 'trust',
    name: 'TrustManager',
    full: 'Bayesian Beta Trust Model',
    color: 'var(--green)',
    summary: 'Each node maintains a Beta(α, β) distribution over trust. Successful interactions increase α; Byzantine detections increase β. The expected trust E[X] = α/(α+β) determines delegation eligibility.',
    equation: 'Trust(t+1) = α/(α+β)    where α += success, β += failure',
    params: [
      { name: 'decay_rate',  default: '0.003', range: '0–0.01', effect: 'Per-step trust decay for inactivity' },
      { name: 'initial_α',  default: '1.0',   range: '0.1–5', effect: 'Prior trust (higher = more trusting start)' },
      { name: 'initial_β',  default: '1.0',   range: '0.1–5', effect: 'Prior distrust' },
    ],
  },
  {
    id: 'tdcb',
    name: 'TDCB',
    full: 'Trust-Based Delegated Consensus for Blockchain',
    color: 'var(--accent)',
    summary: 'TDCB selects the top-K highest-trust nodes as delegates each round. Delegates vote on transaction batches; Byzantine nodes (identified by majority disagreement) have their trust reduced and are excluded from future rounds.',
    equation: 'Delegates = argmax_K { Trust(n) | n ∈ Nodes }',
    params: [
      { name: 'delegation_ratio', default: '0.5',  range: '0.1–1.0', effect: 'Fraction of nodes acting as delegates' },
      { name: 'consensus_threshold', default: '0.6', range: '0.3–0.9', effect: 'Minimum vote fraction for block approval' },
    ],
  },
  {
    id: 'fhe',
    name: 'FHE',
    full: 'Fully Homomorphic Encryption',
    color: 'var(--purple)',
    summary: 'FHE allows ABAC policy evaluation and trust computation on encrypted data. The CKKS scheme (via TenSEAL) enables approximate arithmetic on ciphertext, adding a privacy layer at the cost of 2–5ms overhead per operation.',
    equation: 'Eval(f, Enc(x)) = Enc(f(x))    — compute without decrypting',
    params: [
      { name: 'poly_modulus_degree', default: '8192', range: '4096–32768', effect: 'Security level vs. performance' },
      { name: 'scale',               default: '2^40', range: '2^30–2^50', effect: 'Precision of encrypted arithmetic' },
    ],
  },
  {
    id: 'rl',
    name: 'RL/DRL/MARL',
    full: 'Reinforcement Learning Agents',
    color: 'var(--amber)',
    summary: 'Three agents learn to tune simulation parameters dynamically. RL uses Q-tables; DRL uses a Double DQN with prioritised replay; MARL uses per-node actors sharing a global critic. All agents control delegation ratio, trust decay, and consensus threshold jointly.',
    equation: 'Q(s,a) ← Q(s,a) + α[r + γ max_a\' Q(s\',a\') − Q(s,a)]',
    params: [
      { name: 'action_space',  default: '27', range: '3–27', effect: '3D action: dr×td×ct combinations' },
      { name: 'state_dim',     default: '16', range: '—',    effect: 'Trust stats + chain metrics + collusion' },
      { name: 'learning_rate', default: '5e-4', range: '1e-5–1e-3', effect: 'Weight update magnitude' },
    ],
  },
  {
    id: 'blockchain',
    name: 'Blockchain',
    full: 'Proof-of-Work Blockchain (simplified)',
    color: 'var(--pink)',
    summary: 'Verified transactions are batched into blocks and appended to the chain every N steps. The blockchain provides an immutable audit trail. Byzantine-detected nodes cannot write to the chain until trust recovers above the ABAC threshold.',
    equation: 'Block_n = Hash(Block_{n-1} ∥ Transactions ∥ Nonce)',
    params: [
      { name: 'difficulty', default: '4', range: '1–6', effect: 'Leading zeros required in block hash' },
      { name: 'mine_every', default: '5', range: '1–20', effect: 'Steps between mining attempts' },
    ],
  },
];

function BetaExplorer() {
  const [alpha, setAlpha] = useState(2);
  const [beta, setBeta]   = useState(2);

  const points = useMemo(() => {
    const N = 80;
    const lgamma = (x: number): number => {
      const c = [0.99999999999980993,676.5203681218851,-1259.1392167224028,771.32342877765313,-176.61502916214059,12.507343278686905,-0.13857109526572012,9.9843695780195716e-6,1.5056327351493116e-7];
      const g = 7;
      if (x < 0.5) return Math.log(Math.PI / Math.sin(Math.PI * x)) - lgamma(1 - x);
      let xx = x - 1, a = c[0];
      for (let i = 1; i < g + 2; i++) a += c[i] / (xx + i);
      const t = xx + g + 0.5;
      return 0.5 * Math.log(2 * Math.PI) + (xx + 0.5) * Math.log(t) - t + Math.log(a);
    };
    const betaPdf = (x: number) => {
      if (x <= 0 || x >= 1) return 0;
      const logB = lgamma(alpha) + lgamma(beta) - lgamma(alpha + beta);
      return Math.exp((alpha - 1) * Math.log(x) + (beta - 1) * Math.log(1 - x) - logB);
    };
    const vals = Array.from({ length: N }, (_, i) => betaPdf((i + 0.5) / N));
    const maxY = Math.max(...vals, 0.01);
    return vals.map((y, i) => ({ x: (i + 0.5) / N, y: y / maxY }));
  }, [alpha, beta]);

  const W = 320; const H = 100;
  const polyline = points.map((p) => `${p.x * W},${H - p.y * H * 0.92}`).join(' ');
  const fill = points.map((p) => `${p.x * W},${H - p.y * H * 0.92}`).concat([`${W},${H}`, `0,${H}`]).join(' ');

  return (
    <div style={{ background: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)', padding: 14 }}>
      <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 10, fontWeight: 600 }}>
        Beta Distribution Explorer — E[X] = {(alpha / (alpha + beta)).toFixed(3)}
      </div>
      <svg width={W} height={H} style={{ display: 'block', marginBottom: 12 }}>
        <polygon points={fill} fill="var(--green)" fillOpacity={0.15} />
        <polyline points={polyline} fill="none" stroke="var(--green)" strokeWidth={1.5} />
        <line x1={(alpha / (alpha + beta)) * W} y1={0} x2={(alpha / (alpha + beta)) * W} y2={H}
          stroke="var(--accent)" strokeWidth={1} strokeDasharray="3 2" />
        <text x={2} y={12} fontSize={9} fill="var(--text-muted)">α={alpha} β={beta}</text>
      </svg>
      {[['Alpha (α) — honest votes', alpha, setAlpha], ['Beta (β) — malicious votes', beta, setBeta]].map(([label, val, setter]) => (
        <div key={label as string} style={{ marginBottom: 8 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-secondary)', marginBottom: 4 }}>
            <span>{label as string}</span><span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{val as number}</span>
          </div>
          <input type="range" min={1} max={20} value={val as number}
            onChange={(e) => (setter as (v: number) => void)(Number(e.target.value))}
            style={{ width: '100%', accentColor: 'var(--green)' }} />
        </div>
      ))}
    </div>
  );
}

export function SystemExplainerPage() {
  const navigate = useNavigate();
  const [open, setOpen] = useState<string | null>('tdcb');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, maxWidth: 900 }}>
      <div>
        <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>System Explainer</div>
        <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
          Interactive deep-dives into each system component. Designed for reviewers and conference presentations.
        </div>
      </div>

      {/* Architecture Diagram */}
      <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: 20 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 14 }}>
          System Architecture
        </div>
        <svg width="100%" height={160} viewBox="0 0 800 160">
          {/* IoT Nodes */}
          <rect x={10} y={60} width={90} height={40} rx={6} fill="var(--bg-elevated)" stroke="var(--border)" />
          <text x={55} y={82} textAnchor="middle" fontSize={10} fill="var(--text-secondary)">IoT Nodes</text>
          {/* ABAC */}
          <rect x={130} y={60} width={90} height={40} rx={6} fill="var(--cyan-dim)" stroke="var(--cyan)" />
          <text x={175} y={82} textAnchor="middle" fontSize={10} fill="var(--cyan)">ABAC</text>
          {/* FHE shield */}
          <text x={175} y={94} textAnchor="middle" fontSize={8} fill="var(--purple)">🔒 FHE</text>
          {/* TrustManager */}
          <rect x={250} y={60} width={100} height={40} rx={6} fill="var(--green-dim)" stroke="var(--green)" />
          <text x={300} y={82} textAnchor="middle" fontSize={10} fill="var(--green)">TrustManager</text>
          {/* TDCB */}
          <rect x={380} y={60} width={90} height={40} rx={6} fill="var(--accent-dim)" stroke="var(--accent)" />
          <text x={425} y={82} textAnchor="middle" fontSize={10} fill="var(--accent)">TDCB</text>
          {/* Blockchain */}
          <rect x={500} y={60} width={90} height={40} rx={6} fill="var(--bg-elevated)" stroke="var(--border-strong)" />
          <text x={545} y={82} textAnchor="middle" fontSize={10} fill="var(--text-primary)">Blockchain</text>
          {/* RL Agent */}
          <rect x={620} y={10} width={160} height={40} rx={6} fill="var(--amber-dim)" stroke="var(--amber)" />
          <text x={700} y={32} textAnchor="middle" fontSize={10} fill="var(--amber)">RL / DRL / MARL Agent</text>

          {/* Arrows */}
          {[[100, 80, 130, 80], [220, 80, 250, 80], [350, 80, 380, 80], [470, 80, 500, 80]].map(([x1,y1,x2,y2], i) => (
            <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="var(--border-strong)" strokeWidth={1.5} markerEnd="url(#a)" />
          ))}
          {/* Agent feedback loop */}
          <path d="M700,50 L700,100 L425,100 L425,100" fill="none" stroke="var(--amber)" strokeWidth={1} strokeDasharray="5 3" />
          <defs><marker id="a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="var(--border-strong)" /></marker></defs>
          {/* Attack injection */}
          <text x={300} y={145} textAnchor="middle" fontSize={9} fill="var(--red)">⚡ Attack injection → TrustManager</text>
        </svg>
      </div>

      {/* Component accordions */}
      {COMPONENTS.map((comp) => {
        const isOpen = open === comp.id;
        return (
          <div key={comp.id} style={{ background: 'var(--bg-panel)', border: `1px solid ${isOpen ? comp.color : 'var(--border)'}`, borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
            <button onClick={() => setOpen(isOpen ? null : comp.id)}
              style={{ width: '100%', background: 'none', border: 'none', cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: 12, padding: '14px 18px' }}>
              <span style={{ width: 10, height: 10, borderRadius: '50%', background: comp.color, flexShrink: 0 }} />
              <span style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-primary)' }}>{comp.name}</span>
              <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{comp.full}</span>
              <span style={{ marginLeft: 'auto', color: 'var(--text-muted)', fontSize: 12 }}>{isOpen ? '▲' : '▼'}</span>
            </button>

            {isOpen && (
              <div style={{ borderTop: '1px solid var(--border)', padding: '14px 18px', display: 'flex', flexDirection: 'column', gap: 12 }}>
                <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.65, margin: 0 }}>{comp.summary}</p>

                {/* Equation */}
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: comp.color, background: 'var(--bg-elevated)',
                  borderLeft: `3px solid ${comp.color}`, padding: '8px 12px', borderRadius: '0 var(--radius-sm) var(--radius-sm) 0' }}>
                  {comp.equation}
                </div>

                {/* Beta explorer for TrustManager */}
                {comp.id === 'trust' && <BetaExplorer />}

                {/* Parameter table */}
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
                  <thead>
                    <tr>
                      {['Parameter', 'Default', 'Range', 'Effect'].map((h) => (
                        <th key={h} style={{ padding: '6px 10px', textAlign: 'left', color: 'var(--text-secondary)',
                          borderBottom: '1px solid var(--border)', fontWeight: 600 }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {comp.params.map((p) => (
                      <tr key={p.name}>
                        <td style={{ padding: '6px 10px', fontFamily: 'var(--font-mono)', color: comp.color }}>{p.name}</td>
                        <td style={{ padding: '6px 10px', color: 'var(--text-primary)' }}>{p.default}</td>
                        <td style={{ padding: '6px 10px', color: 'var(--text-muted)' }}>{p.range}</td>
                        <td style={{ padding: '6px 10px', color: 'var(--text-secondary)' }}>{p.effect}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                <button onClick={() => navigate('/')}
                  style={{ alignSelf: 'flex-start', padding: '7px 16px', borderRadius: 'var(--radius-sm)',
                    background: `${comp.color}18`, border: `1px solid ${comp.color}40`,
                    color: comp.color, fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>
                  ▶ See it live →
                </button>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
