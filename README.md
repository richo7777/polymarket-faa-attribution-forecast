# FAA attribution forecaster

A small forecaster for the make.fun `polymarket-faa-attribution-02` bounty.
Given a Polymarket family's per-minute Yes prices up to a checkpoint, it
predicts the price at every minute of the following four hours, as five
quantiles (5/25/50/75/95) per minute.

## How it predicts

The forecast is a random walk with no drift, anchored on the checkpoint
price. The walk's width comes from the market's own recent behaviour: the
standard deviation of its one-minute moves over the previous two hours,
clamped into a sane range so quiet markets still get some width and wild
ones do not blow up.

For a horizon of `h` minutes and a quantile with z-score `z`:

    q = clamp(anchor + z * sigma * h^0.35, 0, 1)

The 5% and 95% bands use z = ±2.2 rather than the textbook ±1.645 — the
FAA markets jump hard (one moved twenty points in a minute), so the tails
carry extra insurance. The middle bands use the usual normal quartiles.

## Settings

- Lookback: 120 minutes
- Sigma floor / ceiling: 0.0006 / 0.015
- Horizon exponent: 0.35
- Tail z: ±2.2; quartile z: ±0.6745

## Local practice check

On the six practice cases the forecaster scores a mean pinball loss of
0.251713, against a local house baseline of 0.347421 — about 28% better,
and ahead on every one of the six cases. (The rules quote the official
house baseline at 0.363589.)

## Running it

    python3 main.py

It reads every `*.in` case from `$MAKEFUN_INPUT_DIR` (default `/input`)
and writes the matching `*.out` forecast to `$MAKEFUN_OUTPUT_DIR`
(default `/output`). Standard library only, no network, deterministic.
