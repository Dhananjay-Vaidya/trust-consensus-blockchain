import { AttackTimeline } from '../components/AttackTimeline';
import { BlockchainStatusCards } from '../components/BlockchainStatusCards';
import { MetricsChart } from '../components/MetricsChart';
import { SimulationControls } from '../components/SimulationControls';
import { TrustDistributionChart } from '../components/TrustDistributionChart';
import { TrustNetworkGraph } from '../components/TrustNetworkGraph';
import { useSimulationStore } from '../store/simulationStore';

export function DashboardPage() {
  const episodeHistory = useSimulationStore((state) => state.episodeHistory);
  const latestStep = useSimulationStore((state) => state.latestStep);

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <div className="eyebrow">Real-time supervision</div>
          <h2>Live Simulation Dashboard</h2>
          <p>Monitor trust scores, delegate dynamics, blockchain growth, and attack impact while a run is executing.</p>
        </div>
        <div className="summary-banner">
          <div>
            <span className="summary-label">Latest F1</span>
            <strong>{latestStep ? latestStep.f1_score.toFixed(4) : '0.0000'}</strong>
          </div>
          <div>
            <span className="summary-label">Reward</span>
            <strong>{latestStep ? latestStep.reward.toFixed(2) : '0.00'}</strong>
          </div>
          <div>
            <span className="summary-label">Episodes Logged</span>
            <strong>{episodeHistory.length}</strong>
          </div>
        </div>
      </header>

      <SimulationControls />
      <BlockchainStatusCards />

      <div className="two-column-grid">
        <TrustNetworkGraph />
        <TrustDistributionChart />
      </div>

      <div className="two-column-grid">
        <MetricsChart />
        <AttackTimeline episodes={episodeHistory} />
      </div>
    </div>
  );
}
