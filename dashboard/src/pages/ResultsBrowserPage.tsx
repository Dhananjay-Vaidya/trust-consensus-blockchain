import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  MagnifyingGlass,
  ArrowClockwise,
  DownloadSimple,
  Play,
  Scales,
  FolderOpen,
} from "@phosphor-icons/react";
import { useResults } from "../hooks/useResults";
import { useSimulationStore } from "../store/simulationStore";
import { MetricCard } from "../components/ui/MetricCard";
export function ResultsBrowserPage() {
  const { data: runs = [], isPending, isError, refetch } = useResults();
  const navigate = useNavigate();
  const selected = useSimulationStore((s) => s.selectedComparisonRuns);
  const toggle = useSimulationStore((s) => s.toggleComparisonRun);
  const replay = useSimulationStore((s) => s.beginReplay);
  const [search, setSearch] = useState("");
  const [agent, setAgent] = useState("all");
  const [attack, setAttack] = useState("all");
  const [sort, setSort] = useState("recent");
  const filtered = useMemo(
    () =>
      runs
        .filter(
          (r) =>
            (agent === "all" || r.agent === agent) &&
            (attack === "all" || r.attack === attack) &&
            r.run_id.toLowerCase().includes(search.toLowerCase()),
        )
        .sort((a, b) =>
          sort === "f1"
            ? (b.final_f1 ?? -1) - (a.final_f1 ?? -1)
            : b.completed_at - a.completed_at,
        ),
    [runs, search, agent, attack, sort],
  );
  const best = runs.length
    ? Math.max(...runs.map((r) => r.final_f1 ?? 0))
    : null;
  return (
    <div className="results-workspace">
      <div className="metric-grid">
        <MetricCard label="Recorded experiments" value={runs.length} />
        <MetricCard
          label="Highest recorded F1"
          value={best === null ? "--" : best.toFixed(3)}
        />
        <MetricCard
          label="Agent families"
          value={new Set(runs.map((r) => r.agent)).size}
        />
        <MetricCard
          label="Attack configurations"
          value={new Set(runs.map((r) => r.attack)).size}
        />
      </div>
      <section className="data-panel">
        <div className="results-toolbar">
          <div className="search-field">
            <MagnifyingGlass size={17} />
            <input
              aria-label="Search run identifier"
              placeholder="Search experiments..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <select
            aria-label="Filter by agent"
            value={agent}
            onChange={(e) => setAgent(e.target.value)}
          >
            <option value="all">All agents</option>
            {["rl", "drl", "marl"].map((a) => (
              <option key={a} value={a}>
                {a.toUpperCase()}
              </option>
            ))}
          </select>
          <select
            aria-label="Filter by attack"
            value={attack}
            onChange={(e) => setAttack(e.target.value)}
          >
            <option value="all">All attacks</option>
            {["none", "nma", "cra", "aaa", "bfi", "tdp"].map((a) => (
              <option key={a} value={a}>
                {a.toUpperCase()}
              </option>
            ))}
          </select>
          <select
            aria-label="Sort experiments"
            value={sort}
            onChange={(e) => setSort(e.target.value)}
          >
            <option value="recent">Most recent</option>
            <option value="f1">Highest F1</option>
          </select>
          <button
            className="quiet-button"
            onClick={() => void refetch()}
            aria-label="Refresh results"
          >
            <ArrowClockwise size={17} />
          </button>
        </div>
        <div className="table-caption">
          <span>{filtered.length} experiments</span>
          <span>Select up to 6 runs to compare</span>
        </div>
        {isError ? (
          <div className="empty-state" role="alert">
            <h3>Could not load experiment results</h3>
            <p>Check the engine connection and refresh this view.</p>
            <button className="quiet-button" onClick={() => void refetch()}>
              Try again
            </button>
          </div>
        ) : isPending ? (
          <div className="loading-state">Loading recorded experiments...</div>
        ) : !filtered.length ? (
          <div className="empty-state">
            <FolderOpen size={30} weight="light" />
            <h3>
              {runs.length
                ? "No matching experiments"
                : "No experiments recorded yet"}
            </h3>
            <p>
              {runs.length
                ? "Adjust the search or filters to find your run."
                : "Run a simulation to generate metrics and a replayable event stream."}
            </p>
            <Link className="quiet-button" to="/">
              Open simulation workspace
            </Link>
          </div>
        ) : (
          <div className="table-scroll">
            <table className="results-table">
              <thead>
                <tr>
                  <th>
                    <span className="sr-only">Select</span>
                  </th>
                  <th>Experiment</th>
                  <th>Agent</th>
                  <th>Attack</th>
                  <th>Nodes</th>
                  <th>Final F1</th>
                  <th>Episodes</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((r) => (
                  <tr key={r.run_id}>
                    <td>
                      <input
                        type="checkbox"
                        aria-label={`Compare ${r.run_id}`}
                        checked={selected.includes(r.run_id)}
                        disabled={
                          !selected.includes(r.run_id) && selected.length >= 6
                        }
                        onChange={() => toggle(r.run_id)}
                      />
                    </td>
                    <td>
                      <span className="run-identifier" title={r.run_id}>
                        {r.run_id}
                      </span>
                      <span className="table-subtitle">
                        {new Date(r.completed_at * 1000).toLocaleString(
                          undefined,
                          { dateStyle: "medium", timeStyle: "short" },
                        )}
                      </span>
                    </td>
                    <td>
                      <span className="neutral-tag">
                        {r.agent.toUpperCase()}
                      </span>
                    </td>
                    <td>
                      <span
                        className={`neutral-tag ${r.attack === "none" ? "" : "attack-tag"}`}
                      >
                        {r.attack.toUpperCase()}
                      </span>
                    </td>
                    <td>{r.nodes}</td>
                    <td className="score-cell">
                      {r.final_f1?.toFixed(4) ?? "--"}
                    </td>
                    <td>{r.episodes}</td>
                    <td>
                      <div className="table-actions">
                        <button
                          className="quiet-button"
                          onClick={() => {
                            replay(r.run_id);
                            navigate("/");
                          }}
                        >
                          <Play size={13} />
                          Replay
                        </button>
                        <a
                          className="quiet-button"
                          href={`/results/${r.run_id}/download`}
                          title="Download metrics CSV"
                        >
                          <DownloadSimple size={15} />
                          <span className="sr-only">Download CSV</span>
                        </a>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
      {selected.length > 0 && (
        <div className="comparison-bar">
          <span>
            <strong>{selected.length}</strong> experiments selected
          </span>
          <Link className="quiet-button" to="/compare">
            <Scales size={17} />
            Compare experiments
          </Link>
        </div>
      )}
    </div>
  );
}
