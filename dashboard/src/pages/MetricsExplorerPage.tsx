import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChartLine, DownloadSimple } from "@phosphor-icons/react";
import {
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { apiClient } from "../api/client";
import { useResults } from "../hooks/useResults";
import { MetricCard } from "../components/ui/MetricCard";
const fields = [
  ["F1 Score", "Detection F1"],
  ["Cumulative Reward", "Cumulative reward"],
  ["Blockchain Length", "Blockchain length"],
  ["Throughput", "Transactions in last block"],
  ["Trust Decay Rate", "Trust decay rate"],
  ["Consensus Threshold", "Consensus threshold"],
];
export function MetricsExplorerPage() {
  const { data: runs = [], isError: resultsError } = useResults();
  const [runId, setRunId] = useState("");
  const [window, setWindow] = useState(100);
  const {
    data: rows = [],
    isPending,
    isError,
  } = useQuery({
    queryKey: ["metrics", runId],
    enabled: !!runId,
    queryFn: async () =>
      (
        await apiClient.get<Record<string, number>[]>(
          `/results/${runId}/metrics`,
        )
      ).data,
  });
  const [prevRunId, setPrevRunId] = useState(runId);
  if (runId !== prevRunId) {
    setPrevRunId(runId);
    setWindow(100);
  }
  const data = useMemo(
    () => rows.slice(0, Math.max(1, Math.ceil((rows.length * window) / 100))),
    [rows, window],
  );
  const last = data.at(-1);
  return (
    <div className="metrics-workspace">
      <section className="data-panel">
        <div className="run-selector">
          <label htmlFor="metrics-run">Recorded experiment</label>
          <select
            id="metrics-run"
            value={runId}
            onChange={(e) => setRunId(e.target.value)}
          >
            <option value="">Choose an experiment</option>
            {runs.map((r) => (
              <option key={r.run_id} value={r.run_id}>
                {r.run_id} / F1 {r.final_f1?.toFixed(3) ?? "unavailable"}
              </option>
            ))}
          </select>
          {runId && (
            <a className="quiet-button" href={`/results/${runId}/download`}>
              <DownloadSimple size={16} />
              Source CSV
            </a>
          )}
        </div>
        {!!rows.length && (
          <div className="episode-scrubber">
            <label htmlFor="episode-window">
              Episode window{" "}
              <output>
                {data.length} / {rows.length}
              </output>
            </label>
            <input
              id="episode-window"
              type="range"
              min={1}
              max={100}
              value={window}
              onChange={(e) => setWindow(Number(e.target.value))}
            />
          </div>
        )}
      </section>
      {resultsError || isError ? (
        <div className="research-callout" role="alert">
          Could not load recorded metrics. Check the simulation engine
          connection.
        </div>
      ) : !runId ? (
        <div className="data-panel empty-state">
          <ChartLine size={34} weight="light" />
          <h3>Explore the evidence behind a run</h3>
          <p>
            Choose a recorded experiment to inspect its F1 trajectory, reward,
            blockchain growth, and adaptive parameters.
          </p>
        </div>
      ) : isPending ? (
        <div className="loading-state">Loading episode metrics...</div>
      ) : (
        <>
          <div className="metric-grid">
            <MetricCard label="Episodes in view" value={data.length} />
            <MetricCard
              label="Latest F1"
              value={last?.["F1 Score"]?.toFixed(3) ?? "--"}
            />
            <MetricCard
              label="Latest reward"
              value={last?.["Cumulative Reward"]?.toFixed(1) ?? "--"}
            />
            <MetricCard
              label="Chain length"
              value={last?.["Blockchain Length"] ?? "--"}
            />
          </div>
          <div className="analysis-chart-grid">
            {fields.map(([key, label], i) => (
              <section className="chart-panel" key={key}>
                <header>
                  <h3>{label}</h3>
                  <span>By episode</span>
                </header>
                {data.some((r) => r[key] !== undefined) ? (
                  <ResponsiveContainer width="100%" height={220}>
                    <LineChart
                      data={data}
                      margin={{ top: 8, right: 12, left: -15, bottom: 0 }}
                    >
                      <CartesianGrid stroke="var(--border)" vertical={false} />
                      <XAxis
                        dataKey="Episode"
                        tickLine={false}
                        axisLine={false}
                        stroke="var(--text-muted)"
                      />
                      <YAxis
                        domain={key === "F1 Score" ? [0, 1] : ["auto", "auto"]}
                        tickLine={false}
                        axisLine={false}
                        stroke="var(--text-muted)"
                        width={62}
                      />
                      <Tooltip
                        contentStyle={{
                          background: "white",
                          border: "1px solid var(--border)",
                          borderRadius: 6,
                          fontSize: 12,
                        }}
                      />
                      <Line
                        dataKey={key}
                        name={label}
                        stroke={i % 2 ? "var(--cyan)" : "var(--accent)"}
                        strokeWidth={2}
                        dot={data.length === 1}
                        isAnimationActive={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="chart-empty">
                    This metric was not recorded for this run.
                  </div>
                )}
              </section>
            ))}
          </div>
          <p className="data-note">
            Charts display values from the saved episode metrics CSV. Throughput
            in this dataset is a last-block transaction count, not transactions
            per second.
          </p>
        </>
      )}
    </div>
  );
}
