import { useEffect, useRef, useState } from "react";
import { CaretDown, CaretUp, Pause, Play } from "@phosphor-icons/react";
import { useSimulationStore } from "../store/simulationStore";
interface LogLine {
  id: string;
  time: string;
  text: string;
  color: string;
}
export function EventFeed() {
  const [lines, setLines] = useState<LogLine[]>([]);
  const [expanded, setExpanded] = useState(true);
  const [paused, setPaused] = useState(false);
  const latest = useSimulationStore((s) => s.latestStep);
  const runId = useSimulationStore((s) => s.runId);
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    setLines([]);
  }, [runId]);
  useEffect(() => {
    if (!latest || paused) return;
    const e = latest;
    const text =
      e.type === "episode_end"
        ? `Episode ${e.episode + 1} complete / F1 ${e.f1_score.toFixed(3)} / Reward ${e.reward.toFixed(2)}`
        : e.type === "error"
          ? e.action_description
          : `Episode ${e.episode + 1} / step ${e.step + 1} / ${e.transactions_verified} verified / ${e.delegate_nodes.length} delegates / F1 ${e.f1_score.toFixed(3)}`;
    const line = {
      id: `${e.timestamp}-${e.type}-${e.step}`,
      time: new Date(e.timestamp * 1000).toLocaleTimeString("en-GB"),
      text,
      color:
        e.type === "error"
          ? "var(--red)"
          : e.type === "episode_end"
            ? "var(--accent)"
            : "var(--text-secondary)",
    };
    setLines((prev) =>
      prev.some((l) => l.id === line.id) ? prev : [...prev, line].slice(-200),
    );
  }, [latest, paused]);
  useEffect(() => {
    if (ref.current && !paused)
      ref.current.scrollTop = ref.current.scrollHeight;
  }, [lines, paused]);
  return (
    <>
      <div className="log-header">
        <button
          className="text-button"
          aria-expanded={expanded}
          onClick={() => setExpanded((v) => !v)}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            fontSize: 12,
            fontWeight: 500,
            color: "var(--text-primary)",
          }}
        >
          {expanded ? <CaretDown size={14} /> : <CaretUp size={14} />}Event log
        </button>
        <div className="log-actions">
          <span className="log-count">{lines.length} events</span>
          <button
            className="text-button"
            onClick={() => setPaused((v) => !v)}
            aria-pressed={paused}
          >
            {paused ? <Play size={11} /> : <Pause size={11} />}{" "}
            {paused ? "Resume log" : "Pause log"}
          </button>
          <button className="text-button" onClick={() => setLines([])}>
            Clear
          </button>
        </div>
      </div>
      {expanded && (
        <div ref={ref} className="log-body">
          {!lines.length && (
            <p className="log-empty">
              Simulation events will appear here when an experiment starts.
            </p>
          )}
          {lines.map((l) => (
            <div className="log-line" key={l.id} style={{ color: l.color }}>
              <time>{l.time}</time>
              <span>{l.text}</span>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
