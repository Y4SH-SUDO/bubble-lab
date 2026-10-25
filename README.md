# Bubble Lab

Replay past crashes and a simulated "AI bubble" economy, and see how different investing strategies behave.
**This is a learning tool, not financial advice and not a forecast.**

## Run it (VS Code, Codespaces or github.dev, anything with Python 3.9+)

    pip install -r requirements.txt
    python run.py history                          # crash replays, built-in approximate data
    python run.py history --real                   # real monthly data (needs internet), shows full recoveries
    python run.py ai --p-burst 0.5 --entry mid     # AI bubble: burst vs no burst
    python run.py ai --entry peak --months 120     # what if you buy at the top?

Charts land in `output/` (PNG, ready to post).

## Files

- `strategies.py` the 6 strategies (hold, DCA, panic, stop-loss, trend, ladder). Add your own here.
- `scenarios.py` historical crash data and the downloader.
- `montecarlo.py` the toy AI-bubble economy. All assumptions are in `PARAMS` at the top.
- `run.py` command line and charts.

## Read this before you trust any result

- The AI economy is **assumption-driven**. `--p-burst` is *your* belief, not a measured probability. The model cannot tell you whether AI is a bubble.
- Simulated crashes are simpler than real ones. Tweak `CRASH_NOISE` and the `PARAMS` ranges and watch how much the "best" strategy changes. That sensitivity is the real finding.
- Built-in history is approximate, quarterly, price only, and stops before the full recovery. Use `--real` for better data.
- Strategy thresholds (20%, 30%, 10-month average) are arbitrary. Don't tune them until history looks good, that's overfitting.

## Posting on LinkedIn

- Lead with one finding and one chart (`ai_worlds.png` or `ai_strategies.png`).
- State your assumptions in the first lines: "simulated, not a forecast".
- Don't tell people what to buy. Say what you learned and what surprised you.
- Link the repo (GitHub) so people can change the assumptions themselves.
