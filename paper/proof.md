# Capped-influence safety proposition

## Setting

A committee of `k` delegates decides each transaction by the trust-weighted rule

    commit  <=>  A := sum_{i : v_i = 1} w_i  >=  theta * W,      W := sum_i w_i,  theta in (0, 1].

Weights are non-negative and produced by the trust backend from audit evidence only; delegates cannot
write their own weight (they influence it only through their votes, which are audited).

**Cap.** Let `s_i := w_i / W` be delegate `i`'s share. SleeperGuard applies water-filling with
`max_share = c / k` (`c >= 1`). The TDCB tally then checks `max_i s_i <= c/k` and **aborts the round
(commits nothing) if the check fails** (DECISIONS D9). Hence for every round that commits anything,

    (Cap)    s_i <= c / k   for all i.

## Assumptions

* **A1 (honest rejection).** On the invalid transaction considered, every honest committee member votes
  reject (`v_i = 0`). (Honest faults are treated separately below.)
* **A2 (coalition).** At most `b` committee members are adversarial; they may vote arbitrarily and
  in coordination. They may also have the largest weights the backend can produce.
* **A3 (weights are fixed before votes are counted).** The weight vector used in the tally is computed
  before the round's votes are revealed and does not depend on them.
* **A4 (enforced cap).** Either (Cap) holds or the round aborts. This is a property of the code path
  `cap_shares -> TDCB.tally(max_share=c/k)`, not of the weights; it covers the cases where water-filling
  is infeasible (fewer than `k/c` members with positive weight) or did not converge within its
  iteration limit.

## Proposition

Under A1–A4, an invalid transaction can be committed only if `b * c / k >= theta`. Equivalently the
committee is safe against every coalition of size `b < theta * k / c`.

*Proof.* Suppose the round commits the invalid transaction. By A4, (Cap) holds. By A1 only adversarial
members approve, so `A = sum_{i in B} w_i` with `|B| <= b`. Dividing by `W > 0`,

    A / W = sum_{i in B} s_i <= |B| * c / k <= b * c / k.

Commit requires `A / W >= theta`, hence `b c / k >= theta`. ∎

*Example.* `k = 16, c = 2, theta = 0.667`: `theta k / c = 5.336`, so any coalition of `b <= 5` is safe.

## Tightness

The bound is attained when the `b` adversarial members each hold exactly the capped share `c/k`
and honest members share the rest. Water-filling produces this when the adversaries' raw weights are
large and honest weights are small but positive. E10 searches for such vectors.

## With honest faults

If some honest members also (mistakenly) approve, with total share `phi`, then commit requires
`b c / k + phi >= theta`. Since each honest share is also at most `c/k`, `f` faulty honest approvals
contribute `phi <= f c / k`, so safety needs `(b + f) c / k < theta`. With independent faults at rate
`p`, `f ~ Binomial(k - b, p)`, so the per-transaction failure probability is bounded by
`P[f >= ceil(theta k / c) - b]`. This term is not zero, and the paper reports the empirical
invalid-commit rate alongside the bound.

## What the proposition does NOT say

* It says nothing about **liveness**. A coalition with share `> 1 - theta` can block valid transactions,
  and an infeasible cap aborts rounds.
* A3 matters: if an adversary could change weights after seeing votes, the argument fails. In the
  implementation, weights for step `t` are computed from evidence up to step `t-1`.
* It does not bound the damage of *wrong* weights: if honest members are quarantined (weight 0), fewer
  than `k/c` positive weights make the cap infeasible, and the protocol aborts rather than commits.
* It assumes audits and signatures are sound (DECISIONS D16).

## Empirical check (E10)

`experiments/exp_e10_safety.py` (a) searches weight vectors (structured extremes, random restarts,
hill-climbing) for `k in {8,16,32}`, `c in {1.5,2,3}`, `theta in {0.5,0.667,0.8}`, `b = 1..k`, through the
real `cap_shares -> TDCB.tally` path, and records any commit with `b c / k < theta` as a violation;
(b) runs the full environment with zero honest faults and a coalition of size `b = 1..8` (k = 16) that
approves every invalid transaction. Results: `results/raw/e10_safety/` and Table `tab:e10`.
