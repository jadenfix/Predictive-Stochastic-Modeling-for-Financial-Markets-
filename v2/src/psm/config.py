"""Project-wide constants: paths, samples, horizons and timing assumptions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

V2_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = V2_ROOT.parent
DATA_FILE = REPO_ROOT / "one45.csv"
ARCHIVED_REPORTED_FILE = V2_ROOT / "data" / "archived_reported.csv"
OUTPUT_DIR = V2_ROOT / "output"

SEED = 20250201

# Forecast horizons in months.
HORIZONS: tuple[int, ...] = (1, 3, 6, 12)

# Bear-market dating thresholds (fractional moves in the real price index).
BEAR_DECLINE = 0.20
BULL_RISE = 0.20

# Publication lags, in months, applied before a series may enter a predictor.
# A forecast is made at the end of month t. Monthly-average prices and bond
# yields for month t are known then; CPI for month t is released in the middle
# of month t + 1; Shiller's monthly dividends and earnings are interpolated
# from quarterly reports that arrive one to two months after quarter end.
CPI_LAG = 1
FUNDAMENTALS_LAG = 6


@dataclass(frozen=True)
class Sample:
    """A closed monthly date range."""

    start: pd.Timestamp
    end: pd.Timestamp

    def label(self) -> str:
        return f"{self.start:%Y:%m}-{self.end:%Y:%m}"


# The archived thesis sample (January 1960 to December 2023).
THESIS_SAMPLE = Sample(pd.Timestamp("1960-01-01"), pd.Timestamp("2023-12-01"))
# The full span used for dating and for the expanding-window forecasts.
FULL_SAMPLE = Sample(pd.Timestamp("1900-01-01"), pd.Timestamp("2023-12-01"))
# First forecast origin for the out-of-sample evaluation of bear-market dates.
OOS_FIRST_ORIGIN = pd.Timestamp("1960-01-01")
