"""Generate every number, table and figure used in the paper from results/raw/ ONLY.

Outputs:
  paper/generated/numbers.tex   \\newcommand macros for every number quoted in the text
  paper/generated/tab_*.tex     LaTeX tables
  paper/figs/*.pdf              vector figures (Okabe-Ito colour-blind-safe palette)
  results/raw/stats/*.csv       paired tests (Wilcoxon, Holm, bootstrap CI, Cliff's delta)
Run: python paper/make_assets.py [--raw results/raw]
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Dict, List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.stats.paired import PairedResult, bootstrap_ci, holm, paired_compare  # noqa: E402

GEN = ROOT / "paper" / "generated"
FIGS = ROOT / "paper" / "figs"
OKABE = ["#000000", "#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7"]
plt.rcParams.update({"font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "legend.fontsize": 7,
                     "xtick.labelsize": 7, "ytick.labelsize": 7, "figure.dpi": 150,
                     "axes.prop_cycle": matplotlib.cycler(color=OKABE[1:] + OKABE[:1]),
                     "pdf.fonttype": 42})

NUM: Dict[str, str] = {}
SOURCES: Dict[str, str] = {}


def macro(name: str, value: float | int | str, src: str, fmt: str = "{:.2f}") -> None:
    """Register \\name -> value; name must be letters only (LaTeX)."""
    assert re.fullmatch(r"[A-Za-z]+", name), name
    if isinstance(value, str):
        s = value
    elif isinstance(value, (int, np.integer)):
        s = str(int(value))
    elif value is None or (isinstance(value, float) and math.isnan(value)):
        s = "n/a"
    else:
        s = fmt.format(value)
    NUM[name] = s
    SOURCES[name] = src


def med_ci(x) -> str:
    x = pd.Series(x).dropna()
    if x.empty:
        return "n/a"
    lo, hi = bootstrap_ci(x.values)
    return f"{np.median(x):.3f} [{lo:.3f}, {hi:.3f}]"


def save_stats(name: str, res: List[PairedResult]) -> pd.DataFrame:
    holm(res)
    df = pd.DataFrame([r.row() for r in res])
    (RAW / "stats").mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW / "stats" / f"{name}.csv", index=False)
    return df


def tex_table(df: pd.DataFrame, path: Path, caption: str, label: str, colfmt: str | None = None) -> None:
    body = df.to_latex(index=False, escape=True, column_format=colfmt or "l" * len(df.columns))
    path.write_text("\\begin{table}[t]\n\\centering\\scriptsize\n\\caption{" + caption + "}\\label{" + label + "}\n"
                    + "\\resizebox{\\columnwidth}{!}{%\n" + body + "}\n\\end{table}\n", encoding="utf-8")


def load(exp: str, name: str = "runs.csv") -> pd.DataFrame | None:
    p = RAW / exp / name
    return pd.read_csv(p) if p.exists() else None


def paired_on_seed(df: pd.DataFrame, key: str, a, b, metric: str):
    x = df[df[key] == a].set_index("seed")[metric]
    y = df[df[key] == b].set_index("seed")[metric]
    idx = x.index.intersection(y.index)
    return x.loc[idx].values, y.loc[idx].values


# ===========================================================================================
def e0() -> None:
    df = load("e0_oracle_gap")
    if df is None:
        return
    res, rows = [], []
    for atk in ["tdp", "cra", "aaa", "nma", "bfi"]:
        g = df[df.attack == atk]
        x, y = paired_on_seed(g, "oracle", True, False, "det_f1")
        res.append(paired_compare(f"det_f1[{atk}]", "oracle", x, "no_oracle", y))
        rows.append({"attack": atk.upper(), "F1 with oracle": med_ci(x), "F1 oracle-free": med_ci(y)})
        macro(f"EzeroOracle{atk.capitalize()}", float(np.median(x)), "results/raw/e0_oracle_gap/runs.csv")
        macro(f"EzeroHonest{atk.capitalize()}", float(np.median(y)), "results/raw/e0_oracle_gap/runs.csv")
    st = save_stats("e0_oracle_gap", res)
    for r, s in zip(rows, st.itertuples()):
        r["Holm p"] = f"{s.p_holm:.2g}"
        r["Cliff's d"] = f"{s.cliffs_delta:+.2f}"
    tex_table(pd.DataFrame(rows), GEN / "tab_e0.tex",
              "E0: node-detection F1 (median [95\\% bootstrap CI], 30 eval seeds) of legacy Beta trust with and "
              "without the pre-audit oracle feedback. Paired Wilcoxon, Holm-corrected.", "tab:e0")


def e1() -> None:
    df = load("e1_tdp_collapse")
    if df is None:
        return
    rows, res = [], []
    for f in sorted(df.fault.unique()):
        g = df[df.fault == f]
        x, y = paired_on_seed(g, "attack", "cra", "tdp", "det_f1")
        res.append(paired_compare(f"det_f1[f={f}]", "cra", x, "tdp", y))
        xf, yf = paired_on_seed(g, "attack", "cra", "tdp", "final_f1")
        rows.append({"honest fault": f, "F1 CRA (always on)": med_ci(x), "F1 TDP (sleeper)": med_ci(y),
                     "final F1 CRA": med_ci(xf), "final F1 TDP": med_ci(yf),
                     "TDP censored sleepers": f"{g[g.attack == 'tdp'].delay_censored.sum()}/{g[g.attack == 'tdp'].n_adversary.sum()}"})
        tag = {0.02: "Two", 0.05: "Five", 0.1: "Ten"}[round(f, 2)]
        macro(f"EoneCra{tag}", float(np.median(x)), "results/raw/e1_tdp_collapse/runs.csv")
        macro(f"EoneTdp{tag}", float(np.median(y)), "results/raw/e1_tdp_collapse/runs.csv")
        macro(f"EoneTdpFinal{tag}", float(np.median(yf)), "results/raw/e1_tdp_collapse/runs.csv")
        macro(f"EoneCraFinal{tag}", float(np.median(xf)), "results/raw/e1_tdp_collapse/runs.csv")
    save_stats("e1_tdp_collapse", res)
    tex_table(pd.DataFrame(rows), GEN / "tab_e1.tex",
              "E1: legacy Beta trust on the oracle-free environment. Node-detection F1 over the attack window "
              "and at the final step, median [95\\% CI] over 30 seeds.", "tab:e1")
    fig, ax = plt.subplots(figsize=(3.4, 2.0))
    data, labels = [], []
    for f in sorted(df.fault.unique()):
        for atk in ("cra", "tdp"):
            data.append(df[(df.fault == f) & (df.attack == atk)].det_f1.values)
            labels.append(f"{atk.upper()}\nf={f:g}")
    ax.boxplot(data, tick_labels=labels, widths=0.6)
    ax.set_ylabel("detection F1 (attack window)")
    ax.set_ylim(-0.05, 1.05)
    fig.tight_layout()
    fig.savefig(FIGS / "e1_collapse.pdf")
    plt.close(fig)


def e2() -> None:
    df = load("e2_sleeperguard")
    if df is None:
        return
    res = []
    for (mf, ts, it), g in df.groupby(["coalition", "t_switch", "intensity"]):
        for m in ("det_f1", "valid_reject_rate"):
            x, y = paired_on_seed(g, "backend", "sleeper_guard", "legacy_beta", m)
            res.append(paired_compare(f"{m}[b={mf},ts={ts},i={it}]", "sleeper_guard", x, "legacy_beta", y))
    st = save_stats("e2_sleeperguard", res)
    f1 = st[st.metric.str.startswith("det_f1")]
    macro("EtwoCells", len(f1), "results/raw/stats/e2_sleeperguard.csv")
    macro("EtwoSigBetter", int(((f1.median_diff > 0) & f1.significant).sum()), "results/raw/stats/e2_sleeperguard.csv")
    macro("EtwoSigWorse", int(((f1.median_diff < 0) & f1.significant).sum()), "results/raw/stats/e2_sleeperguard.csv")
    sg = df[df.backend == "sleeper_guard"]
    lg = df[df.backend == "legacy_beta"]
    macro("EtwoSgFOneMin", float(sg.groupby(["coalition", "t_switch", "intensity"]).det_f1.median().min()), "results/raw/e2_sleeperguard/runs.csv")
    macro("EtwoLgFOneMax", float(lg.groupby(["coalition", "t_switch", "intensity"]).det_f1.median().max()), "results/raw/e2_sleeperguard/runs.csv")
    macro("EtwoSgDelayMed", float(sg.delay_median.median()), "results/raw/e2_sleeperguard/runs.csv", "{:.1f}")
    macro("EtwoLgDelayMed", float(lg.delay_median.median()), "results/raw/e2_sleeperguard/runs.csv", "{:.0f}")
    macro("EtwoSgInvalid", float(sg.invalid_commit_rate.max()), "results/raw/e2_sleeperguard/runs.csv", "{:.4f}")
    macro("EtwoLgInvalid", float(lg.invalid_commit_rate.max()), "results/raw/e2_sleeperguard/runs.csv", "{:.4f}")
    # table at t_switch = middle
    mid = sorted(df.t_switch.unique())[len(df.t_switch.unique()) // 2]
    rows = []
    for (mf, it), g in df[df.t_switch == mid].groupby(["coalition", "intensity"]):
        rows.append({"coalition": f"{mf:.3g}", "intensity": it,
                     "F1 legacy": med_ci(g[g.backend == "legacy_beta"].det_f1),
                     "F1 SleeperGuard": med_ci(g[g.backend == "sleeper_guard"].det_f1),
                     "delay SG (steps)": med_ci(g[g.backend == "sleeper_guard"].delay_median),
                     "valid-reject legacy": med_ci(g[g.backend == "legacy_beta"].valid_reject_rate),
                     "valid-reject SG": med_ci(g[g.backend == "sleeper_guard"].valid_reject_rate)})
    tex_table(pd.DataFrame(rows), GEN / "tab_e2.tex",
              f"E2: legacy Beta vs SleeperGuard under the sleeper attack (t\\_switch={mid}, honest fault 0.05), "
              "median [95\\% CI] over 30 seeds. All grid cells and paired tests: results/raw/stats/e2\\_sleeperguard.csv.",
              "tab:e2")
    fig, axes = plt.subplots(1, 2, figsize=(3.4, 1.9), sharey=True)
    for ax, it in zip(axes, sorted(df.intensity.unique())):
        for be, mk in (("legacy_beta", "o"), ("sleeper_guard", "s")):
            g = df[(df.backend == be) & (df.intensity == it) & (df.t_switch == mid)].groupby("coalition").det_f1
            ax.plot(g.median().index, g.median().values, marker=mk, ms=3, label=be.replace("_", " "))
            ax.fill_between(g.median().index, g.quantile(0.25).values, g.quantile(0.75).values, alpha=0.2)
        ax.set_title(f"intensity {it:g}")
        ax.set_xlabel("coalition fraction")
    axes[0].set_ylabel("detection F1")
    axes[0].legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIGS / "e2_sleeperguard.pdf")
    plt.close(fig)


def e3() -> None:
    df = load("e3_ablation")
    if df is None:
        return
    res, rows = [], []
    for (atk, it), g in df.groupby(["attack", "intensity"]):
        for v in ("no_cusum", "no_two_timescale", "no_cap", "none"):
            for m in ("det_f1", "delay_mean", "honest_quarantines_per_1000", "valid_reject_rate"):
                x, y = paired_on_seed(g, "variant", v, "full", m)
                res.append(paired_compare(f"{m}[{atk},{it},{v}]", v, x, "full", y))
        for v in ("full", "no_cusum", "no_two_timescale", "no_cap", "none"):
            h = g[g.variant == v]
            rows.append({"attack": f"{atk.upper()} ({it:g})", "variant": v.replace("_", "-"),
                         "F1": med_ci(h.det_f1), "delay": med_ci(h.delay_mean),
                         "honest FQ/1000": med_ci(h.honest_quarantines_per_1000),
                         "valid-reject": med_ci(h.valid_reject_rate),
                         "invalid-commit": med_ci(h.invalid_commit_rate)})
    save_stats("e3_ablation", res)
    tex_table(pd.DataFrame(rows), GEN / "tab_e3.tex",
              "E3: SleeperGuard ablation, median [95\\% CI] over 30 seeds. FQ = honest false quarantines per 1000 "
              "node-steps. Paired tests vs full: results/raw/stats/e3\\_ablation.csv.", "tab:e3")
    for v in ("full", "no_cusum", "no_two_timescale", "no_cap", "none"):
        h = df[(df.variant == v) & (df.attack == "tdp") & (df.intensity == 0.25)]
        tag = {"full": "Full", "no_cusum": "NoCusum", "no_two_timescale": "NoTwo", "no_cap": "NoCap", "none": "None"}[v]
        macro(f"Ethree{tag}FOne", float(h.det_f1.median()), "results/raw/e3_ablation/runs.csv")
        macro(f"Ethree{tag}Delay", float(h.delay_mean.median()), "results/raw/e3_ablation/runs.csv", "{:.1f}")


def e4() -> None:
    dec, tim, con = load("e4_he", "decisions.csv"), load("e4_he", "timings.csv"), load("e4_he", "consensus.csv")
    if tim is None or dec is None:
        return
    params = json.loads((RAW / "e4_he" / "params.json").read_text())
    rows = []
    for s, g in tim.groupby("sign_iters"):
        d = dec[dec.sign_iters == s]
        out = d[~d.in_band]
        flips_out = int(out.flip.sum())
        flips_in = int(d[d.in_band].flip.sum())
        band = float(d[d.flip].margin.abs().max()) if d.flip.any() else 0.0
        k16 = g[(g.k == 16) & (g["T"] == 32)].total_ms
        rows.append({"sign iters": s, "N": params[str(s)]["poly_modulus_degree"],
                     "modulus bits (max)": f"{params[str(s)]['total_bits']} ({params[str(s)]['max_bits_128bit_security']})",
                     "decisions": len(d), "flips |m|>1e-3": flips_out, "flips |m|<=1e-3": flips_in,
                     "max |m| of a flip": f"{band:.2e}",
                     "ms/tally k=16,T=32": med_ci(k16), "ct KB": f"{g.ct_bytes.median() / 1024:.0f}"})
        macro(f"EfourFlipsOut{['Zero','One','Two','Three'][s]}", flips_out, "results/raw/e4_he/decisions.csv")
        macro(f"EfourDecisions{['Zero','One','Two','Three'][s]}", len(d), "results/raw/e4_he/decisions.csv")
        macro(f"EfourMs{['Zero','One','Two','Three'][s]}", float(k16.median()), "results/raw/e4_he/timings.csv", "{:.0f}")
        macro(f"EfourBand{['Zero','One','Two','Three'][s]}", band, "results/raw/e4_he/decisions.csv", "{:.1e}")
    tex_table(pd.DataFrame(rows), GEN / "tab_e4.tex",
              "E4: HETally accuracy and cost (CKKS, TenSEAL). Flips = decisions differing from the plaintext rule; "
              "m = normalised margin. Latency: median [95\\% CI] per tally on the machine in meta.json.", "tab:e4")
    fig, axes = plt.subplots(1, 2, figsize=(3.4, 1.9))
    for s, g in tim.groupby("sign_iters"):
        gg = g[g["T"] == 32].groupby("k").total_ms.median()
        axes[0].plot(gg.index, gg.values, marker="o", ms=3, label=f"{s} sign iters")
        gt = g[g.k == 16].groupby("T").per_tx_ms.median()
        axes[1].plot(gt.index, gt.values, marker="s", ms=3, label=f"{s}")
    axes[0].set_xlabel("committee size k (T=32)")
    axes[0].set_ylabel("ms per tally")
    axes[0].set_yscale("log")
    axes[1].set_xlabel("batch T (k=16)")
    axes[1].set_ylabel("ms per transaction")
    axes[1].set_yscale("log")
    axes[1].set_xscale("log", base=2)
    axes[0].legend(frameon=False, fontsize=6)
    fig.tight_layout()
    fig.savefig(FIGS / "e4_he_latency.pdf")
    plt.close(fig)
    lk, bd = load("e4_he", "leakage.csv"), load("e4_he", "band.csv")
    if lk is not None:
        macro("EfourLeakErrMax", float(lk.recover_err_max.max()), "results/raw/e4_he/leakage.csv", "{:.0e}")
        macro("EfourSatMaxPct", 100.0 * float(lk.saturated_frac.max()), "results/raw/e4_he/leakage.csv", "{:.2f}")
    if bd is not None:
        fl = bd[bd.flip]
        macro("EfourBandMaxFlip", float(fl.margin.abs().max()) if len(fl) else 0.0, "results/raw/e4_he/band.csv", "{:.0e}")
        ok = bd[bd.margin.abs() > (fl.margin.abs().max() if len(fl) else 0.0)]
        macro("EfourBandMinSafe", float(ok.margin.abs().min()), "results/raw/e4_he/band.csv", "{:.0e}")
        macro("EfourDecisionsTotal", int(len(dec)), "results/raw/e4_he/decisions.csv")
        macro("EfourFlipsTotal", int(dec.flip.sum()), "results/raw/e4_he/decisions.csv")
    if con is not None:
        crow = []
        for (s, be), g in con.groupby(["sign_iters", "backend"]):
            crow.append({"sign iters": s, "backend": be, "seeds": len(g), "F1": med_ci(g.det_f1),
                         "invalid-commit": med_ci(g.invalid_commit_rate), "valid-reject": med_ci(g.valid_reject_rate),
                         "HE flips": int(g.he_flips.sum()), "wall ms/step": med_ci(g.wall_ms_per_step)})
        tex_table(pd.DataFrame(crow), GEN / "tab_e4_consensus.tex",
                  "E4b: end-to-end runs (TDP, SleeperGuard, 200 steps) with the plaintext vs HE tally on identical seeds.",
                  "tab:e4b")
        for s in sorted(con.sign_iters.unique()):
            g = con[(con.sign_iters == s) & (con.backend == "he")]
            macro(f"EfourConsFlips{['Zero','One','Two','Three'][s]}", int(g.he_flips.sum()), "results/raw/e4_he/consensus.csv")
            macro(f"EfourConsWall{['Zero','One','Two','Three'][s]}", float(g.wall_ms_per_step.median()), "results/raw/e4_he/consensus.csv", "{:.0f}")
        p = con[con.backend == "plain"]
        macro("EfourConsWallPlain", float(p.wall_ms_per_step.median()), "results/raw/e4_he/consensus.csv", "{:.2f}")


def e5() -> None:
    df = load("e5_scale")
    if df is None:
        return
    rows = []
    for (n, k), g in df.groupby(["nodes", "k"]):
        rows.append({"nodes": n, "k": k, "F1": med_ci(g.det_f1), "throughput (tx/s, sim.)": f"{g.throughput_tps.median():.0f}",
                     "p50/p95/p99 latency (ms, sim.)": f"{g.latency_p50_ms.median():.1f}/{g.latency_p95_ms.median():.1f}/{g.latency_p99_ms.median():.1f}",
                     "wall ms/step": f"{g.wall_ms_per_step.median():.2f}", "peak MB": f"{g.peak_mem_mb.median():.1f}"})
    tex_table(pd.DataFrame(rows), GEN / "tab_e5.tex",
              "E5: scale. Throughput and latency use the simulated cost model (D7); wall-clock and peak Python heap "
              "are measured. Median over seeds.", "tab:e5")
    big = df[(df.nodes == df.nodes.max()) & (df.k == df.k.max())]
    macro("EfiveMaxNodes", int(df.nodes.max()), "results/raw/e5_scale/runs.csv")
    macro("EfiveBigWall", float(big.wall_ms_per_step.median()), "results/raw/e5_scale/runs.csv", "{:.1f}")
    macro("EfiveBigMem", float(big.peak_mem_mb.median()), "results/raw/e5_scale/runs.csv", "{:.0f}")
    macro("EfiveBigFOne", float(big.det_f1.median()), "results/raw/e5_scale/runs.csv")
    cen = df[df.nodes == df.nodes.max()]
    macro("EfiveBigCensoredPct", 100.0 * float(cen.delay_censored.sum() / cen.n_adversary.sum()), "results/raw/e5_scale/runs.csv", "{:.0f}")
    small = df[df.nodes == df.nodes.min()]
    macro("EfiveSmallCensoredPct", 100.0 * float(small.delay_censored.sum() / small.n_adversary.sum()), "results/raw/e5_scale/runs.csv", "{:.0f}")
    macro("EfiveMinFOne", float(df.groupby(["nodes", "k"]).det_f1.median().min()), "results/raw/e5_scale/runs.csv")


def e6() -> None:
    df = load("e6_audit_budget")
    if df is None:
        return
    res = []
    for (ar, it), g in df.groupby(["audit_rate", "intensity"]):
        x, y = paired_on_seed(g, "backend", "sleeper_guard", "legacy_beta", "det_f1")
        res.append(paired_compare(f"det_f1[a={ar},i={it}]", "sleeper_guard", x, "legacy_beta", y))
    save_stats("e6_audit_budget", res)
    fig, axes = plt.subplots(1, 2, figsize=(3.4, 1.9))
    for be, mk in (("legacy_beta", "o"), ("sleeper_guard", "s")):
        for it, ls in ((0.25, "-"), (1.0, "--")):
            g = df[(df.backend == be) & (df.intensity == it)].groupby("audit_rate")
            axes[0].plot(g.det_f1.median().index, g.det_f1.median().values, ls, marker=mk, ms=3,
                         label=f"{be.split('_')[0]} i={it:g}")
            axes[1].plot(g.delay_mean.median().index, g.delay_mean.median().values, ls, marker=mk, ms=3)
    axes[0].set_xlabel("audit rate")
    axes[0].set_ylabel("detection F1")
    axes[1].set_xlabel("audit rate")
    axes[1].set_ylabel("mean detection delay (steps)")
    axes[1].set_yscale("log")
    axes[0].legend(frameon=False, fontsize=6)
    fig.tight_layout()
    fig.savefig(FIGS / "e6_audit.pdf")
    plt.close(fig)
    sg = df[(df.backend == "sleeper_guard") & (df.intensity == 0.25)].groupby("audit_rate")
    macro("EsixSgFOneLowAudit", float(sg.det_f1.median().iloc[0]), "results/raw/e6_audit_budget/runs.csv")
    macro("EsixSgDelayLowAudit", float(sg.delay_mean.median().iloc[0]), "results/raw/e6_audit_budget/runs.csv", "{:.1f}")
    macro("EsixSgDelayFullAudit", float(sg.delay_mean.median().iloc[-1]), "results/raw/e6_audit_budget/runs.csv", "{:.1f}")
    macro("EsixLowAudit", float(df.audit_rate.min()), "results/raw/e6_audit_budget/runs.csv", "{:.2f}")


def e7() -> None:
    df = load("e7_false_positives")
    if df is None:
        return
    main = df[~df.sweep]
    rows = []
    for (f, cal), g in main.groupby(["fault", "calibration"]):
        n = g[g.attack == "none"]
        t = g[g.attack == "tdp"]
        rows.append({"honest fault": f, "calibration": cal, "FQ/1000 (no attack)": med_ci(n.honest_quarantines_per_1000),
                     "valid-reject (no attack)": med_ci(n.valid_reject_rate), "abort rate": med_ci(n.abort_rate),
                     "F1 (TDP 0.25)": med_ci(t.det_f1), "delay (TDP)": med_ci(t.delay_mean)})
    tex_table(pd.DataFrame(rows), GEN / "tab_e7.tex",
              "E7: false-positive cost of SleeperGuard vs honest fault rate. 'matched': CUSUM calibrated for the true "
              "fault rate; 'fixed\\_0.05': calibrated for 0.05 regardless (misspecified). Median [95\\% CI], 30 seeds.",
              "tab:e7")
    sw = df[df.sweep]
    fig, ax = plt.subplots(figsize=(3.4, 2.1))
    fp = sw[sw.attack == "none"].groupby("alarm").honest_quarantines_per_1000.median()
    dl = sw[sw.attack == "tdp"].groupby("alarm").delay_mean.median()
    ax.plot(fp.values, dl.values, marker="o", ms=3, color=OKABE[5])
    for a, x, y in zip(fp.index, fp.values, dl.values):
        ax.annotate(f"h={a:g}", (x, y), fontsize=6, xytext=(3, 3), textcoords="offset points")
    ax.set_xlabel("honest false quarantines per 1000 node-steps")
    ax.set_ylabel("mean detection delay (steps)")
    fig.tight_layout()
    fig.savefig(FIGS / "e7_tradeoff.pdf")
    plt.close(fig)
    m = main[(main.calibration == "matched") & (main.attack == "none")].groupby("fault").honest_quarantines_per_1000.median()
    for f, v in m.items():
        tag = {0.0: "Zero", 0.02: "Two", 0.05: "Five", 0.1: "Ten", 0.15: "Fifteen", 0.2: "Twenty"}[round(f, 2)]
        macro(f"EsevenFq{tag}", float(v), "results/raw/e7_false_positives/runs.csv")
    mm = main[(main.calibration == "fixed_0.05") & (main.attack == "none")].groupby("fault").honest_quarantines_per_1000.median()
    macro("EsevenFqMisTwenty", float(mm.get(0.2, math.nan)), "results/raw/e7_false_positives/runs.csv")
    vr = main[(main.calibration == "fixed_0.05") & (main.attack == "none")].groupby("fault").valid_reject_rate.median()
    macro("EsevenVrMisTwenty", float(vr.get(0.2, math.nan)), "results/raw/e7_false_positives/runs.csv", "{:.3f}")


def e8() -> None:
    df = load("e8_privacy")
    if df is None:
        return
    res, rows = [], []
    for (be, b), g in df.groupby(["backend", "budget"]):
        for m in ("valid_reject_rate", "invalid_commit_rate", "bribed_weight_share"):
            x, y = paired_on_seed(g, "strategy", "weights", "votes", m)
            res.append(paired_compare(f"{m}[{be},B={b}]", "weights(plaintext)", x, "votes(encrypted)", y))
            x2, y2 = paired_on_seed(g, "strategy", "votes", "random", m)
            res.append(paired_compare(f"{m}[{be},B={b}]", "votes(encrypted)", x2, "random", y2))
        rows.append({"trust": be.replace("_", " "), "B": b,
                     "share: weights": med_ci(g[g.strategy == "weights"].bribed_weight_share),
                     "share: votes": med_ci(g[g.strategy == "votes"].bribed_weight_share),
                     "share: random": med_ci(g[g.strategy == "random"].bribed_weight_share),
                     "valid-reject: weights": med_ci(g[g.strategy == "weights"].valid_reject_rate),
                     "valid-reject: votes": med_ci(g[g.strategy == "votes"].valid_reject_rate),
                     "valid-reject: random": med_ci(g[g.strategy == "random"].valid_reject_rate)})
    st = save_stats("e8_privacy", res)
    tex_table(pd.DataFrame(rows), GEN / "tab_e8.tex",
              "E8 (H3): bribery with public weights ('weights') vs hidden weights inferred from the public ledger "
              "('votes') vs random targets. Share = bribed nodes' weight share at bribe time; valid-reject in the "
              "40 steps after bribery. Median [95\\% CI], 30 seeds; tests in results/raw/stats/e8\\_privacy.csv.", "tab:e8")
    gap = df.pivot_table(index=["backend", "budget"], columns="strategy", values="bribed_weight_share", aggfunc="median")
    macro("EeightMaxShareGap", float((gap["weights"] - gap["votes"]).max()), "results/raw/e8_privacy/runs.csv")
    wv = st[st.a.str.startswith("weights") & st.metric.str.startswith("valid_reject")]
    macro("EeightTests", len(wv), "results/raw/stats/e8_privacy.csv")
    macro("EeightSig", int(wv.significant.sum()), "results/raw/stats/e8_privacy.csv")
    macro("EeightSigWeightsWorse", int((wv.significant & (wv.median_diff > 0)).sum()), "results/raw/stats/e8_privacy.csv")
    vr = st[st.a.str.startswith("votes") & st.metric.str.startswith("bribed_weight_share")]
    macro("EeightVotesBeatRandom", int((vr.significant & (vr.median_diff > 0)).sum()), "results/raw/stats/e8_privacy.csv")
    macro("EeightVotesRandomTests", len(vr), "results/raw/stats/e8_privacy.csv")


def e9() -> None:
    df = load("e9_learning")
    if df is None:
        return
    order = ["pbft", "static_dpos", "majority", "random_delegates", "legacy_beta", "sleeper_guard",
             "sleeper_guard_fixed", "rule", "tabular_q", "d3p", "marl_factored"]
    order = [o for o in order if o in set(df.controller)]
    rows = []
    for c in order:
        g = df[df.controller == c]
        rows.append({"controller": c.replace("_", " "), "reward": med_ci(g.mean_reward_all),
                     "F1": med_ci(g[g.attack != "none"].det_f1),
                     "invalid-commit": med_ci(g.invalid_commit_rate), "valid-reject": med_ci(g.valid_reject_rate),
                     "throughput (sim.)": f"{g.throughput_tps.median():.0f}"})
    tex_table(pd.DataFrame(rows), GEN / "tab_e9.tex",
              "E9: frozen controllers on eval seeds 100-129 pooled over six attack settings (180 runs each). Reward is "
              "the observable objective (D8); F1 excludes the no-attack setting. Median [95\\% CI].", "tab:e9")
    res = []
    for c in ("tabular_q", "d3p", "marl_factored"):
        if c not in set(df.controller):
            continue
        for ref in ("rule", "sleeper_guard_fixed"):
            a = df[df.controller == c].set_index(["attack", "seed"]).mean_reward_all
            b = df[df.controller == ref].set_index(["attack", "seed"]).mean_reward_all
            idx = a.index.intersection(b.index)
            res.append(paired_compare(f"mean_reward_all[{c} vs {ref}]", c, a.loc[idx].values, ref, b.loc[idx].values))
    st = save_stats("e9_learning", res)
    med = df.groupby("controller").mean_reward_all.median()
    best_learn = max(("tabular_q", "d3p", "marl_factored"), key=lambda c: med.get(c, -1e9))
    macro("EnineBestLearner", best_learn.replace("_", " "), "results/raw/e9_learning/runs.csv")
    macro("EnineBestLearnerReward", float(med[best_learn]), "results/raw/e9_learning/runs.csv", "{:.3f}")
    macro("EnineRuleReward", float(med.get("rule", math.nan)), "results/raw/e9_learning/runs.csv", "{:.3f}")
    macro("EnineFixedReward", float(med.get("sleeper_guard_fixed", math.nan)), "results/raw/e9_learning/runs.csv", "{:.3f}")
    dl = df[df.attack != "none"].groupby("controller").delay_mean.median()
    f1 = df[df.attack != "none"].groupby("controller").det_f1.median()
    macro("EnineBestLearnerDelay", float(dl[best_learn]), "results/raw/e9_learning/runs.csv", "{:.0f}")
    macro("EnineFixedDelay", float(dl["sleeper_guard_fixed"]), "results/raw/e9_learning/runs.csv", "{:.1f}")
    macro("EnineDposReward", float(med.get("static_dpos", math.nan)), "results/raw/e9_learning/runs.csv", "{:.3f}")
    macro("EnineDthreeFOne", float(f1.get("d3p", math.nan)), "results/raw/e9_learning/runs.csv")
    macro("EnineFixedFOne", float(f1.get("sleeper_guard_fixed", math.nan)), "results/raw/e9_learning/runs.csv")
    macro("EnineDthreeReward", float(med.get("d3p", math.nan)), "results/raw/e9_learning/runs.csv", "{:.3f}")
    vs_rule = st[st.b == "rule"]
    macro("EnineLearnersBeatRule", int((vs_rule.significant & (vs_rule.median_diff > 0)).sum()), "results/raw/stats/e9_learning.csv")
    macro("EnineLearnersLoseRule", int((vs_rule.significant & (vs_rule.median_diff < 0)).sum()), "results/raw/stats/e9_learning.csv")
    fig, ax = plt.subplots(figsize=(3.4, 2.0))
    ax.boxplot([df[df.controller == c].mean_reward_all.values for c in order],
               tick_labels=[c.replace("_", "\n") for c in order], widths=0.6, showfliers=False)
    ax.set_ylabel("mean reward (observable)")
    plt.setp(ax.get_xticklabels(), fontsize=5)
    fig.tight_layout()
    fig.savefig(FIGS / "e9_controllers.pdf")
    plt.close(fig)


def e10() -> None:
    s, e = load("e10_safety", "search.csv"), load("e10_safety", "env.csv")
    if s is None:
        return
    it = s[s.method == "verified_iterative"]
    macro("EtenIterAbortFrac", float(it.n_aborts.sum() / it.n_candidates.sum()), "results/raw/e10_safety/search.csv", "{:.3f}")
    macro("EtenIterViolations", int(it.violation.sum()), "results/raw/e10_safety/search.csv")
    ex = s[s.method == "exact"]
    macro("EtenExactAbortFrac", float(ex.n_aborts.sum() / ex.n_candidates.sum()), "results/raw/e10_safety/search.csv", "{:.3f}")
    s = ex
    macro("EtenCells", len(s), "results/raw/e10_safety/search.csv")
    macro("EtenViolations", int(s.violation.sum()), "results/raw/e10_safety/search.csv")
    macro("EtenUnsafeCells", int((~s.predicted_safe).sum()), "results/raw/e10_safety/search.csv")
    macro("EtenUnsafeBroken", int(((~s.predicted_safe) & s.any_commit).sum()), "results/raw/e10_safety/search.csv")
    macro("EtenCapUnenforced", int(s.cap_unenforced_not_aborted.sum()), "results/raw/e10_safety/search.csv")
    rows = []
    for (k, c, th), g in s.groupby(["k", "c", "theta"]):
        safe_b = g[g.predicted_safe].b.max() if g.predicted_safe.any() else 0
        first_commit = g[g.any_commit].b.min() if g.any_commit.any() else float("nan")
        rows.append({"k": k, "c": c, "theta": th, "bound: safe for b <=": int(safe_b),
                     "smallest b that forced a commit": "none" if math.isnan(first_commit) else int(first_commit),
                     "violations": int(g.violation.sum())})
    tex_table(pd.DataFrame(rows), GEN / "tab_e10.tex",
              "E10: adversarial search against the capped-influence bound (paper/proof.md). A violation = a commit "
              "forced with b below the bound.", "tab:e10")
    if e is not None:
        src = "results/raw/e10_safety/env.csv"
        safe0 = e[e.predicted_safe & (e.fault == 0.0)]
        safe5 = e[e.predicted_safe & (e.fault == 0.05)]
        unsafe = e[~e.predicted_safe]
        macro("EtenEnvRunsSafeZero", len(safe0), src)
        macro("EtenEnvBreachSafeZero", int((safe0.invalid_commit_rate > 0).sum()), src)
        macro("EtenEnvRunsSafeFive", len(safe5), src)
        macro("EtenEnvBreachSafeFive", int((safe5.invalid_commit_rate > 0).sum()), src)
        macro("EtenEnvMaxInvalidSafeFive", float(safe5.invalid_commit_rate.max()), src, "{:.4f}")
        macro("EtenEnvBreachUnsafe", int((unsafe.invalid_commit_rate > 0).sum()), src)
        macro("EtenEnvRunsUnsafe", len(unsafe), src)
        macro("EtenEnvMaxInvalidUnsafe", float(unsafe.invalid_commit_rate.max()), src, "{:.4f}")
        rows = []
        for (b, f), g in e.groupby(["b", "fault"]):
            rows.append({"b": b, "honest fault": f, "bound says safe": bool(b * 2 / 16 < 0.667),
                         "runs with an invalid commit": f"{int((g.invalid_commit_rate > 0).sum())}/{len(g)}",
                         "max invalid-commit rate": f"{g.invalid_commit_rate.max():.4f}",
                         "median F1": f"{g.det_f1.median():.2f}"})
        tex_table(pd.DataFrame(rows), GEN / "tab_e10_env.tex",
                  r"E10b: full environment, exact cap ($k=16$, $c=2$, $\theta=0.667$; bound safe for $b\le5$), "
                  "damage-maximising coalition approving invalid transactions at lie rates 0.1/0.3/1.0, 30 seeds each.",
                  "tab:e10b")


def e11() -> None:
    df = load("e11_adaptive")
    if df is None:
        return
    best = json.loads((RAW / "e11_adaptive" / "best.json").read_text())
    rows = []
    for vn in ["legacy_beta", "sg_full", "sg_no_cusum", "sg_no_two_timescale", "sg_no_cap", "sg_none"]:
        g = df[(df.variant == vn) & df.is_best]
        bc = best[vn]
        rows.append({"defence": vn.replace("_", " "), "attacker lie rate": bc["lie_rate"], "b": bc["b"],
                     "target": bc["target"], "invalid-commit": med_ci(g.invalid_commit_rate),
                     "valid-reject": med_ci(g.valid_reject_rate), "F1": med_ci(g.det_f1),
                     "runs w/ invalid commit": f"{int((g.invalid_commit_rate > 0).sum())}/{len(g)}"})
        tag = "".join(w.capitalize() for w in vn.replace("sg_", "sg ").replace("_", " ").split())
        macro(f"EelevenRate{tag}", bc["lie_rate"], "results/raw/e11_adaptive/best.json")
        macro(f"EelevenB{tag}", bc["b"], "results/raw/e11_adaptive/best.json")
        macro(f"EelevenInvalid{tag}", float(g.invalid_commit_rate.median()), "results/raw/e11_adaptive/runs.csv", "{:.4f}")
        macro(f"EelevenFOne{tag}", float(g.det_f1.median()), "results/raw/e11_adaptive/runs.csv")
        macro(f"EelevenReject{tag}", float(g.valid_reject_rate.median()), "results/raw/e11_adaptive/runs.csv", "{:.3f}")
    tex_table(pd.DataFrame(rows), GEN / "tab_e11.tex",
              "E11: each defence against the damage-maximising coalition chosen by search on seeds 30-39 "
              r"(lie rate, coalition size b of 16, target), evaluated on seeds 100-129. Median [95\% CI].", "tab:e11")
    sg = df[df.variant == "sg_full"]
    macro("EelevenSgBelowBoundBreach", int((sg[sg.b <= 5].invalid_commit_rate > 0).sum()), "results/raw/e11_adaptive/runs.csv")
    macro("EelevenSgBelowBoundRuns", int((sg.b <= 5).sum()), "results/raw/e11_adaptive/runs.csv")


def e12() -> None:
    df = load("e12_lierate")
    if df is None:
        return
    fig, ax = plt.subplots(figsize=(3.4, 2.2))
    ax2 = ax.twinx()
    for be, mk, col in (("sleeper_guard", "s", OKABE[5]), ("legacy_beta", "o", OKABE[1])):
        g = df[df.backend == be].groupby("lie_rate")
        ax.plot(g.det_f1.median().index, g.det_f1.median().values, marker=mk, ms=3, color=col,
                label=f"F1 {be.replace('_', ' ')}")
        ax.fill_between(g.det_f1.median().index, g.det_f1.quantile(0.25).values, g.det_f1.quantile(0.75).values,
                        color=col, alpha=0.15)
    g = df[df.backend == "sleeper_guard"].groupby("lie_rate")
    ax2.plot(g.honest_quarantines_per_1000.median().index, g.honest_quarantines_per_1000.median().values,
             "--", marker="^", ms=3, color=OKABE[6], label="honest FQ/1000 (SG)")
    ax.set_xlabel("coalition lie rate")
    ax.set_ylabel("detection F1")
    fqmax = float(g.honest_quarantines_per_1000.median().max())
    ax2.set_ylim(0, max(2.0, 1.5 * fqmax))
    ax2.set_ylabel("honest FQ / 1000 node-steps")
    ax.set_xscale("log")
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.set_ylim(-0.02, 1.15)
    ax.legend(h1 + h2, l1 + l2, frameon=False, fontsize=6, loc="upper left", ncol=1)
    fig.tight_layout()
    fig.savefig(FIGS / "e12_lierate.pdf")
    plt.close(fig)
    sg = df[df.backend == "sleeper_guard"].groupby("lie_rate").det_f1.median()
    half = sg[sg >= 0.5]
    macro("EtwelveHalfRate", float(half.index.min()) if len(half) else math.nan, "results/raw/e12_lierate/runs.csv")
    macro("EtwelveFOneLow", float(sg.iloc[0]), "results/raw/e12_lierate/runs.csv")
    macro("EtwelveLowRate", float(sg.index[0]), "results/raw/e12_lierate/runs.csv")
    macro("EtwelveFOneHigh", float(sg.iloc[-1]), "results/raw/e12_lierate/runs.csv")
    fq = df[df.backend == "sleeper_guard"].honest_quarantines_per_1000
    macro("EtwelveFqMax", float(df[df.backend == "sleeper_guard"].groupby("lie_rate").honest_quarantines_per_1000.median().max()), "results/raw/e12_lierate/runs.csv")
    _ = fq


def e13() -> None:
    df = load("e13_preprint_protocol")
    if df is None:
        return
    src = "results/raw/e13_preprint_protocol/runs.csv"
    rows = []
    for be in ("legacy_beta", "sleeper_guard"):
        g = df[df.backend == be]
        rows.append({"trust": be.replace("_", " "), "adversaries": int(g.n_adversary.median()),
                     "F1 episodes 1-25 (dormant)": med_ci(g.f1_pre_mean),
                     "F1 episodes 26-50 (active)": med_ci(g.f1_post_mean),
                     "F1 final episode": med_ci(g.f1_final)})
        tag = "Legacy" if be == "legacy_beta" else "Sg"
        macro(f"Ethirteen{tag}Pre", float(g.f1_pre_mean.median()), src)
        macro(f"Ethirteen{tag}Post", float(g.f1_post_mean.median()), src)
        macro(f"Ethirteen{tag}Final", float(g.f1_final.median()), src)
    tex_table(pd.DataFrame(rows), GEN / "tab_e13.tex",
              r"E13: the sleeper attack under the preprint's protocol (16 nodes, 4 adversaries, 50 episodes $\times$ 100 "
              r"steps, activation after episode 25, intensity 0.75), F1 at the end of each episode with static labels as "
              r"in the preprint, averaged over the dormant and active phases. Median [95\% CI], 30 seeds.", "tab:e13")


def hardware() -> None:
    p = RAW / "e4_he" / "meta.json"
    if not p.exists():
        return
    m = json.loads(p.read_text())["machine"]
    src = "results/raw/e4_he/meta.json"
    macro("HwCpu", str(m.get("cpu_model") or m.get("processor")).replace("(R)", "").replace("(TM)", ""), src)
    macro("HwCores", f"{m.get('physical_cores', 'n/a')} physical / {m.get('cpu_count')} logical", src)
    macro("HwRam", f"{m.get('ram_gb')}~GB", src)
    macro("HwOs", str(m.get("platform")).replace("_", " "), src)
    macro("HwTenseal", str(m.get("tenseal")), src)
    macro("HwPython", str(m.get("python")), src)


# ===========================================================================================
def main() -> None:
    global RAW
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=str(ROOT / "results" / "raw"))
    a = ap.parse_args()
    RAW = Path(a.raw)
    GEN.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)
    for f in (e0, e1, e2, e3, e4, e5, e6, e7, e8, e9, e10, e11, e12, e13, hardware):
        try:
            f()
            print(f"[assets] {f.__name__} ok")
        except Exception as exc:  # report and continue; a missing table is visible in the PDF
            print(f"[assets] {f.__name__} FAILED: {exc!r}")
            raise
    lines = ["% AUTO-GENERATED by paper/make_assets.py from results/raw/ -- do not edit"]
    for k in sorted(NUM):
        lines.append(f"\\newcommand{{\\{k}}}{{{NUM[k]}}}  % {SOURCES[k]}")
    (GEN / "numbers.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (GEN / "numbers_sources.json").write_text(json.dumps({k: {"value": NUM[k], "source": SOURCES[k]} for k in NUM}, indent=2))
    print(f"[assets] {len(NUM)} macros -> {GEN / 'numbers.tex'}")


RAW = ROOT / "results" / "raw"

if __name__ == "__main__":
    main()
