import { X } from "@phosphor-icons/react";
import { useSimulationStore } from "../store/simulationStore";
export function NodeDetailPanel() {
  const id = useSimulationStore((s) => s.selectedNodeId);
  const trust = useSimulationStore((s) => s.trustScores);
  const mal = useSimulationStore((s) => s.isMalicious);
  const detected = useSimulationStore((s) => s.isDetected);
  const delegates = useSimulationStore((s) => s.delegateNodes);
  const select = useSimulationStore((s) => s.selectNode);
  if (!id) return null;
  return (
    <aside className="node-inspector" aria-label="Node details">
      <header>
        <h3>{id}</h3>
        <button
          className="text-button"
          onClick={() => select(null)}
          aria-label="Close node details"
        >
          <X size={18} />
        </button>
      </header>
      <div className="eyebrow">Reported trust</div>
      <div className="node-trust">{(trust[id] ?? 0).toFixed(3)}</div>
      <dl>
        {[
          ["Ground truth", mal[id] ? "Malicious" : "Honest"],
          ["Detection", detected[id] ? "Flagged" : "Not flagged"],
          [
            "Delegation",
            delegates.includes(id) ? "Active delegate" : "Participant",
          ],
        ].map(([l, v]) => (
          <div key={l}>
            <dt>{l}</dt>
            <dd>{v}</dd>
          </div>
        ))}
      </dl>
      <p>Values reflect the latest received simulation event.</p>
    </aside>
  );
}
