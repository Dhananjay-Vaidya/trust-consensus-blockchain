import type { EpisodeSummary } from '../types';

interface AttackTimelineProps {
  episodes: EpisodeSummary[];
}

function rewardTone(reward: number): string {
  if (reward > 80) return 'timeline-good';
  if (reward > 40) return 'timeline-mid';
  return 'timeline-bad';
}

export function AttackTimeline({ episodes }: AttackTimelineProps) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <h3>Attack Timeline</h3>
          <p>Episode-by-episode outcome trace with reward shading.</p>
        </div>
      </div>
      <div className="timeline-list">
        {episodes.length === 0 && <div className="empty-state">No completed episodes yet.</div>}
        {episodes.map((episode) => (
          <article key={episode.episode} className={`timeline-item ${rewardTone(episode.reward)}`}>
            <div className="timeline-episode">EP {episode.episode + 1}</div>
            <div className="timeline-metrics">
              <span>F1 {episode.f1_score.toFixed(3)}</span>
              <span>P {episode.precision.toFixed(3)}</span>
              <span>R {episode.recall.toFixed(3)}</span>
              <span>Reward {episode.reward.toFixed(1)}</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
