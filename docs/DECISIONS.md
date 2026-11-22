# Design decisions

Each entry records a choice the task left open, the option taken, and why.  Entries are referenced
from code comments and from the paper as `D<n>`.

**D1 — Python version.** The target is Python 3.11 (Dockerfile, CI). The development machine has
Python 3.13.3 and all results in `results/raw/` were produced there; the machine spec is recorded in
every result file. Nothing in the code relies on 3.12+ features.

**D2 — Evidence granularity.** SleeperGuard's docstring speaks of "evidence per node per step". In
the environment a committee member can have several audited votes in one step (T=16 transactions,
audit rate 0.2 gives ~3.2). We feed **one Bernoulli observation per audited vote** rather than
collapsing them (collapsing with "any disagreement" inflates the honest error rate; collapsing with a
fraction is not Bernoulli). Consequence: `lam_fast`, `lam_slow`, `quarantine_steps` and
`probation_steps` count *audited observations of that node*, not wall-clock steps. CUSUM parameters
are calibrated for this granularity on CALIB_SEEDS (exp `calibrate_sg.py`).

**D3 — Where ground truth lives.** A simulator must hold ground truth somewhere. It is confined to
`src/env/world.py` (transaction validity, hidden behaviour types) and `src/env/attacks.py` (the
adversary, which like a real Byzantine delegate can check validity). The defended system
(`honest_env.py`, `src/trust`, `src/consensus`, `src/crypto`, `src/agents`) talks to the world only
through `new_transactions / cast_votes / audit / publish`, and labels are read only in
`src/metrics/`. Enforced by `tests/audit/test_no_ground_truth_access.py` (static) and
`tests/audit/test_a1_no_oracle.py` (runtime: the label accessor raises during stepping).

**D4 — Quarantined nodes stay eligible for the committee with weight 0.** The verified SleeperGuard
code counts down quarantine/probation only when the node is observed. Excluding quarantined nodes from
the committee would freeze them in quarantine forever. They are therefore not excluded by selection;
their weight is 0, they keep voting, and audits keep producing evidence about them.

**D5 — Detection metric.** A node is *flagged* at step t iff it is quarantined or its trust is below
`flag_threshold = 0.5`. The ground-truth positive label at step t is "adversary-controlled AND its
attack is active at t" (so a dormant sleeper is not a positive before `t_switch`). Precision, recall,
F1 and MCC are computed over all node-steps of the evaluation window: `[t_switch, end)` for TDP,
`[50, end)` for other attacks (50-step burn-in). We also report the end-of-run snapshot F1
(`final_f1`), which is the quantity closest to the preprint's per-episode F1.

**D6 — Coalition size.** `round(num_nodes * malicious_fraction)` adversary nodes, chosen with the
world RNG. Attack `none` has no adversary nodes. Default `malicious_fraction = 0.3125` (5 of 16).

**D7 — Simulated cost model.** Per step:
`latency_ms = 5 + 0.05 * k^2 + 2 * n_audited + he_ms` (PBFT-style quadratic messaging, a fixed
cost per audit, plus the *measured* HE time when `tally_backend = he`). Throughput = committed valid
transactions / summed simulated latency. These constants are illustrative, not measured on a network;
the paper says so. Wall-clock compute time per step is reported separately (`wall_ms_per_step`).

**D8 — Controller reward.** `r = audited_agreement - 0.1 * (k^2 / N^2) - 0.2 * audit_rate`, where
audited agreement is the fraction of audited transactions on which the commit decision matched the
audit. Every term is observable by the system. Controllers act every 10 steps on the mean reward.

**D9 — Infeasible share cap aborts the round.** `cap_shares` is left exactly as verified; when fewer
than `1/max_share` committee members have positive weight the cap cannot be met and the function returns
the weights unchanged. The TDCB tally therefore checks the cap and **aborts** (commits nothing) when it
is violated: safety is kept, liveness is lost, and the abort rate is reported.

**D10 — Action space.** 4 knobs x 3 levels = 81 discrete actions: committee fraction
{0.5, 0.75, 1.0}, audit rate {0.1, 0.2, 0.4}, selection temperature {0.05, 0.2, 1.0}, threshold
margin {0, +0.05, +0.1}. Every knob is used by `HonestEnv.step` (test A4).

**D11 — Legacy Beta backend.** The base protocol's Beta trust is kept with its update constants,
random initial trust and periodic decay, but (a) its RNG is injected (reproducible), and (b) its input
is audit evidence (consistent -> "valid", inconsistent -> "invalid") instead of ground truth.

**D12 — Baselines.** PBFT, static DPoS, majority and random-delegate baselines are presets of the same
environment (`src/agents/baselines.py`), with identical seeds, votes and audit budget. The previous
baseline classes generated their own votes and were removed.

**D13 — Old artefacts deleted.** Checkpoints, figures, tables and CSVs produced by the oracle simulator
are removed from the tree (still in git history). The untracked `experiments/checkpoints/` folder on the
author's disk was left alone.

**D14 — ABAC is out of the decision loop.** The old loop assigned ABAC attributes from ground truth
(malicious nodes got `user_role`). Admission control is orthogonal to the research questions; the ABAC
module is kept (minus the fake FHE path) but not wired into the environment.

**D15 — Weight normalisation before the tally.** The commit rule is invariant to scaling the weights, so
weights are divided by their maximum before both the plaintext and HE tallies (HETally clips to [0, 1]).

**D16 — Audits are perfect.** An audited transaction's validity is revealed exactly. This is the
optimistic end of the audit model and is stated as a limitation.

**D17 — Build tooling.** The development machine has no `make` and no LaTeX. `Makefile` targets call
`python scripts/reproduce.py`, which also runs directly. The paper was not compiled on the development
machine (see the final report); `make paper` needs `latexmk` + IEEEtran.

**D18 — Naming of the multi-agent controller.** It is "independent learners over a factored action
space" (one DQN per knob), not "MARL with attention".
