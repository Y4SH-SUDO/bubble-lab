"""Run EVERYTHING and see which conclusions survive.

    python sweep.py

Tries every combination of: entry time x crash roughness x crash depth x your belief that it bursts.
Then counts how often each strategy wins. A strategy that wins in only one setting is a fluke;
one that keeps winning across settings is a real finding.
"""
import itertools
from collections import Counter, defaultdict

import numpy as np

import montecarlo as mc
from strategies import STRATEGIES

N, H = 400, 96
ENTRIES = ["early", "mid", "peak"]
NOISES = [1.0, 2.5, 4.0]                                   # how jumpy the crash is
DEPTHS = {"mild": (0.70, 1.00), "base": (0.45, 0.90), "deep": (0.25, 0.65)}   # trough valuation
BELIEFS = [0.0, 0.2, 0.5, 0.8, 1.0]                        # your chance of a burst


def evaluate(paths, booms, entry):
    res = {k: [] for k in STRATEGIES}
    for p, b in zip(paths, booms):
        s = {"early": 0, "mid": b // 2, "peak": b}[entry]
        w, pre = list(p[s:s + H]), list(p[max(0, s - 10):s])
        for k, f in STRATEGIES.items():
            res[k].append(f(w, pre=pre)[-1])
    return {k: np.array(v) for k, v in res.items()}


calm_paths, calm_booms = mc.make_paths(N, "noburst", seed=2)
calm = {e: evaluate(calm_paths, calm_booms, e) for e in ENTRIES}

settings = []   # each: dict(entry, belief, stats={strategy: (median, p5, lose)})
for noise, (depth, trough) in itertools.product(NOISES, DEPTHS.items()):
    mc.CRASH_NOISE, mc.PARAMS["burst"]["trough"] = noise, trough
    bp, bb = mc.make_paths(N, "burst", seed=1)
    for e in ENTRIES:
        burst = evaluate(bp, bb, e)
        for belief in BELIEFS:
            k = int(belief * N)
            stats = {}
            for s in STRATEGIES:
                f = np.concatenate([burst[s][:k], calm[e][s][:N - k]])
                stats[s] = (np.median(f), np.percentile(f, 5), (f < 1).mean())
            settings.append(dict(entry=e, belief=belief, noise=noise, depth=depth, stats=stats))

names = list(STRATEGIES)
win = {m: Counter() for m in ("median", "worst5", "fewest_losses")}
rank = {m: defaultdict(list) for m in ("median", "worst5")}
below1 = Counter()
cell = {m: defaultdict(Counter) for m in ("median", "worst5")}

for st in settings:
    S = st["stats"]
    by_med = sorted(names, key=lambda n: -S[n][0])
    by_p5 = sorted(names, key=lambda n: -S[n][1])
    by_lose = sorted(names, key=lambda n: S[n][2])
    win["median"][by_med[0]] += 1
    win["worst5"][by_p5[0]] += 1
    win["fewest_losses"][by_lose[0]] += 1
    for i, n in enumerate(by_med): rank["median"][n].append(i + 1)
    for i, n in enumerate(by_p5): rank["worst5"][n].append(i + 1)
    for n in names:
        if S[n][0] < 1: below1[n] += 1
    cell["median"][(st["entry"], st["belief"])][by_med[0]] += 1
    cell["worst5"][(st["entry"], st["belief"])][by_p5[0]] += 1

T = len(settings)
print(f"\n{T} settings = {len(ENTRIES)} entries x {len(NOISES)} roughness x {len(DEPTHS)} depths x {len(BELIEFS)} beliefs, {N} paths each\n")
print("ROBUSTNESS LEADERBOARD  (rank 1 = best, 6 = worst)")
print(f"{'strategy':<12}{'#1 median':>10}{'#1 worst5%':>12}{'#1 fewest loss':>16}{'avg rank med':>14}{'avg rank worst5':>17}{'median<1':>10}")
for n in names:
    print(f"{n:<12}{win['median'][n]:>10}{win['worst5'][n]:>12}{win['fewest_losses'][n]:>16}"
          f"{np.mean(rank['median'][n]):>14.2f}{np.mean(rank['worst5'][n]):>17.2f}{below1[n] / T:>10.0%}")

for m, title in (("median", "WINNER BY MEDIAN OUTCOME"), ("worst5", "WINNER BY WORST-5% OUTCOME")):
    print(f"\n{title}  (most frequent winner, out of 9 crash variants)")
    print(f"{'entry':<8}" + "".join(f"{'burst '+format(b, '.0%'):>20}" for b in BELIEFS))
    for e in ENTRIES:
        row = f"{e:<8}"
        for b in BELIEFS:
            w, c = cell[m][(e, b)].most_common(1)[0]
            row += f"{w + ' ' + str(c) + '/9':>20}"
        print(row)
