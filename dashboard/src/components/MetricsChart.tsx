import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { useSimulationStore } from '../store/simulationStore';

export function MetricsChart() {
  const episodeHistory = useSimulationStore((state) => state.episodeHistory);
  const data = episodeHistory.map((episode) => ({
    episode: episode.episode + 1,
    f1: Number(episode.f1_score.toFixed(4)),
    precision: Number(episode.precision.toFixed(4)),
    recall: Number(episode.recall.toFixed(4)),
    reward: Number((episode.reward / 100).toFixed(4)),
  }));

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <h3>Episode Metrics</h3>
          <p>Live episode-end trends for F1, precision, recall, and normalized reward.</p>
        </div>
      </div>
      <div className="chart-shell">
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={data}>
            <CartesianGrid stroke="#e3ddd0" strokeDasharray="3 3" />
            <XAxis dataKey="episode" stroke="#6e695e" />
            <YAxis stroke="#6e695e" domain={[0, 1.1]} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="f1" stroke="#1f3a5f" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="precision" stroke="#3d6b4b" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="recall" stroke="#9a6f1c" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="reward" stroke="#7d4f5e" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
