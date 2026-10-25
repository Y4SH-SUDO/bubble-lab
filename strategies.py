"""Investing strategies.

Every strategy takes a list of prices and returns the portfolio value at every step.
You start with 1.0 (read it as "100% of your money"), so 1.5 means +50% and 0.4 means -60%.
Steps are months in the AI simulation and quarters in the history replay,
so dca steps / moving-average length are parameters.
"""


def hold(p, **_):
    """Put everything in on day one, never touch it."""
    u = 1.0 / p[0]
    return [u * x for x in p]


def dca(p, steps=12, **_):
    """Invest 1/steps of your money each step until fully invested."""
    cash, units, out = 1.0, 0.0, []
    for i, x in enumerate(p):
        if i < steps:
            chunk = 1.0 / steps
            units += chunk / x
            cash -= chunk
        out.append(cash + units * x)
    return out


def panic(p, drop=0.30, **_):
    """Sell everything after a 30% fall from your best value, never buy back."""
    units, cash, peak, out = 1.0 / p[0], 0.0, 1.0, []
    for x in p:
        if units:
            val = units * x
            peak = max(peak, val)
            if val <= peak * (1 - drop):
                cash, units = val, 0.0
        out.append(cash + units * x)
    return out


def stop_loss(p, drop=0.20, rebound=0.15, **_):
    """Sell after a 20% fall, buy back once price bounces 15% off its low."""
    units, cash, peak, low, out = 1.0 / p[0], 0.0, 1.0, 0.0, []
    for x in p:
        if units:
            val = units * x
            peak = max(peak, val)
            if val <= peak * (1 - drop):
                cash, units, low = val, 0.0, x
        else:
            low = min(low, x)
            if x >= low * (1 + rebound):
                units, cash = cash / x, 0.0
                peak = units * x
        out.append(cash + units * x)
    return out


def trend(p, ma=10, **_):
    """Invested while price is above its moving average, in cash while below."""
    units, cash, out = 1.0 / p[0], 0.0, []
    for i, x in enumerate(p):
        if i >= ma:
            above = x > sum(p[i - ma + 1:i + 1]) / ma
            if units and not above:
                cash, units = units * x, 0.0
            elif not units and above:
                units, cash = cash / x, 0.0
        out.append(cash + units * x)
    return out


def ladder(p, start_frac=0.4, levels=(0.2, 0.3, 0.4), **_):
    """Invest 40% now, keep 60% cash and buy more at -20%, -30%, -40% from the peak."""
    slice_ = (1 - start_frac) / len(levels)
    units, cash, peak = start_frac / p[0], 1 - start_frac, p[0]
    todo, out = list(levels), []
    for x in p:
        peak = max(peak, x)
        while todo and cash > 1e-12 and x <= peak * (1 - todo[0]):
            amt = min(slice_, cash)
            units += amt / x
            cash -= amt
            todo.pop(0)
        out.append(cash + units * x)
    return out


STRATEGIES = {
    "Buy & hold": hold,
    "DCA": dca,
    "Panic sell": panic,
    "Stop-loss": stop_loss,
    "Trend (MA)": trend,
    "Ladder": ladder,
}


def max_drawdown(values):
    """Worst peak-to-trough fall, e.g. -0.45 means a 45% drop at some point."""
    peak, worst = values[0], 0.0
    for v in values:
        peak = max(peak, v)
        worst = min(worst, v / peak - 1)
    return worst
