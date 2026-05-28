import { useEffect, useMemo, useRef } from 'react';
import * as d3 from 'd3';

import { useSimulationStore } from '../store/simulationStore';

interface GraphNode extends d3.SimulationNodeDatum {
  id: string;
  trust: number;
  malicious: boolean;
  detected: boolean;
  delegate: boolean;
}

function trustColor(trust: number): string {
  if (trust <= 0.4) return d3.interpolateRgb('#ef4444', '#f59e0b')((trust / 0.4));
  if (trust <= 0.9) return d3.interpolateRgb('#f59e0b', '#22c55e')(((trust - 0.4) / 0.5));
  return d3.interpolateRgb('#22c55e', '#4f8ef7')(((trust - 0.9) / 0.1));
}

export function TrustNetworkGraph() {
  const svgRef       = useRef<SVGSVGElement | null>(null);
  const simRef       = useRef<d3.Simulation<GraphNode, undefined> | null>(null);
  const prevDetected = useRef<Set<string>>(new Set());

  const trustScores  = useSimulationStore((s) => s.trustScores);
  const isMalicious  = useSimulationStore((s) => s.isMalicious);
  const isDetected   = useSimulationStore((s) => s.isDetected);
  const delegateNodes = useSimulationStore((s) => s.delegateNodes);
  const selectNode   = useSimulationStore((s) => s.selectNode);
  const selectedNodeId = useSimulationStore((s) => s.selectedNodeId);

  const nodes = useMemo<GraphNode[]>(
    () => Object.keys(trustScores).map((id) => ({
      id,
      trust:    trustScores[id]   ?? 0.5,
      malicious: isMalicious[id]  ?? false,
      detected: isDetected[id]    ?? false,
      delegate: delegateNodes.includes(id),
    })),
    [trustScores, isMalicious, isDetected, delegateNodes],
  );

  const showLabels = nodes.length <= 32;

  useEffect(() => {
    if (!svgRef.current || nodes.length === 0) return;

    const W = svgRef.current.clientWidth || 720;
    const H = 420;
    const svg = d3.select(svgRef.current);

    // On first render build simulation
    if (!simRef.current) {
      svg.selectAll('*').remove();

      const defs = svg.append('defs');
      const filt = defs.append('filter').attr('id', 'glow');
      filt.append('feGaussianBlur').attr('stdDeviation', 3).attr('result', 'blur');
      const merge = filt.append('feMerge');
      merge.append('feMergeNode').attr('in', 'blur');
      merge.append('feMergeNode').attr('in', 'SourceGraphic');

      // Zoom
      const zoom = d3.zoom<SVGSVGElement, unknown>()
        .scaleExtent([0.3, 3])
        .on('zoom', (event) => {
          svg.select('g.root').attr('transform', event.transform as unknown as string);
        });
      svg.call(zoom);

      const root = svg.append('g').attr('class', 'root');
      root.append('g').attr('class', 'links');
      root.append('g').attr('class', 'nodes');

      // Delegate-neighbourhood links only (k=5 nearest by index)
      const links: { source: string; target: string }[] = [];
      nodes.forEach((n) => {
        if (!n.delegate) return;
        const nearest = nodes
          .filter((m) => m.id !== n.id)
          .slice(0, Math.min(5, nodes.length - 1));
        nearest.forEach((m) => {
          if (!links.find((l) => (l.source === n.id && l.target === m.id) || (l.source === m.id && l.target === n.id))) {
            links.push({ source: n.id, target: m.id });
          }
        });
      });

      const sim = d3.forceSimulation(nodes)
        .force('charge', d3.forceManyBody().strength(-250))
        .force('center', d3.forceCenter(W / 2, H / 2))
        .force('collision', d3.forceCollide<GraphNode>().radius((n) => 8 + n.trust * 12 + 4))
        .force('link', d3.forceLink<GraphNode, { source: string; target: string }>(links).id((n) => n.id).distance(80));
      simRef.current = sim;

      const linkSel = root.select<SVGGElement>('g.links')
        .selectAll('line')
        .data(links)
        .join('line')
        .attr('stroke', 'var(--border-strong)')
        .attr('stroke-width', 0.5);

      const nodeSel = root.select<SVGGElement>('g.nodes')
        .selectAll<SVGGElement, GraphNode>('g.node')
        .data(nodes, (d) => d.id)
        .join('g')
        .attr('class', 'node')
        .style('cursor', 'pointer')
        .on('click', (_, d) => selectNode(d.id));

      nodeSel.append('circle')
        .attr('r', (d) => 8 + d.trust * 12)
        .attr('fill', (d) => trustColor(d.trust))
        .attr('stroke', 'rgba(255,255,255,0.1)')
        .attr('stroke-width', 1.5);

      // Delegate outer ring
      nodeSel.filter((d) => d.delegate)
        .append('circle')
        .attr('class', 'delegate-ring')
        .attr('r', (d) => 8 + d.trust * 12 + 5)
        .attr('fill', 'none')
        .attr('stroke', '#4f8ef7')
        .attr('stroke-width', 1.5)
        .attr('stroke-opacity', 0.4)
        .attr('filter', 'url(#glow)');

      if (showLabels) {
        nodeSel.append('text')
          .attr('text-anchor', 'middle')
          .attr('dy', (d) => 8 + d.trust * 12 + 14)
          .attr('fill', 'var(--text-muted)')
          .attr('font-size', 9)
          .attr('font-family', 'var(--font-mono)')
          .text((d) => d.id.replace('Node_', 'N'));
      }

      sim.on('tick', () => {
        linkSel
          .attr('x1', (d: d3.SimulationLinkDatum<GraphNode>) => (d.source as GraphNode).x ?? 0)
          .attr('y1', (d: d3.SimulationLinkDatum<GraphNode>) => (d.source as GraphNode).y ?? 0)
          .attr('x2', (d: d3.SimulationLinkDatum<GraphNode>) => (d.target as GraphNode).x ?? 0)
          .attr('y2', (d: d3.SimulationLinkDatum<GraphNode>) => (d.target as GraphNode).y ?? 0);

        root.select('g.nodes').selectAll<SVGGElement, GraphNode>('g.node')
          .attr('transform', (d) => `translate(${d.x ?? 0},${d.y ?? 0})`);
      });
    } else {
      // Update existing — merge node data, gentle drift
      simRef.current.nodes(nodes);
      simRef.current.alpha(0.08).restart();
    }

    // Visual updates with transitions
    const nodeSel = svg.select('g.root').select<SVGGElement>('g.nodes')
      .selectAll<SVGGElement, GraphNode>('g.node');

    nodeSel.select('circle:first-child')
      .transition().duration(200)
      .attr('r', (d) => 8 + d.trust * 12)
      .attr('fill', (d) => trustColor(d.trust))
      .attr('stroke', (d) => {
        if (d.detected) return '#ef4444';
        if (d.delegate) return '#4f8ef7';
        return 'rgba(255,255,255,0.1)';
      })
      .attr('stroke-width', (d) => d.detected ? 3 : d.delegate ? 2 : 1.5);

    // Selected node highlight
    nodeSel.select('circle:first-child')
      .attr('stroke', (d) => {
        if (d.id === selectedNodeId) return '#ffffff';
        if (d.detected) return '#ef4444';
        if (d.delegate) return '#4f8ef7';
        return 'rgba(255,255,255,0.1)';
      });

    // Flash newly-detected nodes
    const currentDetected = new Set(nodes.filter((n) => n.detected).map((n) => n.id));
    nodeSel.filter((d) => d.detected && !prevDetected.current.has(d.id))
      .select('circle:first-child')
      .classed('flash-detected', true)
      .on('animationend', function () { d3.select(this).classed('flash-detected', false); });
    prevDetected.current = currentDetected;

    // Link opacity
    svg.select('g.root').select<SVGGElement>('g.links').selectAll<SVGLineElement, { source: GraphNode; target: GraphNode }>('line')
      .attr('stroke-opacity', (d) => {
        const ta = d.source.trust ?? 0.5;
        const tb = d.target.trust ?? 0.5;
        return ta * tb * 0.4;
      });

  }, [nodes, selectNode, selectedNodeId, showLabels]);

  // Cleanup on unmount
  useEffect(() => () => { simRef.current?.stop(); }, []);

  return (
    <div style={{ position: 'relative', height: '100%', background: 'var(--bg-base)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
      {nodes.length === 0 ? (
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          height: '100%', color: 'var(--text-muted)', fontSize: 13,
        }}>
          Start or replay a simulation to see the live trust network.
        </div>
      ) : (
        <svg ref={svgRef} style={{ width: '100%', height: '100%', display: 'block' }} />
      )}

      {/* Legend */}
      <div style={{
        position: 'absolute', bottom: 10, left: 10,
        background: 'rgba(10,13,20,0.85)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius-sm)', padding: '6px 10px', fontSize: 9,
        display: 'flex', flexDirection: 'column', gap: 4,
      }}>
        {[['#22c55e', 'High trust'], ['#f59e0b', 'Mid trust'], ['#ef4444', 'Low trust']].map(([c, l]) => (
          <div key={l} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: c, flexShrink: 0 }} />
            <span style={{ color: 'var(--text-secondary)' }}>{l}</span>
          </div>
        ))}
        <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', border: '2px solid #4f8ef7', flexShrink: 0 }} />
          <span style={{ color: 'var(--text-secondary)' }}>Delegate</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', border: '3px solid #ef4444', flexShrink: 0 }} />
          <span style={{ color: 'var(--text-secondary)' }}>Byzantine</span>
        </div>
      </div>

      {/* Reset view */}
      <button
        onClick={() => { if (svgRef.current) d3.select(svgRef.current).call(d3.zoom<SVGSVGElement, unknown>().transform, d3.zoomIdentity); }}
        style={{
          position: 'absolute', top: 8, right: 8,
          background: 'var(--bg-elevated)', border: '1px solid var(--border)',
          borderRadius: 'var(--radius-sm)', padding: '4px 8px',
          fontSize: 10, color: 'var(--text-secondary)', cursor: 'pointer',
        }}>
        ↺ Reset
      </button>
    </div>
  );
}
