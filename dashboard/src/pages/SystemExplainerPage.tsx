import { useState } from "react";
import {
  Key,
  Graph,
  Scales,
  Cube,
  Brain,
  LockKey,
} from "@phosphor-icons/react";
const stages = [
  {
    id: "abac",
    icon: Key,
    name: "Authorize",
    subtitle: "Attribute-based access",
    title: "Attribute-based access control",
    description:
      "Incoming transactions are filtered using sender attributes and trust-aware policies. The engine assigns roles to simulated nodes and evaluates write requests before consensus.",
    equation:
      "Transaction request + node attributes + trust -> access decision",
    input: "Node roles, security clearance, request context, and trust score",
    output: "Allowed transactions proceed to the consensus stage.",
    source: "src/abac/abac.py",
  },
  {
    id: "trust",
    icon: Graph,
    name: "Estimate trust",
    subtitle: "Bayesian evidence",
    title: "Bayesian node trust",
    description:
      "The trust manager maintains evidence about each node and updates its trust state as the network runs. Trust influences delegate selection and changes following observed behavior.",
    equation: "Expected trust = alpha / (alpha + beta)",
    input:
      "Interaction evidence, malicious behavior, and configured trust updates",
    output: "Node trust scores and candidate delegates.",
    source: "src/trust/trust.py",
  },
  {
    id: "consensus",
    icon: Scales,
    name: "Reach consensus",
    subtitle: "Trust-driven delegation",
    title: "Trust-driven delegated consensus",
    description:
      "The simulation selects delegates using trust-based sampling by default, with an optional UCB strategy in the CLI. Delegates participate in transaction verification; consensus outcomes feed back into trust updates.",
    equation:
      "Trust evidence -> delegate selection -> verification -> trust update",
    input: "Authorized transactions and selected delegate nodes",
    output: "Verification outcomes and Byzantine detection signals.",
    source: "src/consensus/tdcb.py",
  },
  {
    id: "chain",
    icon: Cube,
    name: "Record blocks",
    subtitle: "Local blockchain model",
    title: "Blockchain and transaction records",
    description:
      "Verified transactions are added to a local blockchain model. Mining is attempted at configured intervals, and chain length and block transaction counts are recorded as experiment metrics.",
    equation:
      "Block hash = hash(previous hash, transactions, nonce, timestamp)",
    input:
      "Verified transactions, pending transaction pool, and previous block",
    output: "Blocks, chain length, and last-block transaction counts.",
    source: "src/blockchain/blockchain.py",
  },
  {
    id: "learning",
    icon: Brain,
    name: "Adapt policy",
    subtitle: "RL / DRL / MARL",
    title: "Adaptive learning agents",
    description:
      "The agent observes a state vector of trust and chain metrics and selects an action. The default action space combines changes to delegation ratio, trust decay, and the consensus threshold.",
    equation: "16 state features -> agent -> 27 action combinations -> reward",
    input: "Trust statistics, chain metrics, and reward feedback",
    output: "Adjusted delegation and consensus parameters.",
    source: "src/agents/ and src/rewards/reward.py",
  },
  {
    id: "encryption",
    icon: LockKey,
    name: "Evaluate privacy",
    subtitle: "Homomorphic tally",
    title: "HETally: trust-weighted vote tally under CKKS",
    description:
      "The trust authority encrypts the committee weights; the aggregator multiplies the public votes by Enc(w) and never sees the weights; the decryptor decodes one value per transaction. One process plays all three roles with one key (a real deployment needs threshold CKKS). Measured: decisions match plaintext for |margin| >= 1e-7, but the decryptor can recover the margins.",
    equation: "accept_t <=> sum_i w_i (v[t,i] - theta) / k >= 0",
    input: "Enc(trust weights) and public signed votes",
    output: "Commit decisions, HE latency and flip count.",
    source: "src/crypto/he_tally.py",
  },
];
export function SystemExplainerPage() {
  const [active, setActive] = useState("trust");
  const model = stages.find((s) => s.id === active)!;
  return (
    <div className="architecture-workspace">
      <div className="research-callout">
        <p>
          Votes come from a noisy vote model; trust learns only from randomly
          audited transactions; the tally can run in plaintext or under CKKS
          encryption. Select a stage to read its role and source file.
        </p>
      </div>
      <div className="pipeline" role="group" aria-label="Simulation components">
        {stages.map((s) => (
          <button
            className={`pipeline-stage ${s.id === active ? "selected" : ""}`}
            aria-pressed={s.id === active}
            onClick={() => setActive(s.id)}
            key={s.id}
          >
            <s.icon size={24} />
            <strong>{s.name}</strong>
            <small>{s.subtitle}</small>
          </button>
        ))}
      </div>
      <section className="data-panel architecture-detail">
        <div>
          <div className="eyebrow">Model component</div>
          <h2>{model.title}</h2>
          <p>{model.description}</p>
          <div className="model-equation">{model.equation}</div>
        </div>
        <dl>
          <div>
            <dt>Inputs</dt>
            <dd>{model.input}</dd>
          </div>
          <div>
            <dt>Outputs</dt>
            <dd>{model.output}</dd>
          </div>
          <div>
            <dt>Implementation</dt>
            <dd>
              <code>{model.source}</code>
            </dd>
          </div>
        </dl>
      </section>
      <section className="data-panel architecture-detail">
        <div>
          <h2>One experiment, episode by episode</h2>
          <p>
            Each episode generates transactions, applies authorization and
            attack behavior, selects delegates, verifies transactions, updates
            trust, computes rewards, and trains the selected agent.
          </p>
        </div>
        <dl>
          <div>
            <dt>Detection measurements</dt>
            <dd>
              F1, precision, recall, and trust separation are reported by
              simulation events.
            </dd>
          </div>
          <div>
            <dt>Recorded artifacts</dt>
            <dd>
              Episode CSVs, replayable event logs, plots, and model checkpoints
              are written under experiments/.
            </dd>
          </div>
          <div>
            <dt>Research interpretation</dt>
            <dd>
              Use matched configurations and multiple random seeds when
              comparing agents or consensus protocols.
            </dd>
          </div>
        </dl>
      </section>
    </div>
  );
}
