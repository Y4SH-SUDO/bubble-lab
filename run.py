"""Bubble Lab.

  python run.py history                       replay real crashes with every strategy
  python run.py ai --p-burst 0.5 --entry mid  simulate an AI bubble: burst vs no burst
"""
import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from montecarlo import make_paths
from scenarios import HISTORY, load_real
from strategies import STRATEGIES, max_drawdown

OUT = "output"
os.makedirs(OUT, exist_ok=True)
COLORS = ["#2563eb", "#16a34a", "#dc2626", "#d97706", "#7c3aed", "#0891b2"]


def history(args):
    for key, sc in HISTORY.items():
        if args.real:
            prices, peak, start_year = load_real(sc["real"])
            per_year, kw, back = 12, dict(steps=12, ma=10), 12     # monthly data
        else:
            prices, peak, start_year = sc["prices"], sc["peak_step"], sc["start_year"]
            per_year, kw, back = 4, dict(steps=8, ma=4), 4         # quarterly data
        for label, s in (("early start", max(0, peak - back)), ("at the peak", peak)):
            window = prices[s:]
            print(f"\n{sc['name']} - invest {label}")
            print(f"{'strategy':<12}{'end value':>10}{'worst dip':>11}")
            fig, ax = plt.subplots(figsize=(9, 4.8))
            yrs = [start_year + (s + i) / per_year for i in range(len(window))]
            for (name, f), c in zip(STRATEGIES.items(), COLORS):
                v = f(window, **kw)
                print(f"{name:<12}{v[-1]:>10.2f}{max_drawdown(v):>11.0%}")
                ax.plot(yrs, v, label=name, color=c, lw=2)
            ax.axhline(1, color="gray", ls="--", lw=1)
            ax.set(title=f"{sc['name']} - start {label} (1.0 = your money)", xlabel="year")
            ax.legend(ncol=3, fontsize=8)
            fig.tight_layout()
            fig.savefig(f"{OUT}/history_{key}_{label.replace(' ', '_')}.png", dpi=160)
            plt.close(fig)


def run_world(world, n, horizon, entry, seed):
    paths, booms = make_paths(n, world, seed=seed)
    res = {k: [] for k in STRATEGIES}
    for p, b in zip(paths, booms):
        s = {"early": 0, "mid": b // 2, "peak": b}[entry]
        window = list(p[s:s + horizon])
        for k, f in STRATEGIES.items():
            v = f(window)
            res[k].append((v[-1], max_drawdown(v)))
    return {k: np.array(v) for k, v in res.items()}, paths


def table(title, res):
    print(f"\n{title}")
    print(f"{'strategy':<12}{'median':>8}{'worst 5%':>10}{'% lose':>8}{'typical dip':>13}")
    for k, a in res.items():
        fin, dd = a[:, 0], a[:, 1]
        print(f"{k:<12}{np.median(fin):>8.2f}{np.percentile(fin, 5):>10.2f}"
              f"{(fin < 1).mean():>8.0%}{np.median(dd):>13.0%}")


def ai(args):
    n, h = args.paths, args.months
    burst, bp = run_world("burst", n, h, args.entry, 1)
    calm, cp = run_world("noburst", n, h, args.entry, 2)
    k = int(args.p_burst * n)
    blend = {s: np.vstack([burst[s][:k], calm[s][:n - k]]) for s in STRATEGIES}
    print(f"\nEntry: {args.entry} of the boom | horizon: {h} months | {n} paths per world")
    print("(1.00 = you got your money back, 1.50 = +50%)")
    table("WORLD A - the AI bubble BURSTS", burst)
    table("WORLD B - it does NOT burst", calm)
    table(f"BLEND - you think there is a {args.p_burst:.0%} chance of a burst", blend)

    fig, ax = plt.subplots(figsize=(9, 4.8))
    for paths, name, c in ((bp, "Bursts", "#dc2626"), (cp, "Doesn't burst", "#16a34a")):
        a = np.array(paths)
        x = np.arange(a.shape[1]) / 12
        ax.fill_between(x, np.percentile(a, 10, 0), np.percentile(a, 90, 0), color=c, alpha=.18)
        ax.plot(x, np.median(a, 0), color=c, lw=2.2, label=f"{name} (median, 10-90% band)")
    ax.set(title="Two possible AI-bubble worlds (simulated, not a forecast)",
           xlabel="years", ylabel="index (start = 1.0)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(f"{OUT}/ai_worlds.png", dpi=160)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), sharey=True)
    for ax, res, t in ((axes[0], burst, "If it bursts"), (axes[1], calm, "If it doesn't")):
        bp_ = ax.boxplot([res[s][:, 0] for s in STRATEGIES], showfliers=False, patch_artist=True)
        for patch, c in zip(bp_["boxes"], COLORS):
            patch.set_facecolor(c)
            patch.set_alpha(.6)
        ax.axhline(1, color="gray", ls="--", lw=1)
        ax.set_xticks(range(1, len(STRATEGIES) + 1), list(STRATEGIES), rotation=30, fontsize=8)
        ax.set_title(t)
    axes[0].set_ylabel(f"final value after {h} months (1.0 = break-even)")
    fig.tight_layout()
    fig.savefig(f"{OUT}/ai_strategies.png", dpi=160)
    plt.close(fig)
    print(f"\nCharts saved in ./{OUT}/")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    h = sub.add_parser("history")
    h.add_argument("--real", action="store_true", help="download real monthly data (needs internet + yfinance)")
    h.set_defaults(fn=history)
    a = sub.add_parser("ai")
    a.add_argument("--p-burst", type=float, default=0.5, help="your belief: chance it bursts (0-1)")
    a.add_argument("--entry", choices=["early", "mid", "peak"], default="mid")
    a.add_argument("--paths", type=int, default=1000)
    a.add_argument("--months", type=int, default=96)
    a.set_defaults(fn=ai)
    args = ap.parse_args()
    args.fn(args)
