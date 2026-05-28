import { useMemo } from 'react';

import { useSimulationStore } from '../store/simulationStore';

export function BlockchainStatusCards() {
  const latestStep = useSimulationStore((state) => state.latestStep);
  const episodeHistory = useSimulationStore((state) => state.episodeHistory);

  const throughputEstimate = useMemo(() => {
    if (!episodeHistory.length) return 0;
    const latest = episodeHistory[episodeHistory.length - 1];
    return latest.transactions_verified;
  }, [episodeHistory]);

  const cards = [
    {
      label: 'Confirmed Blocks',
      value: latestStep?.blockchain_length ?? 0,
      accent: 'accent-blue',
    },
    {
      label: 'Verified Transactions',
      value: latestStep?.transactions_verified ?? 0,
      accent: 'accent-green',
    },
    {
      label: 'Byzantine Detections',
      value: latestStep?.byzantine_detections ?? 0,
      accent: 'accent-red',
    },
    {
      label: 'Estimated Throughput',
      value: throughputEstimate,
      accent: 'accent-amber',
    },
  ];

  return (
    <section className="metric-card-grid">
      {cards.map((card) => (
        <article key={card.label} className="metric-card">
          <div className={`metric-card-glow ${card.accent}`} />
          <div className="metric-card-label">{card.label}</div>
          <div className="metric-card-value">{card.value}</div>
        </article>
      ))}
    </section>
  );
}
