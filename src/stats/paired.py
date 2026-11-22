"""Paired per-seed statistics: Wilcoxon signed-rank, Holm correction, bootstrap CIs, Cliff's delta."""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Dict, List, Sequence, Tuple

import numpy as np
from scipy.stats import wilcoxon

N_BOOT = 10_000


def bootstrap_ci(x: Sequence[float], stat=np.median, n_boot: int = N_BOOT, alpha: float = 0.05,
                 seed: int = 12345) -> Tuple[float, float]:
    """Percentile bootstrap CI of ``stat`` (default median)."""
    a = np.asarray([v for v in x if not (isinstance(v, float) and math.isnan(v))], dtype=float)
    if a.size == 0:
        return (math.nan, math.nan)
    if np.all(a == a[0]):
        return (float(a[0]), float(a[0]))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, a.size, size=(n_boot, a.size))
    boots = stat(a[idx], axis=1)
    return (float(np.quantile(boots, alpha / 2)), float(np.quantile(boots, 1 - alpha / 2)))


def cliffs_delta(x: Sequence[float], y: Sequence[float]) -> float:
    """P(X > Y) - P(X < Y); |d| < 0.147 negligible, < 0.33 small, < 0.474 medium, else large."""
    a, b = np.asarray(x, float), np.asarray(y, float)
    if a.size == 0 or b.size == 0:
        return math.nan
    gt = (a[:, None] > b[None, :]).sum()
    lt = (a[:, None] < b[None, :]).sum()
    return float((gt - lt) / (a.size * b.size))


def magnitude(d: float) -> str:
    if math.isnan(d):
        return "n/a"
    d = abs(d)
    return "negligible" if d < 0.147 else "small" if d < 0.33 else "medium" if d < 0.474 else "large"


@dataclass
class PairedResult:
    metric: str
    a: str
    b: str
    n: int
    median_a: float
    median_b: float
    ci_a: Tuple[float, float]
    ci_b: Tuple[float, float]
    median_diff: float
    ci_diff: Tuple[float, float]
    p_value: float
    p_holm: float = math.nan
    cliffs_delta: float = math.nan
    effect: str = ""
    significant: bool = False

    def row(self) -> Dict[str, object]:
        d = asdict(self)
        d["ci_a"] = f"[{self.ci_a[0]:.4g}, {self.ci_a[1]:.4g}]"
        d["ci_b"] = f"[{self.ci_b[0]:.4g}, {self.ci_b[1]:.4g}]"
        d["ci_diff"] = f"[{self.ci_diff[0]:.4g}, {self.ci_diff[1]:.4g}]"
        return d


def paired_compare(metric: str, a_name: str, a: Sequence[float], b_name: str, b: Sequence[float]) -> PairedResult:
    """a and b are per-seed values in the same seed order (paired design)."""
    x, y = np.asarray(a, float), np.asarray(b, float)
    ok = ~(np.isnan(x) | np.isnan(y))
    x, y = x[ok], y[ok]
    diff = x - y
    if diff.size == 0 or np.all(diff == 0):
        p = 1.0
    else:
        p = float(wilcoxon(x, y, zero_method="wilcox", alternative="two-sided").pvalue)
    d = cliffs_delta(x, y)
    return PairedResult(metric, a_name, b_name, int(diff.size),
                        float(np.median(x)) if x.size else math.nan, float(np.median(y)) if y.size else math.nan,
                        bootstrap_ci(x), bootstrap_ci(y), float(np.median(diff)) if diff.size else math.nan,
                        bootstrap_ci(diff), p, cliffs_delta=d, effect=magnitude(d))


def holm(results: List[PairedResult], alpha: float = 0.05) -> List[PairedResult]:
    """Holm-Bonferroni step-down over one family; sets p_holm and significant."""
    m = len(results)
    order = sorted(range(m), key=lambda i: results[i].p_value)
    running = 0.0
    for rank, i in enumerate(order):
        adj = min(1.0, (m - rank) * results[i].p_value)
        running = max(running, adj)
        results[i].p_holm = running
        results[i].significant = running < alpha
    return results
