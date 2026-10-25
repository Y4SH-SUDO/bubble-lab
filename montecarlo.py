"""A toy 'AI bubble' economy.

price = fundamentals x valuation premium x noise

* fundamentals (think: real earnings) grow with a random wobble
* the premium is how much extra the market pays on top. It inflates during a boom, then either
    - "burst":    collapses to a trough, then slowly drifts back to fair value, or
    - "noburst":  earnings grow into the valuation, so the premium just fades gently

THESE NUMBERS ARE ASSUMPTIONS, not forecasts. Change them in PARAMS and see what changes.
"""
import numpy as np

PARAMS = {
    "burst": dict(growth=(0.04, 0.10), peak=(1.6, 2.8), trough=(0.45, 0.90),
                  crash_months=(6, 25), revert_months=(36, 85)),
    "noburst": dict(growth=(0.10, 0.16), peak=(1.3, 2.0), settle=1.1, fade_months=60),
}
FUND_VOL = 0.04    # monthly volatility of fundamentals
NOISE = 0.03       # monthly price noise on top
CRASH_NOISE = 2.5  # noise multiplier while a burst is happening (real crashes are jumpy, with fake rallies)


def _premium(world, boom, months, rng):
    P = PARAMS[world]
    t = np.arange(months)
    peak = rng.uniform(*P["peak"])
    prem = np.ones(months)
    up = t < boom
    prem[up] = 1 + (peak - 1) * (t[up] / boom) ** 1.5          # convex inflation
    if world == "burst":
        crash = int(rng.integers(*P["crash_months"]))
        trough = rng.uniform(*P["trough"])
        revert = int(rng.integers(*P["revert_months"]))
        knots_t = [boom, boom + crash, boom + crash + revert, months]
        knots_v = np.log([peak, trough, 1.0, 1.0])
    else:
        knots_t = [boom, boom + P["fade_months"], months]
        knots_v = np.log([peak, P["settle"], P["settle"]])
    down = t >= boom
    prem[down] = np.exp(np.interp(t[down], knots_t, knots_v))
    stress = (boom, boom + crash + 12) if world == "burst" else (0, 0)
    return prem, stress


def make_paths(n, world, months=160, seed=0):
    """Returns (paths, boom_lengths). Each path is a list of monthly prices starting at ~1.0."""
    rng = np.random.default_rng(seed)
    paths, booms = [], []
    for _ in range(n):
        boom = int(rng.integers(12, 37))
        g = rng.uniform(*PARAMS[world]["growth"])
        fund = np.exp(np.cumsum(g / 12 - 0.5 * FUND_VOL**2 + FUND_VOL * rng.standard_normal(months)))
        prem, (lo, hi) = _premium(world, boom, months, rng)
        sd = np.full(months, NOISE)
        sd[lo:hi] *= CRASH_NOISE
        price = fund * prem * np.exp(sd * rng.standard_normal(months))
        paths.append(price / price[0])
        booms.append(boom)
    return paths, booms
