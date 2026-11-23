import { useEffect, useRef, useState } from "react";
import { Graph, ArrowsCounterClockwise } from "@phosphor-icons/react";
import * as d3 from "d3";
import { useSimulationStore } from "../store/simulationStore";
interface Node extends d3.SimulationNodeDatum {
  id: string;
  trust: number;
  delegate: boolean;
  detected: boolean;
}
interface Edge extends d3.SimulationLinkDatum<Node> {
  source: string | Node;
  target: string | Node;
}
function color(t: number) {
  return t < 0.4 ? "#b0372a" : t < 0.7 ? "#9a6f1c" : "#3d6b4b";
}
export function TrustNetworkGraph() {
  const ref = useRef<SVGSVGElement>(null);
  const wrap = useRef<HTMLDivElement>(null);
  const positions = useRef(new Map<string, Node>());
  const zoomRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null);
  const [size, setSize] = useState({ width: 700, height: 340 });
  const trust = useSimulationStore((s) => s.trustScores);
  const detected = useSimulationStore((s) => s.isDetected);
  const delegates = useSimulationStore((s) => s.delegateNodes);
  const selected = useSimulationStore((s) => s.selectedNodeId);
  const select = useSimulationStore((s) => s.selectNode);
  const runId = useSimulationStore((s) => s.runId);
  useEffect(() => {
    positions.current.clear();
  }, [runId]);
  useEffect(() => {
    if (!wrap.current) return;
    const observer = new ResizeObserver(([e]) =>
      setSize({ width: e.contentRect.width, height: e.contentRect.height }),
    );
    observer.observe(wrap.current);
    return () => observer.disconnect();
  }, []);
  useEffect(() => {
    if (!ref.current || !Object.keys(trust).length) return;
    const { width: w, height: h } = size;
    const svg = d3.select(ref.current);
    svg.selectAll("*").remove();
    const root = svg.append("g");
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.4, 3])
      .on("zoom", (e) => root.attr("transform", String(e.transform)));
    zoomRef.current = zoom;
    svg.call(zoom);
    root.attr("transform", String(d3.zoomTransform(ref.current)));
    const nodes: Node[] = Object.entries(trust).map(([id, t], i) => {
      const old = positions.current.get(id);
      return {
        id,
        trust: t,
        delegate: delegates.includes(id),
        detected: detected[id] ?? false,
        x: old?.x ?? w / 2 + Math.cos(i * 2.4) * 75,
        y: old?.y ?? h / 2 + Math.sin(i * 2.4) * 75,
      };
    });
    const links: Edge[] = [];
    const seen = new Set<string>();
    nodes
      .filter((n) => n.delegate)
      .forEach((n, i) => {
        for (let j = 1; j <= Math.min(3, nodes.length - 1); j++) {
          const target = nodes[(i + j) % nodes.length];
          if (target.id === n.id) continue;
          const key = [n.id, target.id].sort().join(":");
          if (!seen.has(key)) {
            seen.add(key);
            links.push({ source: n.id, target: target.id });
          }
        }
      });
    const lines = root
      .append("g")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke", "#c9c0ad")
      .attr("stroke-width", 1)
      .attr("stroke-opacity", 0.65);
    const groups = root
      .append("g")
      .selectAll<SVGGElement, Node>("g")
      .data(nodes)
      .join("g")
      .attr("role", "button")
      .attr("tabindex", 0)
      .attr("aria-label", (d) => `${d.id}, trust ${d.trust.toFixed(3)}`)
      .style("cursor", "pointer")
      .on("click", (_, d) => select(d.id))
      .on("keydown", (e, d) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          select(d.id);
        }
      });
    groups
      .append("circle")
      .attr("r", (d) => (d.delegate ? 19 : 14))
      .attr("fill", (d) => (d.delegate ? "#e6e9ee" : "#fbfaf6"))
      .attr("stroke", (d) =>
        d.id === selected
          ? "#1d1c19"
          : d.detected
            ? "#b0372a"
            : d.delegate
              ? "#1f3a5f"
              : "#d8d0be",
      )
      .attr("stroke-width", (d) =>
        d.id === selected || d.detected ? 2.5 : 1.5,
      );
    groups
      .append("circle")
      .attr("r", (d) => 5 + d.trust * 4)
      .attr("fill", (d) => color(d.trust));
    if (nodes.length <= 40)
      groups
        .append("text")
        .attr("text-anchor", "middle")
        .attr("y", 32)
        .attr("fill", "#6e695e")
        .attr("font-family", "var(--font-sans)")
        .attr("font-size", 10)
        .text((d) => d.id.replace("Node_", "N"));
    groups
      .append("title")
      .text(
        (d) =>
          `${d.id}\nTrust: ${d.trust.toFixed(3)}\n${d.delegate ? "Active delegate" : "Network participant"}${d.detected ? " / Flagged" : ""}`,
      );
    const sim = d3
      .forceSimulation(nodes)
      .force("charge", d3.forceManyBody().strength(-95))
      .force("center", d3.forceCenter(w / 2, h / 2 - 15))
      .force("collision", d3.forceCollide(27))
      .force("x", d3.forceX(w / 2).strength(0.07))
      .force("y", d3.forceY(h / 2 - 15).strength(0.12))
      .force(
        "links",
        d3
          .forceLink<Node, Edge>(links)
          .id((d) => d.id)
          .distance(95),
      );
    sim.on("tick", () => {
      nodes.forEach((n) => {
        n.x = Math.max(28, Math.min(w - 28, n.x ?? 0));
        n.y = Math.max(24, Math.min(h - 55, n.y ?? 0));
        positions.current.set(n.id, n);
      });
      groups.attr("transform", (d) => `translate(${d.x},${d.y})`);
      lines
        .attr("x1", (d) => (d.source as Node).x ?? 0)
        .attr("y1", (d) => (d.source as Node).y ?? 0)
        .attr("x2", (d) => (d.target as Node).x ?? 0)
        .attr("y2", (d) => (d.target as Node).y ?? 0);
    });
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      sim.stop();
      sim.tick(100);
      nodes.forEach((n) => positions.current.set(n.id, n));
      groups.attr("transform", (d) => `translate(${d.x},${d.y})`);
      lines
        .attr("x1", (d) => (d.source as Node).x ?? 0)
        .attr("y1", (d) => (d.source as Node).y ?? 0)
        .attr("x2", (d) => (d.target as Node).x ?? 0)
        .attr("y2", (d) => (d.target as Node).y ?? 0);
    }
    return () => {
      sim.stop();
      svg.on(".zoom", null);
    };
  }, [trust, detected, delegates, selected, select, size]);
  const empty = !Object.keys(trust).length;
  return (
    <div ref={wrap} style={{ height: "100%", position: "relative" }}>
      {empty ? (
        <div className="network-empty">
          <div className="network-empty-icon">
            <Graph size={32} weight="light" />
          </div>
          <h3>No run on the bench</h3>
          <p>
            Start an experiment to plot each node's trust, the delegates chosen
            each step, and nodes quarantined by the trust backend.
          </p>
        </div>
      ) : (
        <svg
          ref={ref}
          width="100%"
          height="100%"
          aria-label="Interactive trust network"
        />
      )}
      {!empty && (
        <>
          <button
            className="quiet-button graph-reset"
            onClick={() => {
              if (ref.current && zoomRef.current)
                d3.select(ref.current).call(
                  zoomRef.current.transform,
                  d3.zoomIdentity,
                );
            }}
          >
            <ArrowsCounterClockwise size={13} />
            Reset view
          </button>
          <div className="network-legend">
            {[
              ["#3d6b4b", "High trust"],
              ["#9a6f1c", "Mid trust"],
              ["#b0372a", "Low trust"],
            ].map(([c, l]) => (
              <span className="legend-item" key={l}>
                <i className="legend-node" style={{ background: c }} />
                {l}
              </span>
            ))}
            <span className="legend-item">
              <i
                className="legend-node"
                style={{
                  border: "2px solid var(--accent)",
                  background: "white",
                  width: 10,
                  height: 10,
                }}
              />
              Delegate
            </span>
          </div>
        </>
      )}
    </div>
  );
}
