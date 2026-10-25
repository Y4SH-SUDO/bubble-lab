"""Historical crash data.

Built-in data = APPROXIMATE quarter-end index levels (price only, no dividends) covering the crash window.
It ends before the full recovery, so use `python run.py history --real` to download real monthly data
(needs internet + yfinance) and see the whole story, including the long recovery.
"""

NASDAQ_Q = [1835, 1895, 1694, 2193, 2461, 2686, 2857, 4069, 4573, 3966, 3673, 2471,
            1840, 2161, 1498, 1950, 1845, 1463, 1172, 1335, 1341, 1623, 1787, 2003]  # 1998Q1-2003Q4
SP_Q = [1418, 1421, 1503, 1527, 1468, 1323, 1280, 1166, 904, 798, 919, 1057, 1115,
        1169, 1031, 1141, 1258]  # 2006Q4-2010Q4

HISTORY = {
    "dotcom": {
        "name": "Dot-com crash (Nasdaq)",
        "prices": NASDAQ_Q, "start_year": 1998.0, "peak_step": 8,          # peak = 2000Q1
        "real": ("^IXIC", "1998-01-01", "2016-01-01", "2001-01-01"),       # symbol, start, end, find peak before
    },
    "gfc": {
        "name": "2008 crisis (S&P 500)",
        "prices": SP_Q, "start_year": 2006.75, "peak_step": 3,             # peak = 2007Q3
        "real": ("^GSPC", "2006-10-01", "2014-01-01", "2008-06-01"),
    },
}


def load_real(spec):
    """Download monthly closes from Yahoo Finance. Returns (prices, peak_step, start_year)."""
    import yfinance as yf
    sym, start, end, peak_before = spec
    s = yf.Ticker(sym).history(start=start, end=end, interval="1mo")["Close"].dropna()
    peak_step = int(s.index.get_loc(s[:peak_before].idxmax()))
    return list(s.values), peak_step, s.index[0].year + (s.index[0].month - 1) / 12
