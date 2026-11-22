# Literature search protocol and record

**Status: INCOMPLETE. The author must finish this before any novelty statement is final.**
The paper's novelty claims are worded "to the best of our knowledge, and per the search protocol in
docs/LITERATURE.md". That wording is only honest once the databases marked *not searched* below have
been searched and logged.

## Protocol

* **Topics (T1–T5).**
  T1 sleeper / on-off / trust-drift attacks on reputation or trust-weighted consensus;
  T2 encrypted weighted voting, homomorphic comparison, private tallying;
  T3 trust-weighted / reputation-weighted BFT and delegated consensus;
  T4 learned BFT protocol or parameter selection (e.g. BFTBrain);
  T5 dynamic trust models for blockchain IoT (incl. anything named "DynaTrust").
* **Databases:** arXiv, IEEE Xplore, ACM Digital Library, Scopus (plus IACR ePrint for T2).
* **Inclusion:** peer-reviewed or archived preprint, 2002–2026, English, proposes or evaluates a
  mechanism on one of T1–T5. **Exclusion:** blog posts, product pages, papers without a method.
* **Recording:** for each query, the date, database, exact query string, hit count, number screened
  by title/abstract, number included. Every included paper goes into `paper/refs.bib` only after its
  title, authors, venue, year and DOI/ID are checked against the publisher or archive page.

## Log of what was actually done (2026-11-22, by the coding assistant)

The assistant had a general web search engine and a page fetcher. It had **no access to IEEE Xplore,
ACM DL or Scopus search interfaces**, so it could not run database queries or report database hit
counts. What it ran:

| # | Date | Tool | Query | Outcome |
|---|---|---|---|---|
| 1 | 2026-11-22 | web search | `arXiv 2512.22860` | not indexed by the search engine; page fetched directly (row 11) |
| 2 | 2026-11-22 | web search | `Muniswamy Rathi 2025 Applied Artificial Intelligence ABAC trust delegated consensus blockchain IoT` | found Muniswamy & Rathi (2025), DOI 10.1080/08839514.2025.2459461 (catalogue record; full text not read) |
| 3 | 2026-11-22 | web search | `BFTBrain adaptive BFT consensus reinforcement learning NSDI 2025` | USENIX NSDI'25 page + arXiv 2408.06432 |
| 4 | 2026-11-22 | web search | `on-off attack trust management reputation system sleeper attack detection` | ~10 hits screened; Chae et al. TPDS 2015 included; WSN/IoT on-off papers (PMC4435207, arXiv 2508.17304, arXiv 2508.14028 survey, O2Trust, Future Internet 10(1):6) **screened but not verified, not cited** |
| 5 | 2026-11-22 | web search | `TenSEAL library homomorphic encryption tensors paper Benaissa 2021` | arXiv 2104.03152 |
| 6 | 2026-11-22 | web search | `DynaTrust dynamic trust blockchain` | **no paper named "DynaTrust" found.** Closest: "DYNAMIC-TRUST" (IEEE Xplore doc 10909344, vehicular ITS; not verified, not cited). The task brief's "DynaTrust" reference must be resolved by the author. |
| 7 | 2026-11-22 | web search | `Cheon Kim Kim Song "Homomorphic encryption for arithmetic of approximate numbers" ASIACRYPT 2017 DOI` | CKKS, DOI 10.1007/978-3-319-70694-8_15 |
| 8 | 2026-11-22 | web search | `Jøsang Ismail "The Beta Reputation System" Bled eCommerce 2002` | author-hosted PDF; no DOI |
| 9 | 2026-11-22 | web search | `Page 1954 "Continuous inspection schemes" Biometrika CUSUM DOI` | DOI 10.1093/biomet/41.1-2.100 |
| 10 | 2026-11-22 | web search | `Cheon Kim Kim "Efficient homomorphic comparison methods with optimal complexity" ASIACRYPT 2020` | DOI 10.1007/978-3-030-64834-3_8 |
| 11 | 2026-11-22 | page fetch | arxiv.org/abs/2512.22860, arxiv.org/abs/2408.06432, eprint.iacr.org/2022/915, digitalcommons.uri.edu/cs_facpubs/38 | author lists and identifiers confirmed (refs.bib) |
| 12 | 2026-11-22 | web search | `Castro Liskov "Practical Byzantine fault tolerance" OSDI 1999` | USENIX page, pp. 173–186 |
| 13 | 2026-11-22 | web search | `OpenFHE open-source fully homomorphic encryption library paper 2022 threshold CKKS` | ePrint 2022/915 (WAHC'22); threshold CKKS support stated in the repository README, not checked in the paper |

**Not searched (author TODO):** IEEE Xplore, ACM DL and Scopus for T1–T5, with logged hit counts;
arXiv listing search (cs.CR, cs.DC) for T1–T3 since 2022; IACR ePrint for "private weighted voting"
and "homomorphic tally reputation". Particular risks to novelty that a reviewer may raise and that
were NOT checked: (a) prior homomorphic or MPC-based *weighted* tallies in e-voting or federated
aggregation; (b) CUSUM / change-point detection already applied to reputation in P2P or WSN trust;
(c) influence caps in stake-weighted protocols (e.g. per-validator voting-power caps).

## Relation to the two prior works (what is and is not new)

* **Muniswamy & Rathi (Applied AI, 2025)**: base ABAC-TDCB-D3P protocol (attribute-based access
  control + trust-based delegated consensus + D3P agent). Only the catalogue record and abstract were
  seen; the paper must be read in full to state precisely which components we reuse.
* **Padia, Vaidya, Mangrulkar (arXiv:2512.22860, 2025)**: the authors' own preprint, which compares
  RL/DRL/MARL defences against five attack families and reports the TDP collapse (F1 0.11–0.16 after
  activation). **Its numbers come from the simulator audited in docs/AUDIT.md**, which gave trust
  updates, rewards and agent observations access to ground truth (A1), derived votes from trust (A2),
  and labelled a decrypt-compare-re-encrypt path as FHE (A5). The new paper must say this plainly.
  New relative to it: the oracle-free environment and its measured gap (E0), SleeperGuard, the exact
  share cap with the safety proposition, the HE tally with measured accuracy, cost and leakage, and the
  H3 test.
