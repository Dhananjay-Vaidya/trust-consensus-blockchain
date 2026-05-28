import { useEffect, useMemo, useRef, useState } from 'react';
import * as d3 from 'd3';

import { useSimulationStore } from '../store/simulationStore';

interface GraphNode {
  id: string;
  trust: number;
  malicious: boolean;
  detected: boolean;
  delegate: boolean;
  x?: number;
  y?: number;
}

function trustColor(trust: number): string {
  if (trust <= 0.45) return '#f87171';
  if (trust <= 0.7) return '#fbbf24';
  return '#34d399';
}

export function TrustNetworkGraph() {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const simulationRef = useRef<d3.Simulation<GraphNode, undefined> | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  const trustScores = useSimulationStore((state) => state.trustScores);
  const isMalicious = useSimulationStore((state) => state.isMalicious);
  const isDetected = useSimulationStore((state) => state.isDetected);
  const delegateNodes = useSimulationStore((state) => state.delegateNodes);

  const nodes = useMemo<GraphNode[]>(
    () =>
      Object.keys(trustScores).map((id) => ({
        id,
        trust: trustScores[id] ?? 0.5,
        malicious: isMalicious[id] ?? false,
        detected: isDetected[id] ?? false,
        delegate: delegateNodes.includes(id),
      })),
    [delegateNodes, isDetected, isMalicious, trustScores],
  );

  useEffect(() => {
    if (!svgRef.current || nodes.length === 0) return;

    const width = svgRef.current.clientWidth || 720;
    const height = 420;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const links = nodes.flatMap((source, index) =>
      nodes.slice(index + 1).map((target) => ({ source: source.id, target: target.id })),
    );

    const defs = svg.append('defs');
    const filter = defs.append('filter').attr('id', 'delegate-glow');
    filter.append('feGaussianBlur').attr('stdDeviation', 3).attr('result', 'blur');
    const merge = filter.append('feMerge');
    merge.append('feMergeNode').attr('in', 'blur');
    merge.append('feMergeNode').attr('in', 'SourceGraphic');

    const linkLayer = svg.append('g').attr('class', 'links');
    const nodeLayer = svg.append('g').attr('class', 'nodes');

    const simulation = d3
      .forceSimulation(nodes)
      .force('charge', d3.forceManyBody().strength(-220))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide<GraphNode>().radius((node) => 12 + node.trust * 16))
      .force('link', d3.forceLink<GraphNode, { source: string; target: string }>(links).id((node) => node.id).distance(80));

    simulationRef.current = simulation;

    const linkSelection = linkLayer
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', '#223047')
      .attr('stroke-opacity', 0.45);

    const nodeSelection = nodeLayer
      .selectAll('g')
      .data(nodes)
      .join('g')
      .style('cursor', 'pointer')
      .on('click', (_, node) => setSelectedNodeId((current) => (current === node.id ? null : node.id)));

    nodeSelection
      .append('circle')
      .attr('r', (node) => 10 + node.trust * 12)
      .attr('fill', (node) => trustColor(node.trust))
      .attr('stroke', (node) => (node.detected ? '#ffffff' : node.delegate ? '#60a5fa' : '#223047'))
      .attr('stroke-width', (node) => (node.detected ? 3 : node.delegate ? 2 : 1))
      .attr('filter', (node) => (node.delegate ? 'url(#delegate-glow)' : null));

    nodeSelection
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', 26)
      .attr('fill', '#94a3b8')
      .attr('font-size', 10)
      .text((node) => node.id.replace('Node_', 'N'));

    simulation.on('tick', () => {
      linkSelection
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      nodeSelection.attr('transform', (node) => `translate(${node.x},${node.y})`);
    });

    return () => {
      simulation.stop();
    };
  }, [nodes]);

  const selectedNode = nodes.find((node) => node.id === selectedNodeId) ?? null;

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <h3>Trust Network</h3>
          <p>Live node trust graph with delegate highlighting and Byzantine detection signals.</p>
        </div>
      </div>
      <div className="network-layout">
        <div className="network-canvas">
          {nodes.length === 0 ? (
            <div className="empty-state">Start or replay a simulation to populate the network.</div>
          ) : (
            <svg ref={svgRef} className="network-svg" viewBox="0 0 720 420" preserveAspectRatio="xMidYMid meet" />
          )}
        </div>
        <aside className="inspector-panel">
          <h4>Node Inspector</h4>
          {!selectedNode && <p className="subtle">Click a node to inspect trust, role, and detection state.</p>}
          {selectedNode && (
            <dl className="inspector-grid">
              <div><dt>Node</dt><dd>{selectedNode.id}</dd></div>
              <div><dt>Trust</dt><dd>{selectedNode.trust.toFixed(4)}</dd></div>
              <div><dt>Truth</dt><dd>{selectedNode.malicious ? 'Malicious' : 'Honest'}</dd></div>
              <div><dt>Detected</dt><dd>{selectedNode.detected ? 'Yes' : 'No'}</dd></div>
              <div><dt>Delegate</dt><dd>{selectedNode.delegate ? 'Yes' : 'No'}</dd></div>
            </dl>
          )}
        </aside>
      </div>
    </section>
  );
}
