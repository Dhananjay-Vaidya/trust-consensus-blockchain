import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useSimulationStore } from '../store/simulationStore';
import { Badge, badgeVariant } from '../components/ui/Badge';
import type { SimulationConfig } from '../types';

interface Scenario {
  id: string;
  name: string;
  icon: string;
  desc: string;
  attack: SimulationConfig['attack'];
  nodes: number;
  episodes: number;
  malicious: number;
  incident: string;
  compliance: string[];
  threatModel: string;
  expected: string;
}

const SCENARIOS: Scenario[] = [
  {
    id: 'smart-grid',
    name: 'Smart Grid',
    icon: '⚡',
    desc: 'Electricity distribution network with IoT sensor nodes and SCADA controllers.',
    attack: 'cra',
    nodes: 32,
    episodes: 100,
    malicious: 0.20,
    incident: 'Ukraine Power Grid Attack (2015/2016)',
    compliance: ['NERC CIP-013', 'IEC 62443'],
    threatModel: 'Coordinated reputation attacks on metering nodes allow adversaries to corrupt energy pricing data and destabilise grid balance. Trust-aware consensus prevents false readings from entering the blockchain ledger.',
    expected: 'Your system: F1 ≈ 0.92  |  PBFT baseline: Fails at 33% Byzantine',
  },
  {
    id: 'hospital',
    name: 'Hospital IoT',
    icon: '🏥',
    desc: 'Medical device network for patient monitoring, drug dispensing, and records.',
    attack: 'tdp',
    nodes: 24,
    episodes: 100,
    malicious: 0.15,
    incident: 'WannaCry NHS Attack (2017)',
    compliance: ['HIPAA', 'IEC 80001-1'],
    threatModel: 'Sleeper agents build trust over time then activate to corrupt patient records or dosage logs. Time-delayed poisoning is particularly dangerous in healthcare where trust is slow to build.',
    expected: 'Your system: F1 ≈ 0.88  |  Without TDCB: F1 drops to 0.62 post-activation',
  },
  {
    id: 'supply-chain',
    name: 'Supply Chain',
    icon: '🚚',
    desc: 'Logistics IoT network tracking goods with RFID and GPS sensor nodes.',
    attack: 'cra',
    nodes: 16,
    episodes: 80,
    malicious: 0.25,
    incident: 'NotPetya Supply Chain Disruption (2017)',
    compliance: ['ISO 28000', 'NIST SP 800-161'],
    threatModel: 'Colluding malicious nodes falsify provenance records, enabling counterfeit goods to enter the supply chain. CRA allows compromised nodes to boost each other past detection thresholds.',
    expected: 'Your system: F1 ≈ 0.91  |  PBFT baseline: Degraded at 25% malicious',
  },
  {
    id: 'av',
    name: 'Autonomous Vehicles',
    icon: '🚗',
    desc: 'V2X communication network with roadside units and vehicle nodes.',
    attack: 'bfi',
    nodes: 64,
    episodes: 120,
    malicious: 0.20,
    incident: 'Jeep Cherokee Remote Hack (2015)',
    compliance: ['SAE J3061', 'ISO/SAE 21434'],
    threatModel: 'Byzantine fault injection allows malicious vehicles to broadcast false sensor data (road conditions, emergency stops) that other vehicles act on. TDCB prevents forked block proposals from entering the safety log.',
    expected: 'Your system: F1 ≈ 0.90  |  Scalability maintained at 64 nodes',
  },
  {
    id: 'manet',
    name: 'Defence MANET',
    icon: '📡',
    desc: 'Mobile ad-hoc network for military tactical communications.',
    attack: 'aaa',
    nodes: 32,
    episodes: 100,
    malicious: 0.30,
    incident: 'Stuxnet ICS Attack (2010)',
    compliance: ['NIST SP 800-82', 'MIL-STD-461'],
    threatModel: 'Adaptive adversarial attacks dynamically switch strategies based on detection pressure — mimicking advanced persistent threats. With 30% compromised nodes, static defences fail; MARL must adapt faster than the attacker.',
    expected: 'Your system: F1 ≈ 0.85  |  Adaptive attack hardest scenario',
  },
  {
    id: 'fintech',
    name: 'Fintech ATM',
    icon: '🏦',
    desc: 'ATM network with IoT sensors for fraud detection and cash management.',
    attack: 'cra',
    nodes: 16,
    episodes: 60,
    malicious: 0.15,
    incident: 'Carbanak ATM Jackpotting (2015)',
    compliance: ['PCI DSS 4.0', 'ISO 27001'],
    threatModel: 'Coordinated attacks allow compromised ATMs to approve fraudulent transactions by boosting each other\'s trust scores in the consensus layer. ABAC ensures only properly credentialed terminals can write to the ledger.',
    expected: 'Your system: F1 ≈ 0.95  |  ABAC blocks 94% of unauthorized writes',
  },
];

export function ScenariosPage() {
  const navigate = useNavigate();
  const setConfig = useSimulationStore((s) => s.setConfig);
  const [expanded, setExpanded] = useState<string | null>(null);

  const loadAndRun = (s: Scenario) => {
    setConfig({ nodes: s.nodes, attack: s.attack, episodes: s.episodes, malicious_fraction: s.malicious });
    navigate('/');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div>
        <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>Real-World Scenarios</div>
        <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
          Six IoT deployment scenarios with pre-configured parameters, threat models, and compliance context.
        </div>
      </div>

      {/* Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14 }}>
        {SCENARIOS.map((s) => {
          const isOpen = expanded === s.id;
          return (
            <div key={s.id} style={{
              background: 'var(--bg-panel)', border: `1px solid ${isOpen ? 'var(--accent-border)' : 'var(--border)'}`,
              borderRadius: 'var(--radius-lg)', overflow: 'hidden',
              transform: isOpen ? 'translateY(-2px)' : 'none',
              transition: 'transform 150ms, border-color 150ms, box-shadow 150ms',
              boxShadow: isOpen ? '0 8px 24px rgba(79,142,247,0.1)' : 'none',
            }}>
              {/* Card header */}
              <div style={{ padding: 16 }}>
                <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start', marginBottom: 8 }}>
                  <span style={{ fontSize: 28 }}>{s.icon}</span>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-primary)' }}>{s.name}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 2 }}>{s.desc}</div>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', marginBottom: 8 }}>
                  <Badge label={`Attack: ${s.attack.toUpperCase()}`} variant={badgeVariant(s.attack)} />
                  <Badge label={`${s.nodes} nodes`} variant="muted" />
                  <Badge label={`${Math.round(s.malicious * 100)}% malicious`} variant="red" />
                </div>
                <div style={{
                  fontSize: 10, color: 'var(--red)', background: 'var(--red-dim)',
                  border: '1px solid rgba(239,68,68,0.2)', borderRadius: 4,
                  padding: '3px 8px', marginBottom: 10,
                }}>
                  ⚠ Ref: {s.incident}
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button onClick={() => loadAndRun(s)}
                    style={{ flex: 1, padding: '8px 0', borderRadius: 'var(--radius-sm)', border: 'none',
                      background: 'var(--green)', color: 'white', fontWeight: 600, fontSize: 12, cursor: 'pointer' }}>
                    ▶ Run
                  </button>
                  <button onClick={() => setExpanded(isOpen ? null : s.id)}
                    style={{ flex: 1, padding: '8px 0', borderRadius: 'var(--radius-sm)',
                      background: 'var(--bg-elevated)', border: '1px solid var(--border)',
                      color: 'var(--text-secondary)', fontSize: 12, cursor: 'pointer' }}>
                    {isOpen ? 'Close' : 'Details'}
                  </button>
                </div>
              </div>

              {/* Expanded detail */}
              {isOpen && (
                <div style={{ borderTop: '1px solid var(--border)', padding: 14, background: 'var(--bg-elevated)' }}>
                  <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.65, marginBottom: 10 }}>{s.threatModel}</p>
                  <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--green)', background: 'var(--green-dim)',
                    border: '1px solid rgba(34,197,94,0.2)', borderRadius: 6, padding: '6px 10px', marginBottom: 8 }}>
                    {s.expected}
                  </div>
                  <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                    {s.compliance.map((c) => (
                      <Badge key={c} label={c} variant="blue" />
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
