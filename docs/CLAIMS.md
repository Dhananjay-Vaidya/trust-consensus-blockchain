# Claims register

Every claim in `paper/main.tex` / `paper/results_section.tex`, the file that supports it, and an
honest strength rating. Numbers live in `paper/generated/numbers.tex` (macro → source file mapping in
`paper/generated/numbers_sources.json`).

Strength: **strong** = large effect, 30 paired seeds, Holm-significant, robust across the grid;
**moderate** = holds but narrower conditions or caveats; **weak** = suggestive, design-limited, or
depends on modelling choices a reviewer can reasonably reject.

| # | Claim | Evidence | Strength | Caveat |
|---|---|---|---|---|
| C1 | The pre-audit simulator's oracle feedback inflates detection F1 (legacy TDP 0.00 → 0.76; NMA/BFI similar) | `results/raw/e0_oracle_gap/runs.csv`, `results/raw/stats/e0_oracle_gap.csv` | strong | Only the trust-feedback part of the oracle is re-inserted; the old reward/observation leaks are not separately measured |
| C2 | The old code had oracle leakage, trust-derived votes, fake FHE, dead knobs, non-reproducible hashing | `docs/AUDIT.md`, `tests/audit/` | strong | Line numbers refer to commit c8bab2f |
| C3 | Without the oracle, legacy Beta trust never flags sleepers within the 300-step window, at all fault rates | `results/raw/e1_tdp_collapse/runs.csv` | strong | Depends on window length and on t_switch=300 giving sleepers a long trust build-up; E2 shows legacy reaches F1 up to 0.74 with an earlier switch |
| C4 | SleeperGuard improves detection over legacy Beta in every E2 cell (30/30 Holm-significant) | `results/raw/e2_sleeperguard/runs.csv`, `results/raw/stats/e2_sleeperguard.csv` | strong | Against stealthy sleepers (25% lie rate) F1 is only ~0.42–0.5 |
| C5 | CUSUM is the component that matters; two-timescale memory and the cap barely affect detection | `results/raw/e3_ablation/runs.csv`, `results/raw/stats/e3_ablation.csv` | strong | Single default configuration of the other components |
| C7 | HETally matches the plaintext rule on all random-instance decisions; disagreements only for \|margin\| ≤ ~1e-9 (≤1e-8 in an earlier run) | `results/raw/e4_he/decisions.csv`, `band.csv` | strong | One machine, TenSEAL 0.3.16, scale 2^40 |
| C8 | HE tally latency and size (per k, T, sign iterations) | `results/raw/e4_he/timings.csv`, `params.json`, `meta.json` | moderate | Single CPU, single process; no network; two runs on the same laptop differed by 35-55% in latency, so timings are indicative only |
| C9 | The decryptor recovers margins to within 8e-6 for every sign_iters tested; sign iterations buy no privacy here | `results/raw/e4_he/leakage.csv` | strong | Holds for the margin magnitudes this environment produces; steeper/pre-scaled comparison circuits were not tried |
| C10 | Simulation scales to 1024 nodes cheaply, but detection with a fixed small committee degrades sharply (most sleepers never flagged at 1024 nodes) | `results/raw/e5_scale/runs.csv` | moderate | 10 seeds; throughput/latency are cost-model values, not measurements |
| C11 | Detection degrades gracefully with audit rate | `results/raw/e6_audit_budget/runs.csv`, `results/raw/stats/e6_audit_budget.csv` | moderate | Audits assumed perfect and unpredictable |
| C12 | False-quarantine cost grows with honest fault rate and with CUSUM misspecification | `results/raw/e7_false_positives/runs.csv` | moderate | Fault rates 0.15/0.20 use the 0.10 calibration (outside the calibration grid) |
| C13 | NEGATIVE RESULT, not a contribution: hiding weights did not hinder bribery; ledger votes leak influence | `results/raw/e8_privacy/runs.csv`, `results/raw/stats/e8_privacy.csv` | moderate | "Encrypted" condition simulated by withholding weights from the briber (D19); one briber heuristic; bribery damage is mostly liveness |
| C14 | Factored independent learners and tabular Q beat the tuned rule on the observable reward; D3P does not | `results/raw/e9_learning/runs.csv`, `results/raw/stats/e9_learning.csv` | weak | Reward does not price detection; the top learner has much worse detection delay; static DPoS scores high reward while detecting nothing. Do not present as "learning improves security" |
| C15 | Capped-influence safety proposition (b·c/k ≥ θ needed to force an invalid commit) | `paper/proof.md` | strong (proof) | Assumes honest rejection, weights fixed before votes, enforced cap or abort |
| C16 | No violation of the bound in the adversarial search; bound tight on the grid | `results/raw/e10_safety/search.csv` | moderate | Heuristic search, not exhaustive |
| C17 | The provided iterative `cap_shares` can exceed the cap by up to ~2x; safety then relies on the tally's abort | `tests/test_capping.py`, `results/raw/e10_safety/search.csv` | strong | Measured on random heavy-tailed weight vectors |
| C18 | No invalid commit in the full environment for coalitions up to 8 of 16 with zero honest faults | `results/raw/e10_safety/env.csv` | moderate | CRA colluders are quarantined quickly; says nothing about adversaries that keep high trust |

## Claims that must NOT appear in the paper

* Any "first" / "no one has done" claim (literature search incomplete: `docs/LITERATURE.md`).
* That the HE tally hides margins or weights from the decryptor (contradicted by C9).
* That learning controllers improve security (C14 caveat).
* Any number from the preprint arXiv:2512.22860 as a result of this system (produced by the audited simulator).
