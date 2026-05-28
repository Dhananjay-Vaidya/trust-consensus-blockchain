import { useEffect, useRef, useState } from 'react';

import { useSimulationStore } from '../store/simulationStore';
import type { StepEvent } from '../types';

interface LogLine {
  id: number;
  text: string;
  color: string;
  time: string;
}

let lineId = 0;

function formatEvent(e: StepEvent): LogLine | null {
  const t = new Date(e.timestamp * 1000).toLocaleTimeString('en-US', { hour12: false });
  const base = { id: ++lineId, time: t };

  if (e.type === 'episode_end') {
    return { ...base, color: 'var(--accent)',
      text: `— Episode ${e.episode + 1} complete: F1=${e.f1_score.toFixed(3)}  Reward=${e.reward.toFixed(2)}  Blocks=${e.blockchain_length}` };
  }
  if (e.type === 'simulation_end') {
    return { ...base, color: 'var(--green)',
      text: `✓ Simulation complete — Final F1: ${e.f1_score.toFixed(4)}` };
  }
  if (e.type === 'error') {
    return { ...base, color: 'var(--red)',
      text: `✗ ${e.action_description}` };
  }
  if (e.type === 'step') {
    if (e.byzantine_detections > 0) {
      const detected = Object.entries(e.is_detected)
        .filter(([, v]) => v).map(([k]) => k).join(', ');
      return { ...base, color: 'var(--red)',
        text: `⚠ Byzantine detected: ${detected || '?'} (ep ${e.episode})` };
    }
    if (e.step % 5 !== 0) return null;
    return { ...base, color: 'var(--text-muted)',
      text: `  ep${e.episode} s${e.step}  F1=${e.f1_score.toFixed(3)}  tx=${e.transactions_verified}  del=[${e.delegate_nodes.length}]` };
  }
  return null;
}

export function EventFeed() {
  const [lines, setLines] = useState<LogLine[]>([]);
  const [expanded, setExpanded] = useState(true);
  const [paused, setPaused] = useState(false);
  const latestStep = useSimulationStore((s) => s.latestStep);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!latestStep || paused) return;
    const line = formatEvent(latestStep);
    if (!line) return;
    setLines((prev) => {
      const next = [...prev, line];
      return next.length > 500 ? next.slice(-500) : next;
    });
  }, [latestStep, paused]);

  useEffect(() => {
    if (!paused && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [lines, paused]);

  return (
    <div style={{
      borderTop: '1px solid var(--border)',
      background: 'var(--bg-surface)',
      display: 'flex', flexDirection: 'column',
      height: expanded ? 140 : 28, transition: 'height 200ms ease', flexShrink: 0,
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '0 12px', height: 28, borderBottom: expanded ? '1px solid var(--border)' : 'none',
        flexShrink: 0,
      }}>
        <button onClick={() => setExpanded((v) => !v)}
          style={{ background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--text-secondary)', fontSize: 11 }}>
          {expanded ? '▼' : '▲'} Event Feed
        </button>
        <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
          {lines.length} events
        </span>
        {expanded && (
          <>
            <button onClick={() => setPaused((v) => !v)}
              style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer',
                fontSize: 10, color: paused ? 'var(--amber)' : 'var(--text-muted)' }}>
              {paused ? '▶ Resume' : '⏸ Pause'}
            </button>
            <button onClick={() => setLines([])}
              style={{ background: 'none', border: 'none', cursor: 'pointer',
                fontSize: 10, color: 'var(--text-muted)' }}>
              Clear
            </button>
          </>
        )}
      </div>

      {/* Log lines */}
      {expanded && (
        <div ref={scrollRef} style={{ flex: 1, overflowY: 'auto', overflowX: 'hidden' }}>
          {lines.map((line) => (
            <div key={line.id} style={{
              paddingLeft: 12, paddingRight: 12, height: 18,
              fontFamily: 'var(--font-mono)', fontSize: 10, color: line.color,
              display: 'flex', alignItems: 'center', gap: 8,
              whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
              flexShrink: 0,
            }}>
              <span style={{ color: 'var(--text-muted)', flexShrink: 0 }}>{line.time}</span>
              {line.text}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
