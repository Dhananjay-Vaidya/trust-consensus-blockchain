# System and threat model

This replaces the previous text, which described an "FHE-protected ABAC" path that in fact decrypted,
compared in plaintext and re-encrypted (audit finding A5).

## Parties

| Party | Knows | Does |
|---|---|---|
| **Trust authority** | CKKS secret key; trust weights `w` of the committee (computed from audit evidence) | encrypts `w` each step |
| **Aggregator** | `Enc(w)`; the public, signed votes `v[t, i]` | evaluates the margins `m_t = sum_i w_i (v[t,i] - theta) / k` homomorphically (one ciphertext for all T transactions), optionally applies `s` iterations of the sign polynomial `p(x) = 1.5x - 0.5x^3` |
| **Decryptor** | secret key | decrypts one ciphertext per step and publishes `accept_t = [out_t > 0]` |
| **Auditor** | can re-verify a transaction (signature / rule check) | re-verifies a random `audit_rate` fraction after commit; results are public |
| **Delegates** | their own vote; public ledger | vote; honest ones misread validity with probability `honest_fault_rate` |
| **Adversary** | identities of its coalition; validity of transactions; the public ledger (votes, commits, audit results); in the plaintext condition also the weights | chooses coalition votes and timing (NMA, CRA, AAA, BFI, TDP) and, in E8, which honest nodes to bribe |

In this artefact **one process plays the trust authority, aggregator and decryptor with a single
key**. This is a simulation of the data flow, not a deployment. A real deployment needs threshold
or multiparty CKKS (e.g. OpenFHE's threshold CKKS) so that no single party can decrypt `Enc(w)`.
That is out of scope and is stated as a limitation in the paper.

## What each party learns (measured, not assumed)

* **Aggregator:** never sees `w` in the clear (it only multiplies the plaintext vote matrix by
  `Enc(w)` and evaluates a public polynomial).
* **Decryptor:** sees `out_t = p^(s)(m_t)` (`s = sign_iters`). The task brief said that with
  `s >= 1` the decryptor learns "approximately sign(m_t) outside a small band". **Our measurements
  contradict this for the parameters used.** `p` is strictly increasing on [-1, 1], typical margins are
  small (median |m| ~0.07–0.08), and three iterations do not saturate them. Inverting `p^(s)` recovers
  `m_t` to within 8e-6 at every `s` in {0, 1, 2, 3}, and at most 0.15% of outputs exceed |0.9|
  (`results/raw/e4_he/leakage.csv`). **The decryptor therefore learns the margins in every
  configuration we ran.** From margins over many steps it can, in principle, estimate the weights by
  regression on the public votes. Hiding margins would need a comparison circuit that saturates (more
  or steeper polynomial iterations with pre-scaling, or a different scheme), at higher cost.
* **Everyone:** the commit decisions and the votes are public by design. As E8 tests, an adversary
  can use them to rank delegates by influence without seeing any weight.

## CKKS parameters (128-bit security)

The polynomial modulus degree is the smallest `N` in {8192, 16384, 32768} whose total coefficient
modulus (`60 + 40 * (2s + 1) + 60` bits) is within the 128-bit-security bound used in TenSEAL/SEAL
(218, 438 and 881 bits respectively). `s = 0` needs 160 bits, so `N = 8192`; `s = 1, 2, 3` need
240, 320 and 400 bits, so `N = 16384`. Scale `2^40`. Exact values used per run:
`results/raw/e4_he/params.json`.

## Approximation and the guard band

CKKS is approximate. Decisions with |margin| below a guard band may differ from the plaintext rule.
We measured the band by placing margins at exactly `±delta`
(`experiments/exp_he_band.py`, `results/raw/e4_he/band.csv`): **no flips for |m| >= 1e-8; flips
only at |m| <= 1e-9** (including exact ties, |m| = 0, where plaintext accepts by convention).
An earlier run on the same machine put the boundary one decade higher (1e-7 / 1e-8); treat the band as
~1e-8 and machine/noise dependent.
Over 13,440 random-instance decisions there were 0 flips (`decisions.csv`).

## Trust and audit assumptions

* Trust is updated only from audit evidence: a committee member's vote on an audited transaction is
  *inconsistent* if it differs from the audited validity. Un-audited transactions give no evidence.
* Audits are assumed perfect (DECISIONS D16) and sampled uniformly at random, independently of the
  votes. An adversary that could predict which transactions will be audited could attack only the
  others; this is out of scope.
* Votes are signed, so a delegate cannot repudiate its vote.
* The safety proposition (`paper/proof.md`) bounds what a coalition of size `b` can commit given the
  per-delegate share cap `c/k`; it does not bound liveness attacks.

## Out of scope

Network-level attacks (eclipse, DoS), Sybil identity creation (the committee is drawn from a
permissioned node set), key management, side channels of the HE implementation, and collusion
between the decryptor and the adversary.
