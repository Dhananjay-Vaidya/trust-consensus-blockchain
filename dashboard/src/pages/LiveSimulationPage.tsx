import { useState, useRef } from 'react';

import { EventFeed }              from '../components/EventFeed';
import { LiveMetricsPanel }       from '../components/LiveMetricsPanel';
import { NodeDetailPanel }        from '../components/NodeDetailPanel';
import { SimulationControlPanel } from '../components/SimulationControlPanel';
import { TrustNetworkGraph }      from '../components/TrustNetworkGraph';

export function LiveSimulationPage() {
  const [splitPct, setSplitPct] = useState(55);
  const draggingRef = useRef(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const onDragStart = () => { draggingRef.current = true; };
  const onMouseMove = (e: React.MouseEvent) => {
    if (!draggingRef.current || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const relY = ((e.clientY - rect.top) / rect.height) * 100;
    setSplitPct(Math.min(70, Math.max(30, relY)));
  };
  const onMouseUp = () => { draggingRef.current = false; };

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '280px 1fr',
      gridTemplateRows: '1fr 0px',
      height: 'calc(100vh - var(--topbar-h) - 40px)',
      overflow: 'hidden',
      gap: 0,
    }}>
      {/* Left: Control Panel */}
      <div style={{ gridRow: '1', gridColumn: '1', overflow: 'hidden' }}>
        <SimulationControlPanel />
      </div>

      {/* Right column: graph + metrics stacked with draggable divider */}
      <div ref={containerRef}
        style={{ gridRow: '1', gridColumn: '2', display: 'flex', flexDirection: 'column',
          overflow: 'hidden', position: 'relative' }}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseUp}
      >
        {/* Trust Network */}
        <div style={{ height: `${splitPct}%`, overflow: 'hidden', position: 'relative', minHeight: 200 }}>
          <TrustNetworkGraph />
          <NodeDetailPanel />
        </div>

        {/* Drag handle */}
        <div onMouseDown={onDragStart}
          style={{
            height: 4, background: 'var(--border)', cursor: 'ns-resize',
            flexShrink: 0, transition: 'background 120ms',
          }}
          onMouseEnter={(e) => { (e.target as HTMLElement).style.background = 'var(--accent)'; }}
          onMouseLeave={(e) => { (e.target as HTMLElement).style.background = 'var(--border)'; }}
        />

        {/* Metrics Panel */}
        <div style={{ flex: 1, overflow: 'auto', padding: 12, minHeight: 100 }}>
          <LiveMetricsPanel />
        </div>
      </div>

      {/* Bottom: Event Feed (full width) */}
      <div style={{ gridColumn: '1 / -1', gridRow: '2' }}>
        <EventFeed />
      </div>
    </div>
  );
}
