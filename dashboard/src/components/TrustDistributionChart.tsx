import { useMemo } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { useSimulationStore } from '../store/simulationStore';

export function TrustDistributionChart() {
  const trustScores = useSimulationStore((state) => state.trustScores);

  const histogram = useMemo(() => {
    const bins = Array.from({ length: 10 }, (_, index) => ({
      label: `${(index / 10).toFixed(1)}-${((index + 1) / 10).toFixed(1)}`,
      count: 0,
      threshold: 0.45,
    }));
    for (const value of Object.values(trustScores)) {
      const index = Math.min(9, Math.max(0, Math.floor(value * 10)));
      bins[index].count += 1;
    }
    return bins;
  }, [trustScores]);

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <h3>Trust Distribution</h3>
          <p>Current trust-score histogram with the detection threshold marker.</p>
        </div>
      </div>
      <div className="chart-shell">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={histogram}>
            <CartesianGrid stroke="#243146" strokeDasharray="3 3" />
            <XAxis dataKey="label" stroke="#7f8ea3" />
            <YAxis stroke="#7f8ea3" allowDecimals={false} />
            <Tooltip />
            <ReferenceLine x="0.4-0.5" stroke="#ef4444" strokeDasharray="4 4" />
            <Bar dataKey="count" fill="#5cc7ff" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
