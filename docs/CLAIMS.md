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
| C3 | Without the oracle, legacy Beta trust never flags sleepers within the 300-step window, at all fault rates (over a 2500-step window it catches them after ~20 episodes: C24) | `results/raw/e1_tdp_collapse/runs.csv` | strong | Depends on window length and on t_switch=300 giving sleepers a long trust build-up; E2 shows legacy reaches F1 up to 0.74 with an earlier switch |
| C4 | SleeperGuard improves detection over legacy Beta in every E2 cell (30/30 Holm-significant) | `results/raw/e2_sleeperguard/runs.csv`, `results/raw/stats/e2_sleeperguard.csv` | strong | Against stealthy sleepers (25% lie rate) F1 is only ~0.42–0.5 |
| C5 | CUSUM is the component that matters; two-timescale memory and the cap barely affect detection | `results/raw/e3_ablation/runs.csv`, `results/raw/stats/e3_ablation.csv` | strong | Single default configuration of the other components |
| C7 | HETally matches the plaintext rule on all random-instance decisions; disagreements only for \|margin\| ≤ ~1e-9 (≤1e-8 in an earlier run) | `results/raw/e4_he/decisions.csv`, `band.csv` | strong | One machine, TenSEAL 0.3.16, scale 2^40 |
| C8 | HE tally latency and size (per k, T, sign iterations) | `results/raw/e4_he/timings.csv`, `params.json`, `meta.json` | moderate | Single CPU, single process; no network; two runs on the same laptop differed by 35-55% in latency, so timings are indicative only |
| C9 | The decryptor recovers margins to within 8e-6 for every sign_iters tested; sign iterations buy no privacy here | `results/raw/e4_he/leakage.csv` | strong | Holds for the margin magnitudes this environment produces; steeper/pre-scaled comparison circuits were not tried |
| C10 | Simulation scales to 1024 nodes cheaply, but detection with a fixed small committee degrades sharply (most sleepers never flagged at 1024 nodes) | `results/raw/e5_scale/runs.csv` | moderate | 10 seeds; throughput/latency are cost-model values, not measurements |
| C11 | Detection degrades gracefully with audit rate | `results/raw/e6_audit_budget/runs.csv`, `results/raw/stats/e6_audit_budget.csv` | moderate | Audits assumed perfect and unpredictable |
| C12 | False-quarantine cost grows with honest fault rate and with CUSUM misspecification | `results/raw/e7_false_positives/runs.csv` | moderate | Fault rates 0.15/0.20 use the 0.10 calibration (outside the calibration grid) |
| C13 | NEGATIVE RESULT, not a contribution: hiding weights did not hinder bribery; ledger votes leak influence | `results/raw/e8_privacy/runs.csv`, `results/raw/stats/e8_privacy.csv` | moderate | "Encrypted" condition simulated by withholding weights from the briber (D19); one briber heuristic; bribery damage is mostly liveness |
| C14 | All three learners beat the tuned rule on the observable reward after Holm correction: tabular Q and factored MARL by large margins (median diff 0.047 and 0.066, Cliff's delta 0.665 and 0.921), D3P only by a small margin (median diff 0.014, Cliff's delta 0.297) | `results/raw/e9_learning/runs.csv`, `results/raw/stats/e9_learning.csv` | weak | Reward does not price detection; the top learner has much worse detection delay; static DPoS scores high reward while detecting nothing. Do not present as "learning improves security" |
| C15 | Capped-influence safety proposition (b·c/k ≥ θ needed to force an invalid commit) | `paper/proof.md` | strong (proof) | Assumes honest rejection, weights fixed before votes, enforced cap or abort |
| C16 | No violation of the bound in the adversarial search; bound tight on the grid | `results/raw/e10_safety/search.csv` | moderate | Heuristic search, not exhaustive |
| C17 | The provided iterative `cap_shares` can exceed the cap by up to ~2x; safety then relies on the tally's abort | `tests/test_capping.py`, `results/raw/e10_safety/search.csv` | strong | Measured on random heavy-tailed weight vectors |
| C18 | No invalid commit in the full environment for coalitions up to 8 of 16 with zero honest faults | `results/raw/e10_safety/env.csv` | moderate | CRA colluders are quarantined quickly; says nothing about adversaries that keep high trust |

| C19 | Against the adaptive coalition (exact cap), no invalid commit for coalitions below the bound: 0/450 runs without and 0/450 with honest faults; above the bound 89/540 runs breach, all with honest faults | `results/raw/e10_safety/env.csv` | strong | 30 seeds x 3 lie rates; k=16, c=2, θ=0.667 only |
| C20 | A damage-maximising coalition chosen by search (always b=8, above the bound) evades detection: SleeperGuard median F1 0.24, legacy 0.00; invalid-commit rate 0.0007 vs 0.0023 | `results/raw/e11_adaptive/` | moderate | Attacker search on seeds 30-39 over a fixed grid; damage rates are small in absolute terms |
| C21 | SleeperGuard detection rises with lie rate (F1 0.07 at 5% to 1.00 at 100%; ≥0.5 from 40%); honest false quarantines stay ≤0.30/1000 | `results/raw/e12_lierate/runs.csv` | strong | One coalition size (5/16), one fault rate (0.05) |

| C22 | SleeperGuard cuts the median sleeper-detection delay from 252 steps (legacy Beta) to 2.0 steps (E2, pooled over all 30 grid cells). NOTE: an earlier request quoted this as "24 -> 2 steps"; the data say 252 -> 2.0 | `results/raw/e2_sleeperguard/runs.csv` (macros `EtwoLgDelayMed`, `EtwoSgDelayMed`) | strong | Legacy delays are mostly right-censored (sleepers never flagged within the window), so 252 is a lower bound set by window length; pooled over intensities 0.25 and 1.0, so the stealthy-sleeper delay is longer than the pooled median |
| C23 | Honest false quarantines per 1000 node-steps with CUSUM calibrated to the true fault rate: 0.36 at f=0.02, 0.31 at f=0.05, 0.62 at f=0.10 (E7, no attack) | `results/raw/e7_false_positives/runs.csv` (macros `EsevenFqTwo`, `EsevenFqFive`, `EsevenFqTen`) | moderate | Assumes the operator knows the nominal fault rate; misspecified calibration is much worse (8.07/1000 at true f=0.20 with the 0.05 calibration); calibrated on seeds 20-29 only |
| C24 | Under the preprint's protocol as its code actually ran (E13b: 4 of 16 adversaries, 100 x 100-step episodes, activation after episode 25, intensity 0.75, flag if trust < 0.45, static labels, F1 of the final episode), legacy Beta reaches F1 1.00 on the oracle-free environment. This is NOT inside the preprint's reported 0.11-0.16. Legacy first detects the sleepers at episode 53 (median), SleeperGuard at episode 26. Across 24 plausible readings of the protocol, legacy median F1 ranges from 0.00 to 1.00; only 2 cells (50 episodes, threshold 0.5, all active episodes, which was our earlier E13a reading, F1 0.16) fall inside 0.11-0.16. SleeperGuard is at least 0.99 in every cell | `results/raw/e13_preprint_protocol/{runs,grid,episodes}.csv`, `docs/DECISIONS.md` D23 | moderate (robust finding: detection lag 53 vs 26 episodes); weak for any single-number F1 comparison | The earlier statement that the preprint's 0.16 'survives without the oracle' was an artefact of a 50-episode, all-active-episodes window and is withdrawn. Protocol facts come from code at c8bab2f where the paper text differs (5 vs 4 adversaries, final-10 vs final-episode averaging); one honest fault rate (0.05) only |

## Claims that must NOT appear in the paper

* Any "first" / "no one has done" claim (literature search incomplete: `docs/LITERATURE.md`).
* That the HE tally hides margins or weights from the decryptor (contradicted by C9).
* That learning controllers improve security (C14 caveat).
* That SleeperGuard detects adaptive or low-rate attackers (contradicted by C20, C21); safety against them comes from the cap bound (C19).
* Any number from the preprint arXiv:2512.22860 as a result of this system (produced by the audited simulator).
