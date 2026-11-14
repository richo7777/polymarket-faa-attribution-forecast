"""FAA outage attribution forecaster.

For every market in a Polymarket FAA outage attribution family, this
program projects the Yes price for each minute of the four hours after a
checkpoint, as five quantiles per minute.

Method: a drift-free random walk around the checkpoint price. The walk's
step size comes from how jumpy the market was in the two hours before the
checkpoint: the spread of its one-minute moves, kept inside a floor and a
ceiling so dead markets still widen a little and panicked markets do not
explode the bands. The bands open with a sub-square-root power of the
horizon (exponent 0.35), which the practice sweep settled on.
"""

import json
import math
import os
from pathlib import Path

# --- tuned settings (from the practice sweep) ---
WINDOW = 120          # minutes of history feeding the volatility estimate
VOL_FLOOR = 0.0006    # smallest per-minute spread we will believe
VOL_CEIL = 0.015      # largest per-minute spread we will believe
SPREAD_POWER = 0.35   # how fast the bands open with horizon
TAIL = 2.2            # z for the 5% / 95% bands (jump insurance)
QUARTER = 0.6745      # z for the 25% / 75% bands
Z_VALUES = (-TAIL, -QUARTER, 0.0, QUARTER, TAIL)


def _pinned(value, low, high):
    if value < low:
        return low
    if value > high:
        return high
    return value


def _recent_spread(history):
    """Spread of one-minute moves inside the last WINDOW prices.

    Population standard deviation of those moves (demeaned), pinned into
    [VOL_FLOOR, VOL_CEIL].
    """
    window = history[-WINDOW:]
    moves = [window[i + 1] - window[i] for i in range(len(window) - 1)]
    if len(moves) < 2:
        return VOL_FLOOR
    centre = sum(moves) / len(moves)
    var = sum((m - centre) ** 2 for m in moves) / len(moves)
    return _pinned(math.sqrt(var), VOL_FLOOR, VOL_CEIL)


def _bands(anchor, spread, minutes):
    """One row per forecast minute; each row holds the five quantiles."""
    rows = []
    for h in range(1, minutes + 1):
        reach = spread * (h ** SPREAD_POWER)
        rows.append([round(_pinned(anchor + z * reach, 0.0, 1.0), 6) for z in Z_VALUES])
    return rows


def _forecast_case(case):
    horizon = case["horizon_minutes"]
    out = []
    for market in case["markets"]:
        trail = market["prices"]
        anchor = trail[-1]
        spread = _recent_spread(trail)
        out.append({"id": market["id"], "q": _bands(anchor, spread, horizon)})
    return {"forecasts": out}


def main():
    in_dir = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    for src in sorted(in_dir.glob("*.in")):
        with open(src, "r", encoding="utf-8") as fh:
            case = json.load(fh)
        payload = _forecast_case(case)
        dest = out_dir / (src.stem + ".out")
        with open(dest, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, separators=(",", ":"))
            fh.write("\n")


if __name__ == "__main__":
    main()
