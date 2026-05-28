import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { useSimulationStore } from '../store/simulationStore';

interface NodeInfo {
  id: string;
  trust: number;
  malicious: boolean;
  detected: boolean;
  delegate: boolean;
}

interface SelectedNode extends NodeInfo {}

function trustColor(t: number): string {
  // red (#ef4444) → amber (#f59e0b) → green (#10b981)
  if (t <= 0.5) {
    const r = d3.interpolateRgb('#ef4444', '#f59e0b')(t * 2);
    return r;
  }
  return d3.interpolateRgb('#f59e0b', '#10b981')((t - 0.5) * 2);
}

function trustRadius(t: number): number {
  return 8 + t * 12; // 8–20
}

export function TrustNetworkGraph() {
  const svgRef = useRef<SVGSVGElement>(null);
  const simRef = useRef<d3.Simulation<d3.SimulationNodeDatum & { id: string }, undefined> | null>(null);
  const { trustScores, isMalicious, isDetected, delegateNodes } = useSimulationStore();
  const [selected, setSelected] = useState<SelectedNode | null>(null);

  // Build node list from trustScores keys
  const nodeIds = Object.keys(trustScores);

  useEffect(() => {
    if (!svgRef.current || nodeIds.length === 0) return;

    const svg = d3.select(svgRef.current);
    const width = svgRef.current.clientWidth || 700;
    const height = 400;

    // First render: build simulation and DOM
    if (!simRef.current) {
      svg.selectAll('*').remove();

      const defs = svg.append('defs');
      // Glow filter for delegates
      const filter = defs.append('filter').attr('id', 'glow');
      filter.append('feGaussianBlur').attr('stdDeviation', 3).attr('result', 'coloredBlur');
      const feMerge = filter.append('feMerge');
      feMerge.append('feMergeNode').attr('in', 'coloredBlur');
      feMerge.append('feMergeNode').attr('in', 'SourceGraphic');

      svg.append('g').attr('class', 'links');
      svg.append('g').attr('class', 'nodes');

      const nodes = nodeIds.map((id) => ({ id, x: width / 2, y: height / 2 }));
      // Full mesh links
      const links: { source: string; target: string }[] = [];
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          links.push({ source: nodes[i].id, target: nodes[j].id });
        }
      }

      const sim = d3.forceSimulation(nodes as (d3.SimulationNodeDatum & { id: string })[])
        .force('charge', d3.forceManyBody().strength(-200))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('link', d3.forceLink(links).id((d: any) => d.id).distance(60))
        .force('collision', d3.forceCollide(22));

      simRef.current = sim;

      // Draw links
      svg.select('.links')
        .selectAll('line')
        .data(links)
        .join('line')
        .attr('stroke', '#334155')
        .attr('stroke-width', 1);

      // Draw nodes
      const nodeG = svg.select('.nodes')
        .selectAll<SVGGElement, { id: string }>('g.node')
        .data(nodes, (d) => d.id)
        .join('g')
        .attr('class', 'node')
        .style('cursor', 'pointer')
        .on('click', (_e, d) => {
          const info: SelectedNode = {
            id: d.id,
            trust: trustScores[d.id] ?? 0.5,
            malicious: isMalicious[d.id] ?? false,
            detected: isDetected[d.id] ?? false,
            delegate: delegateNodes.includes(d.id),
          };
          setSelected((prev) => prev?.id === d.id ? null : info);
        });

      nodeG.append('circle')
        .attr('r', (d) => trustRadius(trustScores[d.id] ?? 0.5))
        .attr('fill', (d) => trustColor(trustScores[d.id] ?? 0.5))
        .attr('stroke', '#334155')
        .attr('stroke-width', 1);

      nodeG.append('text')
        .attr('dy', (d) => trustRadius(trustScores[d.id] ?? 0.5) + 12)
        .attr('text-anchor', 'middle')
        .attr('font-size', 9)
        .attr('fill', '#64748b')
        .text((d) => d.id.replace('Node_', 'N'));

      sim.on('tick', () => {
        svg.select('.links').selectAll<SVGLineElement, { source: any; target: any }>('line')
          .attr('x1', (d) => d.source.x)
          .attr('y1', (d) => d.source.y)
          .attr('x2', (d) => d.target.x)
          .attr('y2', (d) => d.target.y);

        svg.select('.nodes').selectAll<SVGGElement, { id: string; x: number; y: number }>('g.node')
          .attr('transform', (d) => `translate(${d.x},${d.y})`);
      });
    }

    // Every render: update visual properties with transitions
    const nodeG = svg.select('.nodes').selectAll<SVGGElement, { id: string }>('g.node');

    nodeG.select('circle')
      .transition().duration(200)
      .attr('r', (d) => trustRadius(trustScores[d.id] ?? 0.5))
      .attr('fill', (d) => trustColor(trustScores[d.id] ?? 0.5))
      .attr('stroke', (d) => {
        if (isDetected[d.id]) return '#ef4444';
        if (delegateNodes.includes(d.id)) return '#3b82f6';
        return '#334155';
      })
      .attr('stroke-width', (d) => {
        if (isDetected[d.id]) return 3;
        if (delegateNodes.includes(d.id)) return 2;
        return 1;
      })
      .attr('filter', (d) => delegateNodes.includes(d.id) ? 'url(#glow)' : null);

    // Flash detected nodes
    nodeG.filter((d) => !!isDetected[d.id])
      .select('circle')
      .classed('byzantine-flash', true)
      .on('animationend', function () {
        d3.select(this).classed('byzantine-flash', false);
      });

    // Update link opacity based on trust product
    const nodesById: Record<string, number> = {};
    nodeIds.forEach((id) => { nodesById[id] = trustScores[id] ?? 0.5; });
    svg.select('.links').selectAll<SVGLineElement, { source: any; target: any }>('line')
      .attr('stroke-opacity', (d) => {
        const ta = nodesById[d.source.id ?? d.source] ?? 0.5;
        const tb = nodesById[d.target.id ?? d.target] ?? 0.5;
        return Math.sqrt(ta * tb) * 0.35;
      });

    // Gentle drift update
    if (simRef.current) {
      simRef.current.alpha(0.1).restart();
    }
  }, [trustScores, isDetected, delegateNodes]);

  return (
    <div className="bg-surface rounded-xl p-4 flex flex-col gap-3">
      <h2 className="text-text-primary font-semibold text-base">Trust Network</h2>
      <div className="relative">
        <svg
          ref={svgRef}
          className="w-full rounded-lg bg-bg"
          style={{ height: 400 }}
        />
        {nodeIds.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center text-muted text-sm">
            Start a simulation to see the live network
          </div>
        )}
      </div>

      {selected && (
        <div className="bg-bg rounded-lg p-3 text-sm space-y-1 border border-slate-700">
          <div className="flex justify-between">
            <span className="font-semibold text-text-primary">{selected.id}</span>
            <button onClick={() => setSelected(null)} className="text-muted hover:text-text-primary">✕</button>
          </div>
          <div className="grid grid-cols-2 gap-1 text-xs">
            <span className="text-muted">Trust Score</span>
            <span className="text-right" style={{ color: trustColor(selected.trust) }}>
              {(selected.trust * 100).toFixed(1)}%
            </span>
            <span className="text-muted">Ground Truth</span>
            <span className={`text-right ${selected.malicious ? 'text-danger' : 'text-success'}`}>
              {selected.malicious ? 'Malicious' : 'Honest'}
            </span>
            <span className="text-muted">Detected</span>
            <span className={`text-right ${selected.detected ? 'text-warning' : 'text-muted'}`}>
              {selected.detected ? 'Byzantine' : '—'}
            </span>
            <span className="text-muted">Role</span>
            <span className={`text-right ${selected.delegate ? 'text-accent' : 'text-muted'}`}>
              {selected.delegate ? 'Delegate' : 'Standard'}
            </span>
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="flex flex-wrap gap-3 text-xs text-muted">
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-full bg-success" /> High trust
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-full bg-warning" /> Mid trust
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-full bg-danger" /> Low trust
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-full border-2 border-danger" /> Detected
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-full border-2 border-accent" /> Delegate
        </span>
      </div>
    </div>
  );
}
