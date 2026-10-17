"""Loading, validating and auditing the archived Shiller extract (`one45.csv`)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from psm.config import DATA_FILE

# What each archived column contains, recovered from the values themselves and
# from Shiller's "U.S. Stock Markets and CAPE Ratio" workbook layout.
COLUMN_DESCRIPTIONS: dict[str, str] = {
    "spprice": "S&P Composite, monthly average of daily closes (nominal)",
    "dividend": "Dividends per share, annualized (nominal, interpolated)",
    "earnings": "Earnings per share, annualized (nominal, interpolated)",
    "infl": "Consumer price index level (not an inflation rate)",
    "lrir10": "Long-term interest rate, 10-year Treasury yield (percent)",
    "realprice": "Real S&P Composite price (deflated by same-month CPI)",
    "realpricelag": "Archived 'lag': equals NEXT month's real price (a lead)",
    "realpricelag2": "Archived 'lag 2': real price two months ahead",
    "realpricelag3": "Archived 'lag 3': real price three months ahead",
    "realpricelag4": "Archived 'lag 4': real price four months ahead",
    "realdividend": "Real dividends, annualized",
    "realtotalreturn": "Real total return price index",
    "realearnings": "Real earnings, annualized",
    "realtrscaledearnings": "Real total-return-scaled earnings",
    "CAPE": "Cyclically adjusted price-earnings ratio",
    "TRCAPE": "Total-return CAPE",
    "excessCAPE": "Excess CAPE yield (decimal)",
    "bond": "Gross monthly total return on 10-year Treasury bonds",
    "realbond": "Real total bond return index",
    "dp": "Price-to-dividend ratio (despite the name)",
    "dy": "Dividend yield, percent",
    "ep": "Price-to-earnings ratio (despite the name)",
    "de": "Dividend payout ratio, percent",
}

ARCHIVED_LEAD_COLUMNS = ("realpricelag", "realpricelag2", "realpricelag3", "realpricelag4")


@dataclass(frozen=True)
class RawData:
    """The validated monthly panel plus a record of rows that were dropped."""

    frame: pd.DataFrame
    dropped_rows: tuple[str, ...]


def load_raw(path: Path = DATA_FILE) -> RawData:
    """Read `one45.csv`, keep dated rows, and return a month-indexed numeric frame.

    The archived file ends with a free-text footnote row ("Mar price is Mar 1st
    close ...") that is not an observation; it is dropped and recorded.
    """
    raw = pd.read_csv(path, dtype=str)
    dates = pd.to_datetime(raw["date"], format="%m/%d/%Y", errors="coerce")
    dropped = tuple(
        ",".join(str(v) for v in row if isinstance(v, str))
        for row in raw.loc[dates.isna()].itertuples(index=False)
    )
    frame = raw.loc[dates.notna()].drop(columns="date")
    frame.index = pd.DatetimeIndex(dates[dates.notna()], name="date")
    frame = frame.apply(pd.to_numeric, errors="raise")
    validate_monthly_index(frame.index)
    return RawData(frame=frame, dropped_rows=dropped)


def validate_monthly_index(index: pd.DatetimeIndex) -> None:
    """Raise if the index is not a gap-free, strictly increasing month-start sequence."""
    if not index.is_monotonic_increasing or index.has_duplicates:
        raise ValueError("Dates must be unique and increasing")
    if not (index.day == 1).all():
        raise ValueError("Dates must be month starts")
    expected = pd.date_range(index[0], index[-1], freq="MS")
    if len(expected) != len(index) or not (expected == index).all():
        raise ValueError("Monthly dates must have no gaps")


def audit_archived_leads(frame: pd.DataFrame, atol: float = 0.01) -> pd.DataFrame:
    """Compare each archived 'lag' column with past and future real prices.

    Returns one row per archived column with the share of comparable rows that
    match the real price k months back and k months ahead.
    """
    rows = []
    price = frame["realprice"]
    for k, column in enumerate(ARCHIVED_LEAD_COLUMNS, start=1):
        archived = frame[column]
        future = price.shift(-k)
        past = price.shift(k)
        fut_ok = archived.notna() & future.notna()
        past_ok = archived.notna() & past.notna()
        rows.append(
            {
                "column": column,
                "k": k,
                "pairs_future": int(fut_ok.sum()),
                "match_future": int((np.abs(archived - future)[fut_ok] <= atol).sum()),
                "pairs_past": int(past_ok.sum()),
                "match_past": int((np.abs(archived - past)[past_ok] <= atol).sum()),
            }
        )
    out = pd.DataFrame(rows)
    out["share_future"] = out["match_future"] / out["pairs_future"]
    out["share_past"] = out["match_past"] / out["pairs_past"]
    return out
