import {
  Line,
  LineChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  ReferenceLine,
} from "recharts";
import { useSimulationStore } from "../store/simulationStore";
import { MetricCard } from "./ui/MetricCard";
const tooltip = {
  contentStyle: {
    background: "white",
    border: "1px solid var(--border)",
    borderRadius: 6,
    fontSize: 11,
  },
  labelStyle: { color: "var(--text-secondary)" },
};
export function LiveMetricsPanel() {
  const history = useSimulationStore((s) => s.episodeHistory);
  const latest = useSimulationStore((s) => s.latestStep);
  const last = history.at(-1),
    prev = history.at(-2);
  const data = history.slice(-100).map((e) => ({
    episode: e.episode + 1,
    f1: e.f1_score,
    precision: e.precision,
    recall: e.recall,
    separation: e.trust_separation,
  }));
  return (
    <div className="live-metrics">
      <div className="metric-grid">
        <MetricCard
          label="Detection F1"
          value={latest ? latest.f1_score.toFixed(3) : "--"}
          delta={last && prev ? last.f1_score - prev.f1_score : undefined}
        />
        <MetricCard
          label="Precision"
          value={latest ? latest.precision.toFixed(3) : "--"}
          deltaLabel="Malicious class"
        />
        <MetricCard
          label="Recall"
          value={latest ? latest.recall.toFixed(3) : "--"}
          deltaLabel="Malicious class"
        />
        <MetricCard
          label="Verified transactions"
          value={latest?.transactions_verified ?? "--"}
          unit="/ event"
          deltaLabel="Reported by current event"
        />
        <MetricCard
          label="Quarantined"
          value={latest?.quarantined ? latest.quarantined.length : "--"}
          deltaLabel={
            latest?.quarantine_events?.length
              ? `New: ${latest.quarantine_events.join(", ")}`
              : latest?.trust_backend ?? "Trust backend"
          }
        />
        <MetricCard
          label="Audited decision error"
          value={
            latest?.audited_error !== undefined && latest?.audited_error !== null
              ? latest.audited_error.toFixed(3)
              : "--"
          }
          deltaLabel={latest?.audited !== undefined ? `${latest.audited} audited` : "Observable signal"}
        />
        <MetricCard
          label="HE tally time"
          value={latest?.fhe_overhead_ms != null ? latest.fhe_overhead_ms.toFixed(1) : "--"}
          unit="ms"
          deltaLabel={
            latest?.tally_backend === "he"
              ? `${latest.he_flips ?? 0} flips vs plaintext`
              : "Plaintext tally"
          }
        />
      </div>
      <div className="chart-grid">
        <section className="chart-panel">
          <header>
            <h3>Detection performance</h3>
            <span>By episode</span>
          </header>
          {data.length ? (
            <ResponsiveContainer width="100%" height={180}>
              <LineChart
                data={data}
                margin={{ top: 5, right: 8, left: -24, bottom: 0 }}
              >
                <CartesianGrid stroke="var(--border)" vertical={false} />
                <XAxis
                  dataKey="episode"
                  tickLine={false}
                  axisLine={false}
                  stroke="var(--text-muted)"
                  minTickGap={25}
                />
                <YAxis
                  domain={[0, 1]}
                  tickLine={false}
                  axisLine={false}
                  stroke="var(--text-muted)"
                  ticks={[0, 0.5, 1]}
                />
                <Tooltip {...tooltip} />
                <Line
                  dataKey="f1"
                  name="F1"
                  stroke="var(--accent)"
                  strokeWidth={2}
                  dot={data.length === 1}
                  isAnimationActive={false}
                />
                <Line
                  dataKey="precision"
                  name="Precision"
                  stroke="var(--cyan)"
                  strokeDasharray="4 3"
                  dot={data.length === 1}
                  isAnimationActive={false}
                />
                <Line
                  dataKey="recall"
                  name="Recall"
                  stroke="var(--amber)"
                  strokeDasharray="2 3"
                  dot={data.length === 1}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="chart-empty">Episode metrics will appear here</div>
          )}
          <div className="chart-legend">
            {[
              ["var(--accent)", "F1 score"],
              ["var(--cyan)", "Precision"],
              ["var(--amber)", "Recall"],
            ].map(([c, l]) => (
              <span key={l}>
                <i className="chart-key" style={{ background: c }} />
                {l}
              </span>
            ))}
          </div>
        </section>
        <section className="chart-panel">
          <header>
            <h3>Trust separation</h3>
            <span>Honest - malicious</span>
          </header>
          {data.length ? (
            <ResponsiveContainer width="100%" height={180}>
              <LineChart
                data={data}
                margin={{ top: 5, right: 8, left: -24, bottom: 0 }}
              >
                <CartesianGrid stroke="var(--border)" vertical={false} />
                <XAxis
                  dataKey="episode"
                  tickLine={false}
                  axisLine={false}
                  stroke="var(--text-muted)"
                />
                <YAxis
                  domain={[-1, 1]}
                  ticks={[-1, 0, 1]}
                  tickLine={false}
                  axisLine={false}
                  stroke="var(--text-muted)"
                />
                <Tooltip {...tooltip} />
                <ReferenceLine
                  y={0}
                  stroke="var(--border-strong)"
                  strokeDasharray="3 3"
                />
                <Line
                  dataKey="separation"
                  name="Trust separation"
                  stroke="var(--accent)"
                  strokeWidth={2}
                  dot={data.length === 1}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="chart-empty">
              Waiting for measured trust separation
            </div>
          )}
          <div className="chart-legend">
            <span>
              <i
                className="chart-key"
                style={{ background: "var(--accent)" }}
              />
              Reported mean trust difference
            </span>
          </div>
        </section>
      </div>
    </div>
  );
}
