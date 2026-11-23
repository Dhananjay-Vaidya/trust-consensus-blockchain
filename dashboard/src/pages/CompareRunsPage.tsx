import { useMemo } from "react";
import { Scales } from "@phosphor-icons/react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useCompareRuns, useResults } from "../hooks/useResults";
import { useSimulationStore } from "../store/simulationStore";
const colors = [
  "#1f3a5f",
  "#4a6a80",
  "#9a6f1c",
  "#5d5470",
  "#7d4f5e",
  "#46433c",
];
export function CompareRunsPage() {
  const { data: runs = [], isError } = useResults();
  const ids = useSimulationStore((s) => s.selectedComparisonRuns);
  const toggle = useSimulationStore((s) => s.toggleComparisonRun);
  const selected = runs.filter((r) => ids.includes(r.run_id));
  const comparison = useCompareRuns(ids, "F1 Score");
  const data = useMemo(() => {
    if (!comparison.data) return [];
    const count = Math.max(
      0,
      ...Object.values(comparison.data.series).map((s) => s.length),
    );
    return Array.from({ length: count }, (_, i) =>
      Object.fromEntries([
        ["episode", i + 1],
        ...ids.map((id) => [id, comparison.data!.series[id]?.[i] ?? null]),
      ]),
    );
  }, [comparison.data, ids]);
  return (
    <div className="compare-workspace">
      <section className="data-panel">
        <div className="panel-heading">
          <div>
            <h2>Select experiments</h2>
            <p>Compare up to six recorded trajectories</p>
          </div>
          <span className="neutral-tag">{ids.length} / 6 selected</span>
        </div>
        <div className="comparison-selector">
          {runs.map((r) => {
            const active = ids.includes(r.run_id);
            return (
              <button
                className={`comparison-option ${active ? "selected" : ""}`}
                key={r.run_id}
                onClick={() => toggle(r.run_id)}
                aria-pressed={active}
                disabled={!active && ids.length >= 6}
              >
                <span className="comparison-option-title">
                  {r.agent.toUpperCase()} / {r.attack.toUpperCase()}
                  <strong>{r.final_f1?.toFixed(3) ?? "--"}</strong>
                </span>
                <small>
                  {r.nodes} nodes / {r.episodes} episodes
                </small>
                <span className="run-identifier" title={r.run_id}>
                  {r.run_id}
                </span>
              </button>
            );
          })}
          {!runs.length && (
            <p className="data-note">
              {isError
                ? "Could not load experiments. Check the engine connection."
                : "No saved experiments available."}
            </p>
          )}
        </div>
      </section>
      {selected.length < 2 ? (
        <div className="data-panel empty-state">
          <Scales size={34} weight="light" />
          <h3>Compare recorded outcomes</h3>
          <p>
            Select at least two experiments. For a controlled comparison, match
            node count, malicious fraction, training budget, and seed.
          </p>
        </div>
      ) : (
        <>
          <section className="chart-panel">
            <header>
              <h3>Detection F1 trajectory</h3>
              <span>Recorded episode metrics</span>
            </header>
            {comparison.isPending ? (
              <div className="loading-state">Loading comparison...</div>
            ) : comparison.isError ? (
              <div className="empty-state" role="alert">
                Could not load comparison metrics.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={320}>
                <LineChart
                  data={data}
                  margin={{ top: 10, right: 15, left: -20, bottom: 5 }}
                >
                  <CartesianGrid stroke="var(--border)" vertical={false} />
                  <XAxis
                    dataKey="episode"
                    axisLine={false}
                    tickLine={false}
                    stroke="var(--text-muted)"
                  />
                  <YAxis
                    domain={[0, 1]}
                    axisLine={false}
                    tickLine={false}
                    stroke="var(--text-muted)"
                  />
                  <Tooltip
                    contentStyle={{
                      background: "white",
                      border: "1px solid var(--border)",
                      fontSize: 12,
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: 11, paddingTop: 20 }} />
                  {selected.map((r, i) => (
                    <Line
                      key={r.run_id}
                      dataKey={r.run_id}
                      name={`${r.agent.toUpperCase()} / ${r.attack.toUpperCase()} / ${r.nodes}n / ${r.episodes}ep [${i + 1}]`}
                      stroke={colors[ids.indexOf(r.run_id)]}
                      strokeWidth={2}
                      strokeDasharray={i > 2 ? "5 3" : undefined}
                      dot={false}
                      connectNulls={false}
                      isAnimationActive={false}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            )}
          </section>
          <section className="data-panel">
            <div className="panel-heading">
              <h2>Recorded run summary</h2>
            </div>
            <div className="table-scroll">
              <table className="results-table">
                <thead>
                  <tr>
                    <th>Configuration</th>
                    {selected.map((r, i) => (
                      <th
                        key={r.run_id}
                        style={{ color: colors[ids.indexOf(r.run_id)] }}
                      >
                        Experiment {i + 1}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[
                    ["Agent", ...selected.map((r) => r.agent.toUpperCase())],
                    ["Attack", ...selected.map((r) => r.attack.toUpperCase())],
                    ["Nodes", ...selected.map((r) => r.nodes)],
                    ["Episodes", ...selected.map((r) => r.episodes)],
                    [
                      "Final F1",
                      ...selected.map((r) => r.final_f1?.toFixed(4) ?? "--"),
                    ],
                  ].map(([label, ...values]) => (
                    <tr key={label}>
                      <td>{label}</td>
                      {values.map((v, i) => (
                        <td
                          key={i}
                          className={label === "Final F1" ? "score-cell" : ""}
                        >
                          {v}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
          <p className="data-note">
            Only recorded metrics are displayed. A single run does not establish
            statistical significance; use repeated seeds and the experiment
            analysis scripts for paper conclusions.
          </p>
        </>
      )}
    </div>
  );
}
