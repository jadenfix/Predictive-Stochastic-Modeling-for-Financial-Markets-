"""Rule-based bull and bear market dating.

A bear market runs from a price peak to the following trough when the index
falls by at least `decline` from the peak before rising by `rise` from the
trough (threshold logic in the spirit of Lunde and Timmermann, 2004). The
algorithm is a causal state machine: its state at month t depends only on
prices through t. Ex-post labels, however, are backdated to the peak, so they
use later information and serve only as forecast targets.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from psm.config import BEAR_DECLINE, BULL_RISE


@dataclass(frozen=True)
class TurningPoint:
    kind: str  # "peak" or "trough"
    index: int  # position of the extreme price
    confirmed_at: int  # position at which the threshold was crossed


@dataclass(frozen=True)
class Dating:
    """Result of dating one price history."""

    labels: np.ndarray  # 1 = bear month (ex post), 0 = bull month
    realtime_state: np.ndarray  # 1 = machine in bear state at t, using prices <= t
    turning_points: tuple[TurningPoint, ...]


def date_bear_markets(
    prices: np.ndarray | pd.Series, decline: float = BEAR_DECLINE, rise: float = BULL_RISE
) -> Dating:
    """Date bull and bear phases in a price series.

    Bear months are those after a confirmed peak up to and including the
    subsequent trough. A bear phase still open at the end of the history is
    labeled bear through the last observation.
    """
    p = np.asarray(prices, dtype=float)
    if p.ndim != 1 or len(p) == 0:
        raise ValueError("prices must be a non-empty 1-d array")
    if not np.all(np.isfinite(p)) or np.any(p <= 0):
        raise ValueError("prices must be finite and positive")
    if not (0 < decline < 1 and rise > 0):
        raise ValueError("thresholds must satisfy 0 < decline < 1 and rise > 0")

    n = len(p)
    state = np.zeros(n, dtype=int)
    turns: list[TurningPoint] = []
    in_bear = False
    extreme, extreme_i = p[0], 0
    for t in range(1, n):
        if not in_bear:
            if p[t] > extreme:
                extreme, extreme_i = p[t], t
            elif p[t] <= (1 - decline) * extreme:
                turns.append(TurningPoint("peak", extreme_i, t))
                in_bear = True
                extreme, extreme_i = p[t], t
        else:
            if p[t] < extreme:
                extreme, extreme_i = p[t], t
            elif p[t] >= (1 + rise) * extreme:
                turns.append(TurningPoint("trough", extreme_i, t))
                in_bear = False
                extreme, extreme_i = p[t], t
        state[t] = int(in_bear)

    labels = np.zeros(n, dtype=int)
    for i, tp in enumerate(turns):
        if tp.kind != "peak":
            continue
        end = turns[i + 1].index if i + 1 < len(turns) else n - 1
        labels[tp.index + 1 : end + 1] = 1
    return Dating(labels=labels, realtime_state=state, turning_points=tuple(turns))


def label_series(prices: pd.Series, **kwargs: float) -> pd.DataFrame:
    """Ex-post bear labels and the real-time bear state as a dated frame."""
    dating = date_bear_markets(prices.to_numpy(), **kwargs)
    return pd.DataFrame(
        {"bear": dating.labels, "bear_now": dating.realtime_state}, index=prices.index
    )


def vintage_labels(prices: pd.Series, asof: pd.Timestamp, **kwargs: float) -> pd.Series:
    """Labels a researcher could assign at `asof`, dating only prices through `asof`."""
    history = prices.loc[:asof]
    return pd.Series(date_bear_markets(history.to_numpy(), **kwargs).labels, index=history.index)


def episodes(prices: pd.Series, **kwargs: float) -> pd.DataFrame:
    """One row per dated bear market: peak, trough, length and peak-to-trough decline."""
    dating = date_bear_markets(prices.to_numpy(), **kwargs)
    idx = prices.index
    rows = []
    turns = dating.turning_points
    for i, tp in enumerate(turns):
        if tp.kind != "peak":
            continue
        trough = turns[i + 1] if i + 1 < len(turns) else None
        end = trough.index if trough else len(prices) - 1
        rows.append(
            {
                "peak": idx[tp.index],
                "trough": idx[end],
                "confirmed": idx[tp.confirmed_at],
                "months": end - tp.index,
                "decline_pct": 100 * (prices.iloc[end] / prices.iloc[tp.index] - 1),
                "complete": trough is not None,
            }
        )
    return pd.DataFrame(rows)
