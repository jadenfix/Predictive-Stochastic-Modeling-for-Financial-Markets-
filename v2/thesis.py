#!/usr/bin/env python3
"""Predictive Stochastic Modeling for Financial Markets, revised edition: the complete pipeline.

One script reproduces every number, table and figure of the paper and compiles it:

    uv run python thesis.py            # same as `all`
    uv run python thesis.py data       # one or more stages, in the order given
    uv run python thesis.py all --keep # do not wipe output/ first

Stages, in order:

    data      download (or reuse) Shiller's workbook, verify its SHA-256, parse it, compare it
              with the archived extract one45.csv, build past-only predictors and date bear markets
    models    in-sample models: Markov-switching regimes (fixed and time-varying transitions),
              alternative regime specifications, logit/probit with Newey-West errors, the archived
              specification corrected and replicated
    forecast  real-time expanding-window forecasts: baselines, regime models, logits, elastic net,
              gradient boosting, equal-weight and dynamic model averaging combinations
    robust    alternative dating rules and windows, subperiods, block bootstrap, Murphy decomposition,
              Giacomini-White, model confidence set and superior-predictive-ability tests
    tables    Typst and Markdown tables and output/numbers.json (every number the paper quotes)
    figures   PNG and SVG figures
    paper     compile paper/main.typ to PDF

Each stage stores its results in .cache/<stage>.pkl so later stages can run on their own. The
pipeline is deterministic: fixed starting values, fixed seeds, single-process execution.

Timing convention: a forecast is made at the end of month t. Monthly-average prices and the
10-year yield for month t are known then; CPI enters with a one-month lag, dividends and earnings
with a six-month lag. Nothing dated after t enters a forecast made at t (see tests/).
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import pickle
import shutil
import sys
import time
import urllib.request
import warnings
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import statsmodels.api as sm  # noqa: E402
import typst  # noqa: E402
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter  # noqa: E402
from scipy import stats  # noqa: E402
from sklearn.ensemble import HistGradientBoostingClassifier  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from statsmodels.othermod.betareg import BetaModel  # noqa: E402
from statsmodels.tsa.regime_switching.markov_autoregression import MarkovAutoregression  # noqa: E402
from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression  # noqa: E402

# =============================================================================================
# 1. Configuration
# =============================================================================================

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
RAW_DIR = ROOT / "data" / "raw"
OUTPUT = ROOT / "output"
CACHE = ROOT / ".cache"
PAPER_SOURCE = ROOT / "paper" / "main.typ"
PAPER_PDF = ROOT / "paper" / "Predictive_Stochastic_Modeling_v2.pdf"

# Primary source: Robert Shiller's "U.S. Stock Markets 1871-Present and CAPE Ratio" workbook,
# linked from https://shillerdata.com (the data page of econ.yale.edu/~shiller/data.htm points
# there). The pinned file was downloaded on 2026-10-18 (UTC); the server reported it as last
# modified on 2026-10-06. A refreshed workbook will fail the hash check by design.
SHILLER_PAGE = "https://shillerdata.com/"
SHILLER_URL = (
    "https://img1.wsimg.com/blobby/go/e5e77e0b-59d1-44d9-ab25-4763ac982e53/downloads/"
    "1449043e-a1ed-4e2e-8e9c-7b9a2a064493/ie_data.xls?ver=1791297298731"
)
SHILLER_FILE = RAW_DIR / "ie_data.xls"
SHILLER_SHA256 = "98a54927942e842ec07ffe73000998e793953708c345b6b27bb363e9ada8366a"
SHILLER_DOWNLOADED = "18 October 2026"  # 03:53 UTC
SHILLER_LAST_MODIFIED = "6 October 2026"
SHILLER_SHEET = "Data"

# Archived inputs of the award version (used only for the comparison and the replication).
ONE45_FILE = REPO / "one45.csv"
ARCHIVED_REPORTED_FILE = ROOT / "data" / "archived_reported.csv"

SEED = 20250201
HORIZONS: tuple[int, ...] = (1, 3, 6, 12)
BEAR_DECLINE = 0.20  # a fall of 20% from a peak confirms a bear market
BULL_RISE = 0.20  # a rise of 20% from a trough ends it
CPI_LAG = 1  # months
FUNDAMENTALS_LAG = 6  # months, dividends and earnings
MAIN_START = pd.Timestamp("1960-01-01")  # main in-sample period and first forecast origin
SPLIT = pd.Timestamp("1990-01-01")  # subsample split
CRISIS = (pd.Timestamp("2007-10-01"), pd.Timestamp("2009-06-01"))
ROLLING_WINDOW = 360  # months
BLOCK = 24  # bootstrap block length, months
BOOT_REPS = 2000
LOG_LOSS_FLOOR = 1e-3
DMA_ALPHA = 0.99  # forgetting factor of dynamic model averaging
DMA_ALPHAS = (0.95, 0.99, 1.0)  # sensitivity (1.0 is recursive Bayesian model averaging)
MURPHY_BINS = 10
ML_VALIDATION = 120  # months of training origins held out for hyperparameter selection
ENET_GRID = tuple(itertools.product((0.01, 0.1, 1.0, 10.0), (0.1, 0.5, 0.9)))  # (C, l1_ratio)
GBT_GRID = tuple(itertools.product((2, 3), (100, 300)))  # (max_depth, max_iter)
GBT_LEARNING_RATE = 0.05
TVTP_KEYS = ("log_dy", "infl_yoy", "vol_12", "drawdown")

_START = time.time()


def log(msg: str) -> None:
    """Progress message with elapsed wall time."""
    print(f"[{time.time() - _START:7.1f}s] {msg}", flush=True)


def months_between(a: pd.Timestamp, b: pd.Timestamp) -> int:
    return (b.year - a.year) * 12 + b.month - a.month


MINUS = "−"


def fmt(x: float | None, digits: int = 3) -> str:
    """Fixed-decimal formatting with a true minus sign; blank for missing values."""
    if x is None or (isinstance(x, (float, np.floating)) and not np.isfinite(x)):
        return ""
    s = f"{float(x):,.{digits}f}"
    if s.startswith("-"):
        s = s[1:] if float(s.replace(",", "")) == 0 else MINUS + s[1:]
    return s


def fmt_p(p: float) -> str:
    """p-values to three decimals, with values below 0.001 shown as '<0.001'."""
    if p is None or not np.isfinite(p):
        return ""
    return "<0.001" if p < 0.001 else fmt(p, 3)


def stars(p: float) -> str:
    if p is None or not np.isfinite(p):
        return ""
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else ""


def month_label(ts: pd.Timestamp) -> str:
    return f"{ts:%B %Y}"


# =============================================================================================
# 2. Data: Shiller's workbook, parsing, validation, comparison with the archived extract
# =============================================================================================

# Columns of the "Data" sheet used here: position -> (name, text expected in header row 8).
SHILLER_COLUMNS: dict[int, tuple[str, str]] = {
    0: ("date", "Date"),
    1: ("price", "P"),
    2: ("dividend", "D"),
    3: ("earnings", "E"),
    4: ("cpi", "CPI"),
    5: ("date_fraction", "Fraction"),
    6: ("gs10", "GS10"),
    7: ("real_price", "Price"),
    9: ("real_tr_price", "Price"),
    11: ("real_trs_earnings", "Earnings"),
    12: ("cape", "CAPE"),
    14: ("tr_cape", "TR CAPE"),
    17: ("bond_return", "Returns"),
    18: ("real_bond", "Returns"),
}
SHILLER_HEADER_ROW = 7  # zero-based row holding the last line of the column headings
SHILLER_DESCRIPTIONS: dict[str, str] = {
    "date": "Month as a fractional year with two decimals (1871.01 = January, 1871.1 = October)",
    "date_fraction": "Shiller's mid-month date fraction, used to validate the parsed months",
    "price": "S&P Composite, monthly average of daily closes",
    "dividend": "Dividends per share, annualized (interpolated from quarterly; annual before 1926)",
    "earnings": "Earnings per share, annualized (interpolated from quarterly; annual before 1926)",
    "cpi": "Consumer price index",
    "gs10": "Long-term interest rate (10-year Treasury yield from 1953), percent",
    "real_price": "Real price, deflated by same-month CPI",
    "real_tr_price": "Real total-return price index",
    "real_trs_earnings": "Real total-return-scaled earnings",
    "cape": "Cyclically adjusted price-earnings ratio",
    "tr_cape": "Total-return CAPE",
    "bond_return": "Gross return on 10-year Treasury bonds from month t to t + 1",
    "real_bond": "Real total return index of 10-year Treasury bonds",
}
# Series that must all be reported for a month to belong to the sample.
CORE_SERIES = ("price", "dividend", "earnings", "cpi", "gs10")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_shiller(path: Path = SHILLER_FILE, url: str = SHILLER_URL, expected: str = SHILLER_SHA256) -> Path:
    """Return the pinned workbook, downloading it first if it is not on disk; verify its SHA-256."""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        log(f"downloading {url}")
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (thesis.py)"})
        with urllib.request.urlopen(request, timeout=60) as response:
            path.write_bytes(response.read())
    actual = sha256(path)
    if actual != expected:
        raise RuntimeError(
            f"{path} has SHA-256 {actual}, expected {expected}. Shiller updates the workbook "
            "regularly; to adopt a new vintage, update SHILLER_URL, SHILLER_SHA256 and the dates."
        )
    return path


def parse_shiller_date(value: float) -> pd.Timestamp:
    """Shiller writes months as fractional years with two decimals: 1871.01 is January 1871 and
    1871.1 (that is, 1871.10) is October."""
    text = f"{float(value):.2f}"
    year, month = int(text[:-3]), int(text[-2:])
    if not 1 <= month <= 12:
        raise ValueError(f"bad Shiller date {value!r}")
    return pd.Timestamp(year=year, month=month, day=1)


def validate_monthly_index(index: pd.DatetimeIndex) -> None:
    """Raise if the index is not a gap-free, strictly increasing month-start sequence."""
    if not index.is_monotonic_increasing or index.has_duplicates:
        raise ValueError("dates must be unique and increasing")
    if not (index.day == 1).all():
        raise ValueError("dates must be month starts")
    expected = pd.date_range(index[0], index[-1], freq="MS")
    if len(expected) != len(index) or not (expected == index).all():
        raise ValueError("monthly dates must have no gaps")


@dataclass(frozen=True)
class ShillerData:
    """The parsed workbook: every dated row, plus the sample used for the analysis."""

    frame: pd.DataFrame  # all dated rows, blank cells as NaN
    end: pd.Timestamp  # last month in which every core series is reported
    footnotes: tuple[str, ...]  # non-data rows below the table

    @property
    def panel(self) -> pd.DataFrame:
        return self.frame.loc[: self.end]


def parse_shiller(path: Path) -> ShillerData:
    """Parse the "Data" sheet: check the headings, keep dated rows, convert fractional dates."""
    sheet = pd.read_excel(path, sheet_name=SHILLER_SHEET, header=None, engine="xlrd")
    header = sheet.iloc[SHILLER_HEADER_ROW]
    for pos, (name, text) in SHILLER_COLUMNS.items():
        if text not in str(header[pos]):
            raise ValueError(f"column {pos} ({name}): expected heading containing {text!r}, got {header[pos]!r}")
    body = sheet.iloc[SHILLER_HEADER_ROW + 1 :]
    dated = pd.to_numeric(body[0], errors="coerce").notna()
    footnotes = tuple(
        "; ".join(str(v) for v in row if isinstance(v, str)) for row in body.loc[~dated].itertuples(index=False)
    )
    body = body.loc[dated]
    frame = pd.DataFrame(
        {name: pd.to_numeric(body[pos], errors="coerce") for pos, (name, _) in SHILLER_COLUMNS.items()}
    )
    index = pd.DatetimeIndex([parse_shiller_date(v) for v in frame.pop("date")], name="date")
    frame.index = index
    validate_monthly_index(index)
    # Shiller's own fractional date (year + (month - 0.5) / 12) must agree with the parsed month.
    implied = index.year + (index.month - 0.5) / 12
    if np.max(np.abs(frame.pop("date_fraction").to_numpy() - implied)) > 1e-6:
        raise ValueError("parsed months disagree with Shiller's date fraction")
    # The monthly bond return in row t runs from t to t + 1 (it uses next month's yield), so it is
    # never used directly; the real bond index at t compounds earlier rows' returns only.
    implied_index = frame["real_bond"].shift(1) * frame["bond_return"].shift(1) * frame["cpi"].shift(1) / frame["cpi"]
    gap = (frame["real_bond"] / implied_index - 1).dropna()
    if np.max(np.abs(gap)) > 1e-9:
        raise ValueError("real bond index is not the compounded lagged bond return")
    complete = frame[list(CORE_SERIES)].notna().all(axis=1)
    end = complete[complete].index[-1]
    if not complete.loc[:end].all():
        raise ValueError("core series have gaps before the last complete month")
    return ShillerData(frame=frame, end=end, footnotes=footnotes)


def load_shiller() -> ShillerData:
    return parse_shiller(fetch_shiller())


# --- the archived extract of the award version ------------------------------------------------

ARCHIVED_LEAD_COLUMNS = ("realpricelag", "realpricelag2", "realpricelag3", "realpricelag4")


def load_one45(path: Path = ONE45_FILE) -> pd.DataFrame:
    """Read `one45.csv` (the award version's data), dropping its trailing footnote row."""
    raw = pd.read_csv(path, dtype=str)
    dates = pd.to_datetime(raw["date"], format="%m/%d/%Y", errors="coerce")
    frame = raw.loc[dates.notna()].drop(columns="date").apply(pd.to_numeric, errors="raise")
    frame.index = pd.DatetimeIndex(dates[dates.notna()], name="date")
    validate_monthly_index(frame.index)
    return frame


def audit_archived_leads(frame: pd.DataFrame, atol: float = 0.01) -> pd.DataFrame:
    """Compare each archived 'lag' column with the real price k months back and k months ahead."""
    rows = []
    price = frame["realprice"]
    for k, column in enumerate(ARCHIVED_LEAD_COLUMNS, start=1):
        archived = frame[column]
        future, past = price.shift(-k), price.shift(k)
        fut_ok, past_ok = archived.notna() & future.notna(), archived.notna() & past.notna()
        rows.append({
            "column": column,
            "k": k,
            "pairs_future": int(fut_ok.sum()),
            "match_future": int((np.abs(archived - future)[fut_ok] <= atol).sum()),
            "pairs_past": int(past_ok.sum()),
            "match_past": int((np.abs(archived - past)[past_ok] <= atol).sum()),
        })
    return pd.DataFrame(rows)


# (one45 column, Shiller column, label, comparison): "level" series are compared after rounding
# Shiller's value to the two decimals of the archived file; "scaled" (real) series are expressed
# in different base-month dollars, so each is first rescaled by its median ratio.
ONE45_COMPARISON: tuple[tuple[str, str, str, str], ...] = (
    ("spprice", "price", "S&P Composite price", "level"),
    ("dividend", "dividend", "Dividends", "level"),
    ("earnings", "earnings", "Earnings", "level"),
    ("infl", "cpi", "CPI", "level"),
    ("lrir10", "gs10", "Long-term interest rate", "level"),
    ("CAPE", "cape", "CAPE", "level"),
    ("TRCAPE", "tr_cape", "Total-return CAPE", "level"),
    ("realprice", "real_price", "Real price (rescaled)", "scaled"),
    ("realtrscaledearnings", "real_trs_earnings", "Real TR-scaled earnings (rescaled)", "scaled"),
)


def compare_with_one45(shiller: pd.DataFrame, one45: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Month-by-month comparison of the archived extract with the current Shiller workbook.

    Returns a summary per series and the list of months whose values differ beyond rounding.
    """
    rows, details = [], []
    for old_col, new_col, label, kind in ONE45_COMPARISON:
        pair = one45[[old_col]].set_axis(["old"], axis=1).join(shiller[[new_col]].set_axis(["new"], axis=1), how="inner").dropna()
        old, new = pair["old"], pair["new"]
        if kind == "level":
            differs = (old - new.round(2)).abs() > 0.0101
            ref = new
        else:
            ref = new * float((old / new).median())
            differs = (100 * (old / ref - 1)).abs() > 0.05  # beyond the rounding of the archived values
        rel = 100 * (old / ref - 1)
        changed = rel[differs]
        rows.append({
            "series": label,
            "months": len(pair),
            "first": pair.index[0],
            "last": pair.index[-1],
            "n_differ": int(differs.sum()),
            "max_abs_rel_pct": float(changed.abs().max()) if len(changed) else 0.0,
            "first_differ": changed.index.min() if len(changed) else pd.NaT,
            "last_differ": changed.index.max() if len(changed) else pd.NaT,
        })
        details += [
            {"series": label, "month": d, "one45": float(old[d]), "shiller": float(ref[d]), "rel_pct": float(rel[d])}
            for d in changed.index
        ]
    return pd.DataFrame(rows), pd.DataFrame(details)


# =============================================================================================
# 3. Past-only predictors
# =============================================================================================


@dataclass(frozen=True)
class Feature:
    key: str
    label: str
    unit: str
    construction: str
    lag: str  # publication lag of the inputs, in months


# Monthly-change predictors mirroring the seven series of the award version (appendix only).
ORIGINAL_FEATURES: tuple[Feature, ...] = (
    Feature("infl_m", "CPI inflation, monthly", "% per month", "100 dlog CPI", "1"),
    Feature("d_rate", "Change in 10-year yield", "pp", "Monthly change", "0"),
    Feature("bond_ret", "Real bond return", "% per month", "100 dlog real bond index", "0 (CPI 1)"),
    Feature("div_growth", "Real dividend growth", "% per month", "100 dlog real dividends", "6"),
    Feature("tr_ret", "Real total return", "% per month", "Price return plus D/12P, less inflation", "0 (D 6, CPI 1)"),
    Feature("trse_growth", "TR-scaled earnings growth", "% per month", "100 dlog real TR-scaled earnings", "6"),
    Feature("d_trcape", "Change in log TR-CAPE", "% per month", "100 dlog TR price / 10-yr mean earnings", "0 (E 6)"),
)
# State predictors of the main bear-market models.
FORECAST_FEATURES: tuple[Feature, ...] = (
    Feature("log_dy", "Log dividend yield", "log points", "log(D / P)", "0 (D 6)"),
    Feature("log_cape", "Log CAPE", "log points", "log(P / 10-yr mean real earnings)", "0 (E 6)"),
    Feature("infl_yoy", "CPI inflation, 12-month", "%", "100 x 12-month dlog CPI", "1"),
    Feature("d_rate_12", "12-month change in 10-year yield", "pp", "12-month change", "0"),
    Feature("mom_12", "12-month real price change", "%", "100 x 12-month dlog real price", "0 (CPI 1)"),
    Feature("vol_12", "12-month realized volatility", "% annualized", "sd of monthly real returns x sqrt(12)", "0 (CPI 1)"),
)
# Additional state predictors (predictor experiments, rich machine-learning set).
EXTRA_FEATURES: tuple[Feature, ...] = (
    Feature("ecy", "Excess CAPE yield", "%", "100 E10/P less (yield less 10-yr inflation)", "0 (E 6, CPI 1)"),
    Feature("log_payout", "Log payout ratio", "log points", "log(D / E)", "6"),
    Feature("earn_growth_12", "12-month real earnings growth", "%", "100 x 12-month dlog real earnings", "6"),
    Feature("rate_level", "10-year Treasury yield", "%", "Level", "0"),
    Feature("drawdown", "Drawdown from 12-month high", "%", "100 x log(P / 12-month high)", "0 (CPI 1)"),
)
ORIGINAL_KEYS = [f.key for f in ORIGINAL_FEATURES]
FORECAST_KEYS = [f.key for f in FORECAST_FEATURES]
EXTRA_KEYS = [f.key for f in EXTRA_FEATURES]
ALL_KEYS = FORECAST_KEYS + EXTRA_KEYS
FEATURE_LABELS: dict[str, str] = {f.key: f.label for f in ORIGINAL_FEATURES + FORECAST_FEATURES + EXTRA_FEATURES}
FEATURE_LABELS["bear_now"] = "Real-time bear state"

# The only workbook columns the predictors may read.
FEATURE_INPUTS = ("price", "dividend", "earnings", "cpi", "gs10", "real_trs_earnings", "real_bond")


def real_price_index(panel: pd.DataFrame) -> pd.Series:
    """Real S&P 500 price observable at the end of month t: P_t / CPI_{t-1}.

    Shiller deflates by same-month CPI, which is published only in month t + 1. The index is in
    units of the price per CPI point; only its ratios matter for dating and returns.
    """
    return (panel["price"] / panel["cpi"].shift(CPI_LAG)).rename("real_price")


def real_returns(panel: pd.DataFrame) -> pd.Series:
    """Monthly real price return in percent: 100 times the log change of the observable index."""
    return (100 * np.log(real_price_index(panel)).diff()).rename("real_return")


def _ten_year_mean(series: pd.Series) -> pd.Series:
    return series.rolling(120, min_periods=120).mean()


def build_features(panel: pd.DataFrame) -> pd.DataFrame:
    """All predictors, indexed by the forecast origin t, using only data published by t."""
    missing = set(FEATURE_INPUTS) - set(panel.columns)
    if missing:
        raise KeyError(f"missing columns: {sorted(missing)}")
    cpi = panel["cpi"]
    cpi_avail = cpi.shift(CPI_LAG)
    log_cpi_avail = np.log(cpi_avail)
    infl_m = 100 * log_cpi_avail.diff()
    price = panel["price"]
    log_real_price = np.log(real_price_index(panel))
    monthly_real = 100 * log_real_price.diff()
    dividend_avail = panel["dividend"].shift(FUNDAMENTALS_LAG)
    earnings_avail = panel["earnings"].shift(FUNDAMENTALS_LAG)
    real_div_avail = (panel["dividend"] / cpi).shift(FUNDAMENTALS_LAG)
    real_earn_avail = (panel["earnings"] / cpi).shift(FUNDAMENTALS_LAG)
    trse_avail = panel["real_trs_earnings"].shift(FUNDAMENTALS_LAG)
    # Shiller's real bond index at t compounds returns through t and divides by CPI_t; multiplying
    # by CPI_t / CPI_{t-1} deflates the same nominal index by the CPI available at t instead.
    real_bond = panel["real_bond"] * cpi / cpi_avail
    # Total return from the price and the lagged dividend, deflated by lagged CPI.
    tr_ret = 100 * np.log((price + dividend_avail / 12) / price.shift(1)) - infl_m
    tr_index = np.exp(tr_ret.fillna(0).cumsum() / 100).where(tr_ret.notna())
    log_trcape = np.log(tr_index) - np.log(_ten_year_mean(trse_avail))
    log_cape = log_real_price - np.log(_ten_year_mean(real_earn_avail))
    return pd.DataFrame(
        {
            "infl_m": infl_m,
            "d_rate": panel["gs10"].diff(),
            "bond_ret": 100 * np.log(real_bond).diff(),
            "div_growth": 100 * np.log(real_div_avail).diff(),
            "tr_ret": tr_ret,
            "trse_growth": 100 * np.log(trse_avail).diff(),
            "d_trcape": 100 * log_trcape.diff(),
            "log_dy": np.log(dividend_avail / price),
            "log_cape": log_cape,
            "infl_yoy": 100 * (log_cpi_avail - log_cpi_avail.shift(12)),
            "d_rate_12": panel["gs10"].diff(12),
            "mom_12": 100 * (log_real_price - log_real_price.shift(12)),
            "vol_12": monthly_real.rolling(12, min_periods=12).std() * np.sqrt(12),
            "ecy": 100 * np.exp(-log_cape) - (panel["gs10"] - 10 * (log_cpi_avail - log_cpi_avail.shift(120))),
            "log_payout": np.log(dividend_avail / earnings_avail),
            "earn_growth_12": 100 * (np.log(real_earn_avail) - np.log(real_earn_avail.shift(12))),
            "rate_level": panel["gs10"],
            "drawdown": 100 * (log_real_price - log_real_price.rolling(12, min_periods=12).max()),
        },
        index=panel.index,
    )


def standardize(frame: pd.DataFrame) -> pd.DataFrame:
    return (frame - frame.mean()) / frame.std(ddof=0)


# =============================================================================================
# 4. Dating bull and bear markets
# =============================================================================================


@dataclass(frozen=True)
class TurningPoint:
    kind: str  # "peak" or "trough"
    index: int  # position of the extreme price
    confirmed_at: int  # position at which the threshold was crossed


@dataclass(frozen=True)
class Dating:
    labels: np.ndarray  # 1 = bear month (ex post, backdated to the month after the peak)
    realtime_state: np.ndarray  # 1 = in a confirmed bear market at t, using prices through t
    turning_points: tuple[TurningPoint, ...]


def date_bear_markets(prices: np.ndarray | pd.Series, decline: float = BEAR_DECLINE, rise: float = BULL_RISE) -> Dating:
    """Threshold dating in the spirit of Lunde and Timmermann (2004).

    In a bull state the running maximum is a candidate peak; a fall of `decline` below it confirms
    the peak and starts a bear market in the following month. In a bear state the running minimum
    is a candidate trough; a rise of `rise` above it confirms the trough, which ends the bear
    market. The state machine is causal; the backdated labels are not, and serve only as targets.
    A bear market still open at the end of the history is labeled through the last month.
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
        if tp.kind == "peak":
            end = turns[i + 1].index if i + 1 < len(turns) else n - 1
            labels[tp.index + 1 : end + 1] = 1
    return Dating(labels=labels, realtime_state=state, turning_points=tuple(turns))


def label_series(prices: pd.Series, decline: float = BEAR_DECLINE, rise: float = BULL_RISE) -> pd.DataFrame:
    """Ex-post bear labels (`bear`) and the real-time state (`bear_now`) as a dated frame."""
    d = date_bear_markets(prices.to_numpy(), decline, rise)
    return pd.DataFrame({"bear": d.labels, "bear_now": d.realtime_state}, index=prices.index)


def episodes(prices: pd.Series, decline: float = BEAR_DECLINE, rise: float = BULL_RISE) -> pd.DataFrame:
    """One row per dated bear market: peak, trough, confirmation, length and decline."""
    d = date_bear_markets(prices.to_numpy(), decline, rise)
    idx, turns, rows = prices.index, d.turning_points, []
    for i, tp in enumerate(turns):
        if tp.kind != "peak":
            continue
        trough = turns[i + 1] if i + 1 < len(turns) else None
        end = trough.index if trough else len(prices) - 1
        rows.append({
            "peak": idx[tp.index],
            "trough": idx[end],
            "confirmed": idx[tp.confirmed_at],
            "months": end - tp.index,
            "decline_pct": 100 * (prices.iloc[end] / prices.iloc[tp.index] - 1),
            "complete": trough is not None,
        })
    return pd.DataFrame(rows)


# =============================================================================================
# 5. Forecast evaluation and inference
# =============================================================================================


def brier(p: np.ndarray, y: np.ndarray) -> float:
    """Mean squared error of probability forecasts (Brier, 1950)."""
    return float(np.mean((np.asarray(p, dtype=float) - np.asarray(y, dtype=float)) ** 2))


def log_loss(p: np.ndarray, y: np.ndarray, floor: float = LOG_LOSS_FLOOR) -> float:
    """Mean negative log-likelihood with probabilities truncated to [floor, 1 - floor]."""
    q = np.clip(np.asarray(p, dtype=float), floor, 1 - floor)
    y = np.asarray(y, dtype=float)
    return float(-np.mean(y * np.log(q) + (1 - y) * np.log(1 - q)))


def auc(p: np.ndarray, y: np.ndarray) -> float:
    """Area under the ROC curve via the Mann-Whitney statistic (ties count one half)."""
    p, y = np.asarray(p, dtype=float), np.asarray(y).astype(bool)
    n1, n0 = y.sum(), (~y).sum()
    if n1 == 0 or n0 == 0:
        return float("nan")
    ranks = stats.rankdata(p)
    return float((ranks[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def roc_curve(p: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """False- and true-positive rates over all distinct thresholds."""
    p, y = np.asarray(p, dtype=float), np.asarray(y).astype(int)
    thresholds = np.r_[np.inf, np.unique(p)[::-1]]
    tpr = np.array([(p[y == 1] >= c).mean() for c in thresholds])
    fpr = np.array([(p[y == 0] >= c).mean() for c in thresholds])
    return fpr, tpr


def calibration(p: np.ndarray, y: np.ndarray, bins: int = 10) -> pd.DataFrame:
    """Mean forecast and observed frequency within forecast-quantile bins (ties share a bin)."""
    p, y = np.asarray(p, dtype=float), np.asarray(y, dtype=float)
    which = pd.qcut(p, bins, labels=False, duplicates="drop")
    rows = []
    for b in np.unique(which):
        mask = which == b
        rows.append({"bin": int(b), "forecast": p[mask].mean(), "observed": y[mask].mean(), "count": int(mask.sum())})
    return pd.DataFrame(rows)


def murphy_decomposition(p: np.ndarray, y: np.ndarray, bins: int = MURPHY_BINS) -> dict[str, float]:
    """Murphy (1973) partition of the Brier score: reliability - resolution + uncertainty.

    Forecasts are grouped into `bins` equal-width bins; `remainder` is the part of the Brier
    score due to variation of the forecasts within bins, which the binned partition omits.
    """
    p, y = np.asarray(p, dtype=float), np.asarray(y, dtype=float)
    which = np.clip((p * bins).astype(int), 0, bins - 1)
    n, ybar = len(p), y.mean()
    rel = res = 0.0
    for b in np.unique(which):
        mask = which == b
        rel += mask.sum() * (p[mask].mean() - y[mask].mean()) ** 2
        res += mask.sum() * (y[mask].mean() - ybar) ** 2
    rel, res, unc = rel / n, res / n, ybar * (1 - ybar)
    bs = brier(p, y)
    return {"brier": bs, "reliability": rel, "resolution": res, "uncertainty": unc,
            "remainder": bs - (rel - res + unc)}


def hac_variance(d: np.ndarray, lags: int) -> float:
    """Bartlett-kernel long-run variance of a series (Newey and West, 1987)."""
    d = np.asarray(d, dtype=float) - np.mean(d)
    n = len(d)
    var = d @ d / n
    for k in range(1, lags + 1):
        var += 2 * (1 - k / (lags + 1)) * (d[k:] @ d[:-k]) / n
    return float(var)


def diebold_mariano(loss_model: np.ndarray, loss_ref: np.ndarray, horizon: int, lags: int | None = None) -> tuple[float, float]:
    """Diebold-Mariano (1995) test with the Harvey-Leybourne-Newbold (1997) correction.

    Returns (statistic, one-sided p-value) for H1: the model has lower expected loss than the
    reference. Bartlett HAC variance with `lags` lags, by default the conventional max(h - 1, 1).
    """
    d = np.asarray(loss_model) - np.asarray(loss_ref)
    n = len(d)
    var = hac_variance(d, max(horizon - 1, 1) if lags is None else lags)
    if var <= 0:
        return float("nan"), float("nan")
    dm = d.mean() / np.sqrt(var / n)
    stat = float(dm * np.sqrt((n + 1 - 2 * horizon + horizon * (horizon - 1) / n) / n))
    return stat, float(stats.t.cdf(stat, df=n - 1))


def clark_west(actual: np.ndarray, pred_restricted: np.ndarray, pred_unrestricted: np.ndarray, horizon: int) -> tuple[float, float]:
    """Clark-West (2007) MSPE-adjusted test for nested models; one-sided p-value for H1: the
    unrestricted model is more accurate."""
    e1 = np.asarray(actual) - np.asarray(pred_restricted)
    e2 = np.asarray(actual) - np.asarray(pred_unrestricted)
    f = e1**2 - (e2**2 - (np.asarray(pred_restricted) - np.asarray(pred_unrestricted)) ** 2)
    var = hac_variance(f, max(horizon - 1, 1))
    if var <= 0:
        return float("nan"), float("nan")
    stat = float(f.mean() / np.sqrt(var / len(f)))
    return stat, float(1 - stats.norm.cdf(stat))


def giacomini_white(loss_diff: np.ndarray, instruments: np.ndarray, lags: int) -> tuple[float, float]:
    """Giacomini-White (2006) test of conditional predictive ability.

    `loss_diff` is d_{t+h} = loss of the model minus loss of the benchmark for forecasts made at
    t, and `instruments` (n x q) holds test functions known at t. Under the null of equal
    conditional accuracy, E[d_{t+h} | instruments] = 0, the Wald statistic n Zbar' S^{-1} Zbar is
    chi-squared with q degrees of freedom. S is estimated under the null (uncentered) with
    Bartlett weights on `lags` autocovariances. Returns (statistic, p-value).
    """
    z = np.asarray(instruments, dtype=float) * np.asarray(loss_diff, dtype=float)[:, None]
    n, q = z.shape
    zbar = z.mean(axis=0)
    s = z.T @ z / n
    for k in range(1, lags + 1):
        g = z[k:].T @ z[:-k] / n
        s += (1 - k / (lags + 1)) * (g + g.T)
    stat = float(n * zbar @ np.linalg.solve(s, zbar))
    return stat, float(1 - stats.chi2.cdf(stat, q))


def block_indices(n: int, block: int, reps: int, rng: np.random.Generator) -> np.ndarray:
    """Circular moving-block bootstrap (Künsch, 1989): (reps, n) resampled positions."""
    n_blocks = -(-n // block)
    starts = rng.integers(0, n, size=(reps, n_blocks))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]) % n
    return idx.reshape(reps, -1)[:, :n]


def bootstrap_means(values: np.ndarray, idx: np.ndarray) -> np.ndarray:
    """Means of each column of `values` (n x m) in every bootstrap draw: (reps, m)."""
    values = np.asarray(values, dtype=float)
    if values.ndim == 1:
        values = values[:, None]
    return np.column_stack([values[:, j][idx].mean(axis=1) for j in range(values.shape[1])])


def model_confidence_set(losses: np.ndarray, idx: np.ndarray) -> np.ndarray:
    """Model confidence set p-values (Hansen, Lunde and Nason, 2011), T_max statistic.

    `losses` is (n x m). At each step the statistic t_i = dbar_i. / se(dbar_i.) compares every
    surviving model's mean loss with the average of the surviving set; the model with the largest
    t_i is eliminated if max t_i is large relative to its bootstrap distribution. The MCS p-value
    of a model is the largest elimination p-value up to and including its own elimination; the
    last survivor has p-value one. The (1 - alpha) MCS is the set of models with p >= alpha.
    """
    losses = np.asarray(losses, dtype=float)
    m = losses.shape[1]
    mean = losses.mean(axis=0)
    boot = bootstrap_means(losses, idx)
    alive = list(range(m))
    pvals = np.ones(m)
    running = 0.0
    while len(alive) > 1:
        d = mean[alive] - mean[alive].mean()
        db = boot[:, alive] - boot[:, alive].mean(axis=1, keepdims=True)
        se = np.sqrt(((db - d) ** 2).mean(axis=0))
        se = np.where(se > 0, se, np.inf)
        t = d / se
        t_boot = ((db - d) / se).max(axis=1)
        p = float((t_boot >= t.max()).mean())
        worst = alive[int(np.argmax(t))]
        running = max(running, p)
        pvals[worst] = running
        alive.remove(worst)
    return pvals


def spa_test(gains: np.ndarray, idx: np.ndarray) -> dict[str, float]:
    """Hansen's (2005) test for superior predictive ability against a benchmark.

    `gains` (n x m) holds the benchmark's loss minus each model's loss. H0: no model has lower
    expected loss than the benchmark. Returns the consistent p-value (SPA_c) and the lower and
    upper bounds; the upper bound is White's (2000) Reality Check. The bootstrap uses the same
    circular blocks for all models.
    """
    d = np.asarray(gains, dtype=float)
    n = d.shape[0]
    dbar = d.mean(axis=0)
    boot = bootstrap_means(d, idx)
    omega = np.sqrt(n) * boot.std(axis=0)
    omega = np.where(omega > 0, omega, np.inf)
    t = np.sqrt(n) * dbar / omega
    stat = max(float(t.max()), 0.0)
    threshold = -np.sqrt(2 * np.log(np.log(n)))
    centers = {
        "lower": np.maximum(dbar, 0),
        "consistent": np.where(t >= threshold, dbar, 0.0),
        "upper": dbar,
    }
    out = {"stat": stat, "best": int(np.argmax(t))}
    for name, g in centers.items():
        tb = np.maximum((np.sqrt(n) * (boot - g) / omega).max(axis=1), 0)
        out[f"p_{name}"] = float((tb >= stat).mean()) if stat > 0 else 1.0
    return out


def wide_losses(fc: pd.DataFrame, horizon: int) -> tuple[pd.DataFrame, np.ndarray]:
    """Forecasts of one horizon as an origin x model frame, and the realized outcomes."""
    sub = fc[fc.horizon == horizon]
    wide = sub.pivot(index="origin", columns="model", values="p")
    y = sub.drop_duplicates("origin").set_index("origin")["y"].reindex(wide.index).to_numpy()
    return wide, y


def score(fc: pd.DataFrame, models: Iterable[str] | None = None) -> pd.DataFrame:
    """Brier score, skill relative to the unconditional frequency, log loss, AUC and one-sided
    Diebold-Mariano p-values against both baselines, per (horizon, model)."""
    rows = []
    for h in sorted(fc.horizon.unique()):
        wide, y = wide_losses(fc, h)
        loss = wide.sub(y, axis=0) ** 2
        for m in models or list(wide.columns):
            if m not in wide:
                continue
            p = wide[m].to_numpy()
            rows.append({
                "horizon": h,
                "model": m,
                "n": len(y),
                "bear_share": float(y.mean()),
                "brier": brier(p, y),
                "bss": 1 - loss[m].mean() / loss["uncond"].mean(),
                "log_loss": log_loss(p, y),
                "auc": auc(p, y),
                "p_uncond": diebold_mariano(loss[m].to_numpy(), loss["uncond"].to_numpy(), h)[1]
                if m != "uncond" else np.nan,
                "p_persist": diebold_mariano(loss[m].to_numpy(), loss["persist"].to_numpy(), h)[1]
                if m not in BASELINES and "persist" in loss else np.nan,
                "p_persist_long": diebold_mariano(loss[m].to_numpy(), loss["persist"].to_numpy(), h, BLOCK - 1)[1]
                if m not in BASELINES and "persist" in loss else np.nan,
            })
    return pd.DataFrame(rows).set_index(["horizon", "model"])


def bootstrap_skill(fc: pd.DataFrame, models: tuple[str, ...], block: int = BLOCK, reps: int = BOOT_REPS,
                    seed: int = SEED) -> pd.DataFrame:
    """Block-bootstrap distribution of Brier skill and of each model's gain over persistence.

    Target months are resampled in circular blocks, jointly for all models, which preserves the
    dependence of overlapping forecasts and the correlation between models. Returns 90%
    percentile intervals and the share of draws in which each model beats each baseline.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for h in sorted(fc.horizon.unique()):
        wide, y = wide_losses(fc, h)
        loss = wide.sub(y, axis=0) ** 2
        idx = block_indices(len(y), block, reps, rng)
        needed = sorted(set(models) | {"uncond", "persist"})
        means = dict(zip(needed, bootstrap_means(loss[needed].to_numpy(), idx).T))
        skill_persist = 1 - means["persist"] / means["uncond"]
        for m in models:
            s = 1 - means[m] / means["uncond"]
            gain = s - skill_persist
            rows.append({
                "horizon": h,
                "model": m,
                "bss": 1 - loss[m].mean() / loss["uncond"].mean(),
                "bss_lo": float(np.quantile(s, 0.05)),
                "bss_hi": float(np.quantile(s, 0.95)),
                "gain_lo": float(np.quantile(gain, 0.05)) if m != "persist" else np.nan,
                "gain_hi": float(np.quantile(gain, 0.95)) if m != "persist" else np.nan,
                "share_beats_persist": float((gain > 0).mean()) if m != "persist" else np.nan,
                "share_beats_uncond": float((s > 0).mean()),
            })
    return pd.DataFrame(rows).set_index(["horizon", "model"])


# =============================================================================================
# 6. Regression containers and predictive regressions
# =============================================================================================


@dataclass(frozen=True)
class Coef:
    estimate: float
    se: float
    pvalue: float

    def ci(self, level: float = 0.95) -> tuple[float, float]:
        z = stats.norm.ppf(0.5 + level / 2)
        return self.estimate - z * self.se, self.estimate + z * self.se


@dataclass(frozen=True)
class FitSummary:
    """Coefficients and fit statistics of one estimated equation."""

    model: str
    horizon: int
    coefs: dict[str, Coef]
    nobs: int
    start: pd.Timestamp  # first forecast origin in the estimation sample
    end: pd.Timestamp
    stats: dict[str, float] = field(default_factory=dict)


def nw_lags(nobs: int, horizon: int) -> int:
    """Newey-West truncation lag: max(h, ceil(0.75 T^(1/3)))."""
    return max(horizon, math.ceil(0.75 * nobs ** (1 / 3)))


def align(target: pd.Series, features: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Pair x_t with target_{t+h}; rows are indexed by the forecast origin t."""
    return pd.concat([target.shift(-horizon).rename("target"), features], axis=1).dropna()


def squeeze_unit(q: pd.Series | np.ndarray) -> Any:
    """Map [0, 1] into (0, 1): (q (n - 1) + 0.5) / n (Smithson and Verkuilen, 2006)."""
    n = len(q)
    return (q * (n - 1) + 0.5) / n


def _coefs(res: Any, names: list[str]) -> dict[str, Coef]:
    exog = list(res.model.exog_names)
    k = len(exog)
    params, bse, pvals = (np.asarray(a)[:k] for a in (res.params, res.bse, res.pvalues))
    pos = {name: i for i, name in enumerate(exog)}
    return {n: Coef(float(params[pos[n]]), float(bse[pos[n]]), float(pvals[pos[n]])) for n in names}


def fit_ols(target: pd.Series, features: pd.DataFrame, horizon: int, scale: float = 1.0) -> FitSummary:
    """OLS of scale * target_{t+h} on x_t with Newey-West standard errors."""
    data = align(target * scale, features, horizon)
    X = sm.add_constant(data[features.columns])
    lags = nw_lags(len(data), horizon)
    res = sm.OLS(data["target"], X).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return FitSummary("OLS", horizon, _coefs(res, ["const", *features.columns]), int(res.nobs), data.index[0],
                      data.index[-1], {"r2": float(res.rsquared), "nw_lags": lags})


def fit_beta(target: pd.Series, features: pd.DataFrame, horizon: int) -> FitSummary:
    """Beta regression (Ferrari and Cribari-Neto, 2004) of target_{t+h} on x_t, Newey-West errors."""
    data = align(squeeze_unit(target), features, horizon)
    X = sm.add_constant(data[features.columns])
    lags = nw_lags(len(data), horizon)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = BetaModel(data["target"], X).fit(disp=0, maxiter=500, cov_type="HAC", cov_kwds={"maxlags": lags})
    eta = X.to_numpy() @ np.asarray(res.params[: X.shape[1]])
    logit_y = np.log(data["target"] / (1 - data["target"]))
    return FitSummary("Beta", horizon, _coefs(res, ["const", *features.columns]), int(res.nobs), data.index[0],
                      data.index[-1], {"pseudo_r2": float(np.corrcoef(eta, logit_y)[0, 1] ** 2), "nw_lags": lags})


def fit_binary(target: pd.Series, features: pd.DataFrame, horizon: int, link: str = "logit") -> FitSummary:
    """Logit or probit of the bear indicator y_{t+h} on x_t with Newey-West standard errors."""
    data = align(target, features, horizon)
    X = sm.add_constant(data[features.columns])
    lags = nw_lags(len(data), horizon)
    cls = {"logit": sm.Logit, "probit": sm.Probit}[link]
    res = cls(data["target"], X).fit(disp=0, maxiter=200, cov_type="HAC", cov_kwds={"maxlags": lags})
    return FitSummary(link.capitalize(), horizon, _coefs(res, ["const", *features.columns]), int(res.nobs),
                      data.index[0], data.index[-1],
                      {"pseudo_r2": float(res.prsquared), "llf": float(res.llf), "aic": float(res.aic), "nw_lags": lags})


# =============================================================================================
# 7. Markov-switching regime models
# =============================================================================================
#
# Two-regime models of monthly real returns r_t, estimated by maximum likelihood (statsmodels):
#   "mean_var": r_t = mu_S + e_t, e_t ~ N(0, sigma2_S)
#   "ar1":      r_t - mu_S(t) = phi (r_{t-1} - mu_S(t-1)) + e_t (Hamilton, 1989)
#   "tvtp":     "ar1" with time-varying transition probabilities (Diebold, Lee and Weinbach,
#               1994; Filardo, 1994): P(S_t = 0 | S_{t-1} = i) = logistic(z_{t-1}' b_i), where
#               z_{t-1} = (1, standardized predictors at t - 1).
# The bear regime is the one with the lower mean.


def _ms_model(returns: pd.Series, kind: str, tvtp: np.ndarray | None = None) -> Any:
    y = returns.to_numpy(dtype=float)
    if kind == "mean_var":
        return MarkovRegression(y, k_regimes=2, trend="c", switching_variance=True)
    if kind in ("ar1", "tvtp"):
        return MarkovAutoregression(y, k_regimes=2, order=1, switching_ar=False, switching_variance=True,
                                    exog_tvtp=tvtp if kind == "tvtp" else None)
    raise ValueError(f"unknown kind {kind!r}")


def _logit(p: float) -> float:
    return float(np.log(p / (1 - p)))


def _start_grid(returns: pd.Series, names: list[str]) -> list[np.ndarray]:
    """A fixed grid of starting values (so that estimation is deterministic)."""
    m, s2 = float(returns.mean()), float(returns.var())
    s = np.sqrt(s2)
    grid = []
    for (p00, p11), gap, ratio in itertools.product([(0.97, 0.90), (0.95, 0.80), (0.90, 0.60)], [0.5, 1.5], [3.0, 8.0]):
        values = {
            "p[0->0]": p00, "p[1->0]": 1 - p11,
            "p[0->0].tvtp0": _logit(p00), "p[1->0].tvtp0": _logit(1 - p11),
            "const[0]": m + 0.2 * gap * s, "const[1]": m - gap * s,
            "sigma2[0]": s2 * 2 / (1 + ratio), "sigma2[1]": s2 * 2 * ratio / (1 + ratio),
            "ar.L1": 0.2,
        }
        grid.append(np.array([values.get(n, 0.0) for n in names]))  # TVTP slopes start at zero
    return grid


@dataclass(frozen=True)
class RegimeFit:
    """A fitted two-regime model with regimes reported in the order (bull, bear)."""

    kind: str
    index: pd.DatetimeIndex
    params: np.ndarray
    param_names: tuple[str, ...]
    bear: int  # position of the bear regime in statsmodels' parameterization
    llf: float
    aic: float
    bic: float
    nobs: int
    means: tuple[float, float]  # (bull, bear) mean monthly return, percent
    variances: tuple[float, float]
    transition: np.ndarray  # fixed models: row-stochastic (bull, bear); TVTP: at mean predictors
    ar: float | None
    filtered: pd.Series  # P(bear at t | returns through t)
    smoothed: pd.Series  # P(bear at t | all returns): retrospective only
    coefs: dict[str, Coef]
    tvtp_keys: tuple[str, ...] = ()
    tvtp_center: tuple[np.ndarray, np.ndarray] | None = None  # mean and sd used to standardize
    p_bull_bear: pd.Series | None = None  # TVTP: P(S_t = bear | S_{t-1} = bull) over time

    @property
    def durations(self) -> tuple[float, float]:
        return tuple(float(1 / (1 - self.transition[i, i])) for i in range(2))


def _row_transitions(col_stochastic: np.ndarray, bear: int) -> np.ndarray:
    """statsmodels' [i, j] = P(S_t = i | S_{t-1} = j) -> row-stochastic, ordered (bull, bear)."""
    order = [1 - bear, bear]
    return col_stochastic.T[np.ix_(order, order)]


def tvtp_design(features: pd.DataFrame, keys: tuple[str, ...], center: tuple[np.ndarray, np.ndarray]) -> np.ndarray:
    """Rows z_t = (1, standardized predictors at t); row t drives the transition from t to t + 1."""
    x = (features[list(keys)].to_numpy(dtype=float) - center[0]) / center[1]
    return np.column_stack([np.ones(len(x)), x])


def _tvtp_lagged(returns: pd.Series, features: pd.DataFrame, keys: tuple[str, ...],
                 center: tuple[np.ndarray, np.ndarray]) -> np.ndarray:
    """exog_tvtp aligned with `returns`: the row for month t holds z_{t-1}."""
    return tvtp_design(features.shift(1).reindex(returns.index), keys, center)


def _named_coefs(res: Any, bull: int, bear: int) -> dict[str, Coef]:
    names = res.model.param_names
    est = dict(zip(names, np.asarray(res.params)))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        se = dict(zip(names, np.asarray(res.bse)))
        pv = dict(zip(names, np.asarray(res.pvalues)))
    out = {
        "mean_bull": Coef(est[f"const[{bull}]"], se[f"const[{bull}]"], pv[f"const[{bull}]"]),
        "mean_bear": Coef(est[f"const[{bear}]"], se[f"const[{bear}]"], pv[f"const[{bear}]"]),
        "sigma2_bull": Coef(est[f"sigma2[{bull}]"], se[f"sigma2[{bull}]"], np.nan),
        "sigma2_bear": Coef(est[f"sigma2[{bear}]"], se[f"sigma2[{bear}]"], np.nan),
    }
    if "p[0->0]" in est:  # fixed transitions: statsmodels estimates p[0->0] and p[1->0]
        out["p_bull_bull"] = Coef(est["p[0->0]"] if bull == 0 else 1 - est["p[1->0]"], se["p[0->0]" if bull == 0 else "p[1->0]"], np.nan)
        out["p_bear_bear"] = Coef(est["p[0->0]"] if bear == 0 else 1 - est["p[1->0]"], se["p[0->0]" if bear == 0 else "p[1->0]"], np.nan)
    else:  # TVTP: logit coefficients of P(S_t = 0 | S_{t-1} = i) on z_{t-1}
        for name in names:
            if name.startswith("p["):
                out[name] = Coef(est[name], se[name], pv[name])
    if "ar.L1" in est:
        out["ar"] = Coef(est["ar.L1"], se["ar.L1"], pv["ar.L1"])
    return out


def _summarize(kind: str, res: Any, index: pd.DatetimeIndex, tvtp_keys: tuple[str, ...] = (),
               center: tuple[np.ndarray, np.ndarray] | None = None) -> RegimeFit:
    names = list(res.model.param_names)
    p = dict(zip(names, np.asarray(res.params)))
    consts = np.array([p["const[0]"], p["const[1]"]])
    bear = int(np.argmin(consts))
    bull = 1 - bear
    p_bull_bear = None
    if kind == "tvtp":
        mean_z = np.r_[1.0, np.zeros(len(tvtp_keys))][None, :]
        transition = _row_transitions(res.model.regime_transition_matrix(res.params, exog_tvtp=mean_z)[:, :, 0], bear)
        path = res.regime_transition  # (2, 2, nobs)
        p_bull_bear = pd.Series(path[bear, bull, :], index=index, name="p_bull_bear")
    else:
        transition = _row_transitions(res.regime_transition[:, :, 0], bear)
    sig = np.array([p["sigma2[0]"], p["sigma2[1]"]])
    return RegimeFit(
        kind=kind, index=index, params=np.asarray(res.params), param_names=tuple(names), bear=bear,
        llf=float(res.llf), aic=float(res.aic), bic=float(res.bic), nobs=int(res.nobs),
        means=(float(consts[bull]), float(consts[bear])), variances=(float(sig[bull]), float(sig[bear])),
        transition=transition, ar=float(p["ar.L1"]) if "ar.L1" in p else None,
        filtered=pd.Series(np.asarray(res.filtered_marginal_probabilities)[:, bear], index=index, name="filtered"),
        smoothed=pd.Series(np.asarray(res.smoothed_marginal_probabilities)[:, bear], index=index, name="smoothed"),
        coefs=_named_coefs(res, bull, bear), tvtp_keys=tvtp_keys, tvtp_center=center, p_bull_bear=p_bull_bear,
    )


def _best_fit(model: Any, starts: list[np.ndarray]) -> Any:
    best = None
    for start in starts:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                res = model.fit(start_params=start, disp=False, maxiter=500)
            except (np.linalg.LinAlgError, ValueError):
                continue
        if np.isfinite(res.llf) and np.all(np.isfinite(res.params)) and (best is None or res.llf > best.llf + 1e-9):
            best = res
    if best is None:
        raise RuntimeError("Markov-switching estimation failed from every start")
    return best


def fit_regimes(returns: pd.Series, kind: str = "ar1", warm_start: np.ndarray | None = None) -> RegimeFit:
    """Fixed-transition two-regime model by ML from a fixed grid of starting values."""
    returns = returns.dropna()
    model = _ms_model(returns, kind)
    starts = _start_grid(returns, list(model.param_names))
    if warm_start is not None:
        starts.insert(0, np.asarray(warm_start))
    res = _best_fit(model, starts)
    return _summarize(kind, res, returns.index[len(returns) - model.nobs:])


def fit_tvtp(returns: pd.Series, features: pd.DataFrame, keys: tuple[str, ...] = TVTP_KEYS,
             fixed: RegimeFit | None = None, warm_start: np.ndarray | None = None, grid: bool = True) -> RegimeFit:
    """MS-AR(1) with time-varying transitions driven by the lagged predictors in `keys`.

    The sample is the set of months with a return and all lagged predictors; the predictors are
    standardized with that sample's means and standard deviations. Estimation starts from the
    fixed-transition estimates with zero slopes (`fixed`, estimated here if not given), from
    `warm_start` if given, and from the fixed grid if `grid` is true.
    """
    lagged = features[list(keys)].shift(1).reindex(returns.index)
    ok = returns.notna() & lagged.notna().all(axis=1)
    r = returns[ok]
    center = (lagged[ok].mean().to_numpy(), lagged[ok].std(ddof=0).to_numpy())
    model = _ms_model(r, "tvtp", _tvtp_lagged(r, features, keys, center))
    names = list(model.param_names)
    fixed = fixed or fit_regimes(r, "ar1")
    raw = dict(zip(fixed.param_names, fixed.params))
    from_fixed = {"p[0->0].tvtp0": _logit(raw["p[0->0]"]), "p[1->0].tvtp0": _logit(raw["p[1->0]"]), **raw}
    starts = [np.array([from_fixed.get(n, 0.0) for n in names])]
    if warm_start is not None:
        starts.insert(0, np.asarray(warm_start))
    if grid:
        starts += _start_grid(r, names)
    res = _best_fit(model, starts)
    return _summarize("tvtp", res, r.index[len(r) - model.nobs:], keys, center)


def bear_forecast(filtered_bear: np.ndarray, transition: np.ndarray, horizon: int) -> np.ndarray:
    """P(bear at t + h | returns through t) from filtered probabilities and a (bull, bear)
    row-stochastic transition matrix."""
    step = np.linalg.matrix_power(transition, horizon)
    f = np.asarray(filtered_bear, dtype=float)
    return (np.column_stack([1 - f, f]) @ step)[:, 1]


def regime_track(returns: pd.Series, features: pd.DataFrame, fit: RegimeFit, horizons: tuple[int, ...]) -> dict[int, pd.Series]:
    """h-step bear-regime forecasts over a history, with the parameters of `fit` held fixed.

    Filtered probabilities use returns through each month only. For TVTP models the h-step
    forecast from month t applies the transition matrix implied by z_t (known at t) h times.
    """
    returns = returns.dropna()
    if fit.kind != "tvtp":
        model = _ms_model(returns, fit.kind)
        res = model.filter(fit.params)
        index = returns.index[len(returns) - model.nobs:]
        f = np.asarray(res.filtered_marginal_probabilities)[:, fit.bear]
        return {h: pd.Series(bear_forecast(f, fit.transition, h), index=index) for h in horizons}
    lagged = features[list(fit.tvtp_keys)].shift(1).reindex(returns.index)
    r = returns[lagged.notna().all(axis=1)]
    model = _ms_model(r, "tvtp", _tvtp_lagged(r, features, fit.tvtp_keys, fit.tvtp_center))
    res = model.filter(fit.params)
    index = r.index[len(r) - model.nobs:]
    f = np.asarray(res.filtered_marginal_probabilities)[:, fit.bear]
    z = tvtp_design(features.reindex(index), fit.tvtp_keys, fit.tvtp_center)
    ok = np.all(np.isfinite(z), axis=1)
    out = {}
    trans = np.full((len(index), 2, 2), np.nan)
    if ok.any():
        cols = model.regime_transition_matrix(fit.params, exog_tvtp=z[ok])  # (2, 2, n_ok)
        trans[ok] = np.stack([_row_transitions(cols[:, :, i], fit.bear) for i in range(cols.shape[2])])
    for h in horizons:
        prob = np.column_stack([1 - f, f])[:, None, :]  # (n, 1, 2)
        step = np.linalg.matrix_power(np.where(np.isfinite(trans), trans, 0.0), h)
        val = (prob @ step)[:, 0, 1]
        out[h] = pd.Series(np.where(ok, val, np.nan), index=index)
    return out


@dataclass(frozen=True)
class SpecSummary:
    """A regime specification for the robustness table, regimes ordered by decreasing mean."""

    name: str
    k: int
    llf: float
    aic: float
    bic: float
    n_params: int
    nobs: int
    means: tuple[float, ...]
    sds: tuple[float, ...]
    stay: tuple[float, ...]
    bear_filtered: pd.Series
    ar: float | None = None

    @property
    def durations(self) -> tuple[float, ...]:
        return tuple(1 / (1 - p) for p in self.stay)


def fit_spec(name: str, returns: pd.Series, k: int, switching_mean: bool, switching_var: bool,
             seed: int = SEED) -> SpecSummary:
    """Markov-switching mean/variance model from statsmodels' starting values plus a seeded
    random search; regimes ordered by mean (ties by variance)."""
    returns = returns.dropna()
    model = MarkovRegression(returns.to_numpy(dtype=float), k_regimes=k, trend="c",
                             switching_trend=switching_mean, switching_variance=switching_var)
    best = None
    for reps in (0, 25):
        np.random.seed(seed)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                res = model.fit(search_reps=reps, disp=False, maxiter=500)
            except (np.linalg.LinAlgError, ValueError):
                continue
        if np.isfinite(res.llf) and (best is None or res.llf > best.llf + 1e-9):
            best = res
    if best is None:
        raise RuntimeError("Markov-switching estimation failed")
    p = dict(zip(best.model.param_names, np.asarray(best.params)))
    means = np.array([p.get(f"const[{r}]", p.get("const")) for r in range(k)], dtype=float)
    var = np.array([p.get(f"sigma2[{r}]", p.get("sigma2")) for r in range(k)], dtype=float)
    order = np.lexsort((var, -means))
    stay = np.diag(best.regime_transition[:, :, 0])
    return SpecSummary(
        name=name, k=k, llf=float(best.llf), aic=float(best.aic), bic=float(best.bic), n_params=len(best.params),
        nobs=int(best.nobs), means=tuple(float(means[i]) for i in order), sds=tuple(float(np.sqrt(var[i])) for i in order),
        stay=tuple(float(stay[i]) for i in order),
        bear_filtered=pd.Series(np.asarray(best.filtered_marginal_probabilities)[:, order[-1]],
                                index=returns.index[len(returns) - int(best.nobs):]),
    )


def spec_from_fit(name: str, fit: RegimeFit) -> SpecSummary:
    return SpecSummary(name=name, k=2, llf=fit.llf, aic=fit.aic, bic=fit.bic, n_params=len(fit.params), nobs=fit.nobs,
                       means=fit.means, sds=tuple(float(np.sqrt(v)) for v in fit.variances),
                       stay=(float(fit.transition[0, 0]), float(fit.transition[1, 1])), bear_filtered=fit.filtered,
                       ar=fit.ar)


# =============================================================================================
# 8. Real-time forecasting
# =============================================================================================
#
# At every forecast origin t (each month-end from MAIN_START) each model is re-estimated with
# information available at t only:
#   * predictors x_s for s <= t (already lagged for publication in build_features);
#   * "vintage" bear labels from dating the price history through t, so a training pair
#     (x_s, y_{s+h}) is used only if s + h <= t;
#   * regime models re-estimated every January on returns through t, filtered probabilities only;
#   * machine-learning models re-estimated every January, hyperparameters chosen by validation on
#     the last ML_VALIDATION months of that training window.

MODEL_LABELS: dict[str, str] = {
    "uncond": "Unconditional frequency",
    "persist": "Persistence (real-time state)",
    "ms": "MS-AR(1) filtered probability",
    "tvtp": "TVTP MS-AR(1)",
    "logit_dy": "Logit: dividend yield",
    "logit_all": f"Logit: {len(FORECAST_KEYS)} main predictors",
    "probit_all": f"Probit: {len(FORECAST_KEYS)} main predictors",
    "logit_state": f"Logit: {len(FORECAST_KEYS)} predictors + state",
    "enet": "Elastic-net logit",
    "enet_rich": "Elastic-net logit, rich set",
    "gbt": "Gradient boosting",
    "gbt_rich": "Gradient boosting, rich set",
    "logit_ext": f"Logit: all {len(ALL_KEYS)} predictors",
    "combo": "Equal-weight combination",
    "dma_uni": "DMA: univariate logits",
    "dma_all": "DMA: all models",
    **{f"uni_{k}": f"Univariate logit: {FEATURE_LABELS[k]}" for k in ALL_KEYS},
}
BASELINES = ("uncond", "persist")
CORE_MODELS = ("uncond", "persist", "ms", "logit_dy", "logit_all", "probit_all", "logit_state")
MODERN_MODELS = ("tvtp", "enet", "enet_rich", "gbt", "gbt_rich", "combo", "dma_uni", "dma_all")
UNIVARIATE = tuple(f"uni_{k}" for k in ALL_KEYS)
ML_MODELS = ("enet", "enet_rich", "gbt", "gbt_rich")
MAIN_MODELS = CORE_MODELS + ("tvtp",) + ML_MODELS + UNIVARIATE + ("logit_ext", "combo")
ROBUST_MODELS = ("uncond", "persist", "ms", "logit_dy", "logit_all")
DMA_ALL_MEMBERS = CORE_MODELS + ("tvtp",) + ML_MODELS


def _jeffreys(successes: float, n: float) -> float:
    return (successes + 0.5) / (n + 1)


def _zscore(train: np.ndarray, test: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mu, sd = train.mean(axis=0), train.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    return (train - mu) / sd, (test - mu) / sd


def newton_binary(y: np.ndarray, X: np.ndarray, link: str = "logit", maxiter: int = 50, tol: float = 1e-10) -> np.ndarray | None:
    """Maximum likelihood logit (Newton-Raphson) or probit (Fisher scoring); None if the
    iterations do not converge cleanly. Matches statsmodels to numerical tolerance (tested) at a
    fraction of the cost of the tens of thousands of real-time refits."""
    beta = np.zeros(X.shape[1])
    for _ in range(maxiter):
        eta = X @ beta
        if link == "logit":
            p = 1 / (1 + np.exp(-eta))
            w, score = p * (1 - p), y - p
        else:
            cdf = np.clip(stats.norm.cdf(eta), 1e-12, 1 - 1e-12)
            pdf = stats.norm.pdf(eta)
            w = pdf**2 / (cdf * (1 - cdf))
            score = (y - cdf) * pdf / (cdf * (1 - cdf))
        try:
            step = np.linalg.solve((X * w[:, None]).T @ X, X.T @ score)
        except np.linalg.LinAlgError:
            return None
        beta = beta + step
        if not np.all(np.isfinite(beta)) or np.max(np.abs(beta)) > 30:
            return None
        if np.max(np.abs(step)) < tol:
            return beta
    return None


def binary_forecast(link: str, y: np.ndarray, X: np.ndarray, x_new: np.ndarray) -> float:
    """Fit a logit or probit on standardized predictors and return P(y = 1 | x_new)."""
    Xz, xz = _zscore(X, x_new[None, :])
    Xc = np.column_stack([np.ones(len(Xz)), Xz])
    xc = np.r_[1.0, xz[0]]
    beta = newton_binary(np.asarray(y, dtype=float), Xc, link)
    if beta is None:
        cls = {"logit": sm.Logit, "probit": sm.Probit}[link]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            beta = np.asarray(cls(y, Xc).fit(disp=0, maxiter=200).params)
    eta = float(xc @ beta)
    return float(1 / (1 + np.exp(-eta))) if link == "logit" else float(stats.norm.cdf(eta))


def _odds(p: np.ndarray) -> np.ndarray:
    q = np.clip(p, 1e-4, 1 - 1e-4)
    return np.log(q / (1 - q))


# --- machine learning ----------------------------------------------------------------------


def _make_ml(kind: str, params: tuple) -> Any:
    if kind == "enet":
        c, l1 = params
        return LogisticRegression(C=c, l1_ratio=l1, solver="saga", max_iter=5000, tol=1e-6, random_state=SEED)
    depth, iters = params
    return HistGradientBoostingClassifier(max_depth=depth, max_iter=iters, learning_rate=GBT_LEARNING_RATE, min_samples_leaf=40,
                                          l2_regularization=1.0, early_stopping=False, random_state=SEED)


@dataclass(frozen=True)
class MLFit:
    """A fitted classifier, the scaling applied to its inputs and the chosen hyperparameters."""

    model: Any
    mu: np.ndarray
    sd: np.ndarray
    params: tuple

    def predict(self, x: np.ndarray) -> float:
        z = ((x - self.mu) / self.sd)[None, :]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return float(self.model.predict_proba(z)[0, 1])


def _scaled_fit(kind: str, params: tuple, X: np.ndarray, y: np.ndarray) -> MLFit:
    mu, sd = X.mean(axis=0), X.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    if kind == "gbt":  # trees are invariant to scaling
        mu, sd = np.zeros(X.shape[1]), np.ones(X.shape[1])
    model = _make_ml(kind, params)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model.fit((X - mu) / sd, y)
    return MLFit(model, mu, sd, params)


def fit_ml(kind: str, X: np.ndarray, y: np.ndarray, horizon: int, validation: int = ML_VALIDATION) -> MLFit:
    """Choose hyperparameters by a time-series split inside the training window, then refit.

    The last `validation` training origins form the validation block; the estimation block ends
    `horizon` origins earlier, so no estimation target overlaps the validation period. The grid
    point with the lowest validation Brier score is refit on the whole window (ties: first).
    """
    grid = ENET_GRID if kind == "enet" else GBT_GRID
    n = len(y)
    fit_end, val_start = n - validation - horizon, n - validation
    best, best_score = grid[0], np.inf
    if fit_end > 0 and len(np.unique(y[:fit_end])) == 2:
        for params in grid:
            f = _scaled_fit(kind, params, X[:fit_end], y[:fit_end])
            z = (X[val_start:] - f.mu) / f.sd
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                score_ = brier(f.model.predict_proba(z)[:, 1], y[val_start:])
            if score_ < best_score - 1e-12:
                best, best_score = params, score_
    return _scaled_fit(kind, best, X, y)


# --- the forecasting loop -------------------------------------------------------------------


@dataclass(frozen=True)
class RunSpec:
    """One real-time forecasting design: the dating rule, the estimation window and the models."""

    key: str
    label: str
    price: pd.Series  # index dated to obtain vintage labels (real or nominal)
    labels: pd.DataFrame  # final labels (`bear`) and real-time state (`bear_now`) under this rule
    decline: float
    models: tuple[str, ...]
    window: int | None = None  # rolling window in months; None = expanding


@dataclass(frozen=True)
class Vintages:
    """Model fits re-estimated at the first origin and every January, used until the next refit."""

    fits: dict[pd.Timestamp, Any]

    def asof(self, origin: pd.Timestamp) -> Any:
        return self.fits[max(d for d in self.fits if d <= origin)]


def refit_dates(origins: pd.DatetimeIndex) -> list[pd.Timestamp]:
    return [origins[0], *[d for d in origins[1:] if d.month == 1]]


def fit_vintage_regimes(returns: pd.Series, origins: pd.DatetimeIndex) -> Vintages:
    """MS-AR(1) re-estimated each January on returns through that month (warm-started)."""
    fits: dict[pd.Timestamp, RegimeFit] = {}
    warm = None
    for date in refit_dates(origins):
        fits[date] = fit_regimes(returns.loc[:date], "ar1", warm_start=warm)
        warm = fits[date].params
    return Vintages(fits)


def fit_vintage_tvtp(returns: pd.Series, features: pd.DataFrame, origins: pd.DatetimeIndex, fixed: Vintages) -> Vintages:
    """TVTP MS-AR(1) re-estimated each January on data through that month.

    Starting values: the previous year's estimates and the same month's fixed-transition fit
    with zero slopes; the full starting-value grid is used only at the first refit.
    """
    fits: dict[pd.Timestamp, RegimeFit] = {}
    warm = None
    for date in refit_dates(origins):
        fits[date] = fit_tvtp(returns.loc[:date], features.loc[:date], fixed=fixed.fits[date], warm_start=warm,
                              grid=warm is None)
        warm = fits[date].params
    return Vintages(fits)


def run_forecasts(specs: list[RunSpec], features: pd.DataFrame, returns: pd.Series, origins: pd.DatetimeIndex,
                  horizons: tuple[int, ...], regimes: dict[str, Vintages]) -> tuple[dict[str, pd.DataFrame], dict]:
    """Real-time probability forecasts of a bear market h months ahead for every design.

    `features` holds all predictors; the training sample of every model is the set of origins at
    which all of them are observed. Returns one long frame per design, with one row per (origin,
    horizon, model), and, for the first design, the vintage labels and chosen ML hyperparameters.
    """
    dates = features.index
    pos = {d: i for i, d in enumerate(dates)}
    feat = features[ALL_KEYS].to_numpy(dtype=float)
    col = {k: i for i, k in enumerate(ALL_KEYS)}
    base_cols = [col[k] for k in FORECAST_KEYS]
    valid = np.isfinite(feat).all(axis=1)
    rows: dict[str, list[dict]] = {s.key: [] for s in specs}
    vintage_store: dict[pd.Timestamp, np.ndarray] = {}
    ml_choices: list[dict] = []
    ml_fits: dict[tuple[str, int], MLFit] = {}
    main = specs[0]
    for n_done, origin in enumerate(origins):
        t = pos[origin]
        tracks = {
            name: {h: s.reindex(dates[: t + 1]).to_numpy()
                   for h, s in regime_track(returns.loc[:origin], features.loc[:origin], v.asof(origin), horizons).items()}
            for name, v in regimes.items()
        }
        for spec in specs:
            models = spec.models
            vintage = date_bear_markets(spec.price.iloc[: t + 1].to_numpy(), spec.decline, spec.decline).labels
            if spec is main:
                vintage_store[origin] = vintage.astype(np.int8)
            state_all = spec.labels["bear_now"].to_numpy()
            for h in horizons:
                if t + h >= len(dates):
                    continue
                train = np.arange(0, t - h + 1)
                if spec.window is not None:
                    train = train[train > t - h - spec.window]
                train = train[valid[train]]
                y = vintage[train + h]
                X, x_new = feat[train], feat[t]
                state, state_new = state_all[train], state_all[t]
                preds: dict[str, float] = {}
                if "uncond" in models:
                    preds["uncond"] = _jeffreys(y.sum(), len(y))
                if "persist" in models:
                    same = state == state_new
                    preds["persist"] = _jeffreys(y[same].sum(), same.sum())
                for name in ("ms", "tvtp"):
                    if name in models:
                        track = tracks[name][h]
                        ok = np.isfinite(track[train])
                        preds[name] = binary_forecast("logit", y[ok], _odds(track[train][ok])[:, None],
                                                      _odds(track[[t]]))
                if "logit_dy" in models:
                    j = col["log_dy"]
                    preds["logit_dy"] = binary_forecast("logit", y, X[:, [j]], x_new[[j]])
                if "logit_all" in models:
                    preds["logit_all"] = binary_forecast("logit", y, X[:, base_cols], x_new[base_cols])
                if "probit_all" in models:
                    preds["probit_all"] = binary_forecast("probit", y, X[:, base_cols], x_new[base_cols])
                if "logit_state" in models:
                    preds["logit_state"] = binary_forecast("logit", y, np.column_stack([X[:, base_cols], state]),
                                                           np.r_[x_new[base_cols], state_new])
                if "logit_ext" in models:
                    preds["logit_ext"] = binary_forecast("logit", y, X, x_new)
                uni = []
                for key in ALL_KEYS:
                    if f"uni_{key}" in models:
                        j = col[key]
                        uni.append(binary_forecast("logit", y, X[:, [j]], x_new[[j]]))
                        preds[f"uni_{key}"] = uni[-1]
                if "combo" in models and uni:
                    preds["combo"] = float(np.mean(uni))
                for name in ML_MODELS:
                    if name not in models:
                        continue
                    kind = name.split("_")[0]
                    rich = name.endswith("_rich")
                    Xm = np.column_stack([X, state]) if rich else X[:, base_cols]
                    xm = np.r_[x_new, state_new] if rich else x_new[base_cols]
                    if origin.month == 1 or (name, h) not in ml_fits:
                        ml_fits[(name, h)] = fit_ml(kind, Xm, y, h)
                        ml_choices.append({"origin": origin, "model": name, "horizon": h,
                                           "params": str(ml_fits[(name, h)].params)})
                    preds[name] = ml_fits[(name, h)].predict(xm)
                target = dates[t + h]
                y_final = int(spec.labels["bear"].iloc[t + h])
                for model, p in preds.items():
                    rows[spec.key].append({"origin": origin, "horizon": h, "target_date": target, "y": y_final,
                                           "model": model, "p": p, "n_train": len(y)})
        if n_done % 60 == 0:
            log(f"  forecasts through {origin:%Y-%m}")
    out = {k: pd.DataFrame(v) for k, v in rows.items()}
    return out, {"vintages": vintage_store, "ml_choices": pd.DataFrame(ml_choices)}


def dma_combination(fc: pd.DataFrame, members: tuple[str, ...], name: str, vintages: dict[pd.Timestamp, np.ndarray],
                    dates: pd.DatetimeIndex, alpha: float = DMA_ALPHA) -> pd.DataFrame:
    """Dynamic model averaging of probability forecasts (Raftery, Kárný and Ettler, 2010).

    With a fixed set of member forecasts, the DMA recursion (weights flattened by the forgetting
    factor alpha, then updated by each model's predictive likelihood) gives weights proportional to
    exp(sum_j alpha^(age_j) log p_k(y_j)). At origin t only forecasts whose targets s + h <= t are
    scored, against the vintage labels available at t. Members start with equal weights.
    """
    pos = {d: i for i, d in enumerate(dates)}
    out = []
    for h in sorted(fc.horizon.unique()):
        sub = fc[fc.horizon == h]
        wide = sub.pivot(index="origin", columns="model", values="p")[list(members)]
        meta = sub.drop_duplicates("origin").set_index("origin").reindex(wide.index)
        P = np.clip(wide.to_numpy(), LOG_LOSS_FLOOR, 1 - LOG_LOSS_FLOOR)
        lp1, lp0 = np.log(P), np.log(1 - P)
        o_pos = np.array([pos[o] for o in wide.index])
        for i, origin in enumerate(wide.index):
            t = o_pos[i]
            past = np.flatnonzero(o_pos + h <= t)
            weights = np.full(len(members), 1 / len(members))
            if len(past):
                y = vintages[origin][o_pos[past] + h].astype(bool)
                ls = np.where(y[:, None], lp1[past], lp0[past])
                s = (alpha ** (t - h - o_pos[past])) @ ls
                weights = np.exp(s - s.max())
                weights /= weights.sum()
            out.append({"origin": origin, "horizon": h, "target_date": meta["target_date"].iloc[i],
                        "y": int(meta["y"].iloc[i]), "model": name, "p": float(weights @ wide.iloc[i].to_numpy()),
                        "n_train": int(len(past))})
    return pd.DataFrame(out)


# =============================================================================================
# 9. Forecasting the regime probability (the award version's design, corrected)
# =============================================================================================


def regime_prob_forecasts(target: pd.Series, features: pd.DataFrame, origins: pd.DatetimeIndex,
                          horizons: tuple[int, ...], sample_start: pd.Timestamp) -> pd.DataFrame:
    """Expanding-window univariate OLS and beta-regression forecasts of Q_{t+h}, each against an
    intercept-only model. One row per (origin, horizon, predictor)."""
    dates = target.index
    pos = {d: i for i, d in enumerate(dates)}
    start = pos[sample_start]
    rows = []
    for h in horizons:
        lead = target.shift(-h)
        for origin in origins:
            t = pos[origin]
            if t + h >= len(dates):
                continue
            train = np.arange(start, t - h + 1)
            y = lead.iloc[train].to_numpy()
            y_beta = squeeze_unit(y)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                b0 = BetaModel(y_beta, np.ones((len(y), 1))).fit(disp=0, maxiter=500)
            beta_restricted = float(b0.predict(np.ones((1, 1)))[0])
            for key in features.columns:
                x = features[key].iloc[train].to_numpy()
                X = sm.add_constant(x)
                x_new = np.array([[1.0, features[key].iloc[t]]])
                ols = sm.OLS(y, X).fit()
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    beta = BetaModel(y_beta, X).fit(disp=0, maxiter=500, start_params=np.r_[b0.params[0], 0.0, b0.params[-1]])
                rows.append({"origin": origin, "horizon": h, "predictor": key, "actual": float(lead.iloc[t]),
                             "ols_restricted": float(y.mean()), "ols": float(ols.predict(x_new)[0]),
                             "beta_restricted": beta_restricted, "beta": float(beta.predict(x_new)[0])})
    return pd.DataFrame(rows)


def mspe_summary(fc: pd.DataFrame) -> pd.DataFrame:
    """Ratio of mean squared prediction errors and the Clark-West test, per predictor and horizon."""
    rows = []
    for (h, key), g in fc.groupby(["horizon", "predictor"]):
        a = g["actual"].to_numpy()
        for model in ("OLS", "Beta"):
            col = model.lower()
            r_pred, u_pred = g[f"{col}_restricted"].to_numpy(), g[col].to_numpy()
            stat, p = clark_west(a, r_pred, u_pred, h)
            rows.append({"model": model, "predictor": key, "k": h, "n": len(a), "cw_stat": stat, "cw_p": p,
                         "mspe_ratio": np.mean((u_pred - a) ** 2) / np.mean((r_pred - a) ** 2)})
    return pd.DataFrame(rows)


# =============================================================================================
# 10. Replication of the award version's code path (errors included, for comparison only)
# =============================================================================================
#
# Three problems of the archived code.R are reproduced deliberately so their effect can be
# measured: (1) the regime model regresses 100 ln P_t on the `realpricelag` column, which holds
# P_{t+1}; (2) `dplyr::lag(Q, k)` builds the "k months ahead" target, i.e. Q_{t-k}; (3) the "MSPE
# ratio" divides squared mean errors. The replication runs on one45.csv, the award version's data.

ARCHIVED_PREDICTORS: dict[str, str] = {
    "infl": "CPI",
    "lrir10": "Long-term rate",
    "realbond": "Real bond",
    "realdividend": "Real dividend",
    "realtotalreturn": "Real total return",
    "realtrscaledearnings": "TR-scaled earnings",
    "TRCAPE": "TR-CAPE",
}
ARCHIVED_HORIZONS = (1, 2, 3, 6, 12, 18, 24)
ARCHIVED_SAMPLE = (pd.Timestamp("1960-01-01"), pd.Timestamp("2023-12-01"))


@dataclass(frozen=True)
class ArchivedRegimes:
    regime_prob: pd.Series  # filtered probability of the high-variance regime
    transition: np.ndarray  # row-stochastic, ordered (bull, bear)


def archived_frame(one45: pd.DataFrame) -> pd.DataFrame:
    """The archived design matrix: rows 1959:12-2023:12, differenced, first row dropped."""
    df = one45.loc[ARCHIVED_SAMPLE[0] - pd.DateOffset(months=1): ARCHIVED_SAMPLE[1]].copy()
    df["realprice"] = 100 * np.log(df["realprice"])
    df["realpricelag"] = 100 * np.log(df["realpricelag"])
    for col in ARCHIVED_PREDICTORS:
        df[col] = df[col].diff()
    return df.iloc[1:]


def fit_archived_regimes(df: pd.DataFrame) -> ArchivedRegimes:
    """Two-regime regression of 100 ln P_t on 100 ln P_{t+1} (switching intercept, slope, variance)."""
    y = df["realprice"].to_numpy()
    x = df["realpricelag"].to_numpy()
    xc = x - x.mean()  # centring only re-parameterizes the intercepts
    model = MarkovRegression(y, k_regimes=2, exog=xc, switching_exog=True, switching_variance=True)
    ols = sm.OLS(y, sm.add_constant(xc)).fit()
    best = None
    for p00, p11 in [(0.9, 0.8), (0.95, 0.85), (0.8, 0.6)]:
        start = np.array([p00, 1 - p11, ols.params[0] + 1, ols.params[0] - 1, ols.params[1], ols.params[1],
                          ols.mse_resid * 0.5, ols.mse_resid * 2])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                res = model.fit(start_params=start, em_iter=0, disp=False, maxiter=2000)
            except np.linalg.LinAlgError:
                continue
        if np.isfinite(res.llf) and (best is None or res.llf > best.llf):
            best = res
    if best is None:
        raise RuntimeError("archived regime model failed to converge")
    p = dict(zip(best.model.param_names, best.params))
    bear = int(np.argmax([p["sigma2[0]"], p["sigma2[1]"]]))
    return ArchivedRegimes(
        regime_prob=pd.Series(np.asarray(best.filtered_marginal_probabilities)[:, bear], index=df.index),
        transition=_row_transitions(best.regime_transition[:, :, 0], bear),
    )


def archived_in_sample(df: pd.DataFrame, q: pd.Series) -> pd.DataFrame:
    """Archived univariate OLS of Q_{t-k} (mislabeled 'ahead k') with classical standard errors."""
    rows = []
    for col in ARCHIVED_PREDICTORS:
        for k in ARCHIVED_HORIZONS:
            data = pd.concat([q.shift(k).rename("y"), df[col]], axis=1).iloc[k:]
            res = sm.OLS(data["y"], sm.add_constant(data[col])).fit()
            rows.append({"predictor": col, "k": k, "coef": float(res.params[col]), "se": float(res.bse[col]),
                         "r2": float(res.rsquared), "nobs": int(res.nobs)})
    return pd.DataFrame(rows)


def archived_mspe(df: pd.DataFrame, q: pd.Series, horizons: tuple[int, ...]) -> pd.DataFrame:
    """Archived 80/20 holdout with both the archived ratio and the true MSPE ratio."""
    rows = []
    cut = int(round(0.8 * (len(df) - 1)))  # code.R reuses the k = 1 split point for every k
    for k in horizons:
        data = pd.concat([q.shift(k).rename("y"), df[list(ARCHIVED_PREDICTORS)]], axis=1).iloc[k:]
        train, test = data.iloc[:cut], data.iloc[cut:]
        y_beta = squeeze_unit(train["y"])
        restricted = np.full(len(test), train["y"].mean())
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            b0 = BetaModel(y_beta.to_numpy(), np.ones((len(train), 1))).fit(disp=0)
        beta_restricted = np.full(len(test), float(b0.predict(np.ones((1, 1)))[0]))
        for col in ARCHIVED_PREDICTORS:
            X = sm.add_constant(train[col])
            Xt = sm.add_constant(test[col], has_constant="add")
            ols = sm.OLS(train["y"], X).fit().predict(Xt).to_numpy()
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                beta = BetaModel(y_beta.to_numpy(), X.to_numpy()).fit(disp=0).predict(Xt.to_numpy())
            actual = test["y"].to_numpy()
            for model, unr, res_ in (("OLS", ols, restricted), ("Beta", beta, beta_restricted)):
                eu, er = unr - actual, res_ - actual
                rows.append({"model": model, "predictor": col, "k": k, "test_start": test.index[0],
                             "archived_ratio": float(eu.mean() ** 2 / er.mean() ** 2),
                             "mspe_ratio": float(np.mean(eu**2) / np.mean(er**2))})
    return pd.DataFrame(rows)


def replication_pairs(arch_is: pd.DataFrame, arch_mspe_all: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Reported award-version values (transcribed from the PDF) paired with their replication."""
    reported = pd.read_csv(ARCHIVED_REPORTED_FILE)

    def pairs(table: str, stat: str, source: pd.DataFrame, value: str) -> pd.DataFrame:
        rep = reported[(reported.table == table) & (reported.statistic == stat)]
        merged = rep.merge(source, on=["predictor", "k"])
        return pd.DataFrame({"reported": merged["value"], "replicated": merged[value]})

    ols_ratios = arch_mspe_all[arch_mspe_all.model == "OLS"]
    return {
        "OLS coefficients\n(4 predictors x 7 horizons)": pairs("ols_in_sample", "coef", arch_is, "coef"),
        "OLS R²\n(6 predictors x 7 horizons)": pairs("ols_in_sample", "r2", arch_is, "r2"),
        "Award 'MSPE ratio', OLS\n(7 predictors x 7 horizons)": pairs("ols_forecast_ratio", "ratio", ols_ratios, "archived_ratio"),
    }


# =============================================================================================
# 11. Tables (Typst and Markdown from one definition)
# =============================================================================================

STAR_NOTE = "* p < 0.10, ** p < 0.05, *** p < 0.01 (two-sided)."
DM_STARS = "Stars: one-sided Diebold-Mariano test against the unconditional frequency, * p < 0.10, ** p < 0.05, *** p < 0.01."


@dataclass
class Row:
    label: str
    cells: list[str]
    kind: str = "stat"  # "coef" rows carry significance stars


@dataclass
class Section:
    title: str | None
    rows: list[Row] = field(default_factory=list)


@dataclass
class Table:
    key: str
    title: str
    columns: list[str]
    sections: list[Section]
    notes: list[str]
    groups: list[tuple[str, int]] | None = None
    stub: str = ""
    stub_width: str = "2fr"
    widths: list[str] | None = None
    aligns: list[str] | None = None
    size: str = "8.5pt"


def coef_rows(label: str, coefs: list[Coef | None], digits: int = 3, with_stars: bool = True) -> list[Row]:
    """An estimate row with stars and a standard-error row beneath it."""
    est, se = [], []
    for c in coefs:
        if c is None:
            est.append("")
            se.append("")
            continue
        est.append(fmt(c.estimate, digits) + (stars(c.pvalue) if with_stars else ""))
        se.append(f"({fmt(c.se, digits)})" if np.isfinite(c.se) else "")
    return [Row(label, est, "coef"), Row("", se, "se")]


def coef_cell(c: Coef, digits: int = 2) -> str:
    return f"{fmt(c.estimate, digits)}{stars(c.pvalue)} ({fmt(c.se, digits)})"


def _typst_escape(text: str) -> str:
    return "".join("\\" + ch if ch in "\\*_$#@<>`[]~" else ch for ch in text)


def _typst_cell(text: str, kind: str) -> str:
    star_part = ""
    if kind == "coef":
        stripped = text.rstrip("*")
        n = len(text) - len(stripped)
        text = stripped
        if n:
            star_part = "#super[" + "\\*" * n + "]"
    return "[" + _typst_escape(text) + star_part + "]"


def to_typst(table: Table) -> str:
    """A Typst `figure` holding the table and its notes."""
    ncol = len(table.columns)
    lines = [
        "#figure(",
        f"  caption: [{_typst_escape(table.title)}],",
        "  kind: table,",
        "  [",
        f"    #set text(size: {table.size}, hyphenate: false)",
        "    #set par(justify: false, first-line-indent: 0em)",
        "    #table(",
        f"      columns: ({table.stub_width}, " + ", ".join(table.widths or ["1fr"] * ncol) + "),",
        "      align: (left, " + ", ".join(table.aligns or ["center"] * ncol) + "),",
        "      stroke: none,",
        "      inset: (x: 3pt, y: 2.4pt),",
        "      table.hline(stroke: 0.9pt),",
        "      table.header(",
    ]
    if table.groups:
        cells, rules, col = ["[]"], [], 1
        for name, span in table.groups:
            cells.append(f"table.cell(colspan: {span})[{_typst_escape(name)}]")
            rules.append(f"table.hline(start: {col}, end: {col + span}, stroke: 0.4pt)")
            col += span
        lines.append("        " + ", ".join(cells) + ",")
        lines.extend("        " + r + "," for r in rules)
    header = [f"[{_typst_escape(table.stub)}]"] + [f"[{_typst_escape(c)}]" for c in table.columns]
    lines += ["        " + ", ".join(header) + ",", "      ),", "      table.hline(stroke: 0.5pt),"]
    for s_i, section in enumerate(table.sections):
        if section.title:
            if s_i > 0:
                lines.append(f"      table.cell(colspan: {ncol + 1}, inset: (y: 1.5pt))[],")
            lines.append(f"      table.cell(colspan: {ncol + 1}, align: left)[_{_typst_escape(section.title)}_],")
        elif s_i > 0:
            lines.append("      table.hline(stroke: 0.3pt),")
        for row in section.rows:
            cells = [f"[{_typst_escape(row.label)}]"] + [_typst_cell(c, row.kind) for c in row.cells]
            lines.append("      " + ", ".join(cells) + ",")
    lines += ["      table.hline(stroke: 0.9pt),", "    )"]
    if table.notes:
        note = " ".join(_typst_escape(n) for n in table.notes)
        lines.append("    #block(width: 100%, above: 0.5em)[#set text(size: 7.5pt); #set par(justify: true); "
                     f"#align(left)[_Notes:_ {note}]]")
    lines += ["  ],", f") <tab:{table.key}>"]
    return "\n".join(lines) + "\n"


def to_markdown(table: Table) -> str:
    """GitHub-flavoured Markdown (group names are folded into the column headers)."""
    headers = list(table.columns)
    if table.groups:
        expanded = [name for name, span in table.groups for _ in range(span)]
        headers = [f"{g} {c}".strip() for g, c in zip(expanded, headers)]

    def esc(text: str) -> str:
        return text.replace("|", "\\|").replace("*", "\\*")

    lines = [f"**{table.title}**", "", "| " + " | ".join([esc(table.stub)] + [esc(h) for h in headers]) + " |",
             "|" + "---|" + "---:|" * len(headers)]
    for section in table.sections:
        if section.title:
            lines.append(f"| *{esc(section.title)}* |" + " |" * len(headers))
        for row in section.rows:
            lines.append("| " + " | ".join([esc(row.label)] + [esc(c) for c in row.cells]) + " |")
    if table.notes:
        lines += ["", "Notes: " + " ".join(table.notes)]
    return "\n".join(lines) + "\n"


def write_table(table: Table, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{table.key}.typ").write_text(to_typst(table))
    (directory / f"{table.key}.md").write_text(to_markdown(table))


def _h(h: int) -> str:
    return f"h = {h}"


def _ym(ts: pd.Timestamp) -> str:
    return f"{ts:%Y:%m}"


# --- table builders ---------------------------------------------------------------------------


def variables_table(features: pd.DataFrame, sample: str) -> Table:
    sections = []
    for title, group in (("Monthly-change predictors (award-version variables; appendix)", ORIGINAL_FEATURES),
                         ("State predictors (main bear-market models)", FORECAST_FEATURES),
                         ("Additional state predictors (predictor experiments, rich machine-learning set)", EXTRA_FEATURES)):
        rows = []
        for f in group:
            s = features[f.key].dropna()
            rows.append(Row(f.label, [f.construction, f.unit, f.lag, fmt(s.mean(), 2), fmt(s.std(), 2)]))
        sections.append(Section(title, rows))
    return Table(
        key="variables", title="Predictors, construction and publication lags",
        columns=["Construction", "Units", "Lag (months)", "Mean", "SD"], sections=sections,
        notes=[f"Statistics over {sample}. A forecast is made at the end of month t. Lag gives the publication lag "
               "applied to the inputs: CPI enters with one month, dividends (D) and earnings (E) with six. Real values "
               "are deflated by the CPI available at t."],
        stub="Predictor", stub_width="1.9fr", widths=["2.1fr", "1fr", "1fr", "0.6fr", "0.6fr"],
        aligns=["left", "left", "center", "right", "right"],
    )


def episodes_table(ep: pd.DataFrame, span: str) -> Table:
    rows = [Row(f"{r.peak:%Y-%m}", [f"{r.trough:%Y-%m}", str(r.months), fmt(r.decline_pct, 1), f"{r.confirmed:%Y-%m}",
                                     str(months_between(r.peak, r.confirmed))]) for r in ep.itertuples()]
    return Table(
        key="episodes", title=f"Dated bear markets in the real S&P 500, {span}",
        columns=["Trough", "Months", "Decline (%)", "Confirmed", "Months to confirm"], sections=[Section(None, rows)],
        notes=["A bear market runs from a peak to the following trough when the real index falls at least 20% below the "
               "peak before rising 20% above the trough. 'Confirmed' is the first month in which the 20% decline had "
               "occurred, that is, when the bear market became knowable in real time."],
        stub="Peak", stub_width="1fr", size="8pt",
    )


def data_comparison_table(comp: pd.DataFrame, vintage: str) -> Table:
    rows = [Row(r.series, [f"{_ym(r.first)}-{_ym(r.last)}", f"{r.months:,}", str(r.n_differ),
                           fmt(r.max_abs_rel_pct, 2) if r.n_differ else "",
                           f"{_ym(r.first_differ)}-{_ym(r.last_differ)}" if r.n_differ else ""])
            for r in comp.itertuples()]
    return Table(
        key="data_comparison", title=f"The archived extract one45.csv against the {vintage} Shiller workbook",
        columns=["Overlap", "Months", "Months that differ", "Largest difference (%)", "Months affected"],
        sections=[Section(None, rows)],
        notes=["A month differs if the archived value differs from the current value rounded to two decimals by more "
               "than 0.01 (levels), or by more than 0.05% after rescaling (real series, which Shiller expresses in "
               "dollars of the latest month). 'Largest difference' is the largest absolute percentage difference among "
               "the months that differ. All differences fall in the last months of the archived file, which held "
               "estimates at the time (see output/results/one45_differences.csv)."],
        stub="Series", stub_width="2.2fr", widths=["1.5fr", "0.7fr", "0.9fr", "1fr", "1.3fr"],
    )


def regime_table(fits: dict[str, RegimeFit]) -> Table:
    cols = list(fits.values())

    def coef_row(label: str, key: str, digits: int = 3, with_stars: bool = True) -> list[Row]:
        return coef_rows(label, [f.coefs.get(key) for f in cols], digits, with_stars)

    def sd_row(label: str, key: str) -> Row:
        return Row(label, [fmt(float(np.sqrt(f.coefs[key].estimate)), 2) for f in cols])

    sections = [
        Section("Mean monthly real return (%)", coef_row("Bull regime", "mean_bull") + coef_row("Bear regime", "mean_bear")),
        Section("Innovation variance", coef_row("Bull regime", "sigma2_bull", 2, False) + coef_row("Bear regime", "sigma2_bear", 2, False)
                + [sd_row("Bull volatility (sd, %)", "sigma2_bull"), sd_row("Bear volatility (sd, %)", "sigma2_bear")]),
        Section("Autoregression", coef_row("AR(1) coefficient", "ar")),
        Section("Transitions", coef_row("P(bull to bull)", "p_bull_bull", 3, False) + coef_row("P(bear to bear)", "p_bear_bear", 3, False)
                + [Row("Expected bull duration (months)", [fmt(f.durations[0], 1) for f in cols]),
                   Row("Expected bear duration (months)", [fmt(f.durations[1], 1) for f in cols])]),
        Section("Fit", [Row("Log-likelihood", [fmt(f.llf, 1) for f in cols]), Row("AIC", [fmt(f.aic, 1) for f in cols]),
                        Row("BIC", [fmt(f.bic, 1) for f in cols]), Row("Observations", [f"{f.nobs:,}" for f in cols]),
                        Row("Sample", [f"{_ym(f.index[0])}-{_ym(f.index[-1])}" for f in cols])]),
    ]
    return Table(
        key="regimes", title="Two-regime Markov-switching models of monthly real S&P 500 returns", columns=list(fits),
        sections=sections,
        notes=["Maximum-likelihood estimates; standard errors in parentheses from the numerical Hessian. The bear regime "
               "is the regime with the lower mean. Switching mean and variance; the AR(1) coefficient is common to both "
               "regimes. Returns are 100 times the log change in the real price index. " + STAR_NOTE
               + " Stars are shown only for tests against zero that are meaningful (means, AR term)."],
        stub_width="2.2fr",
    )


def tvtp_slopes(fit: RegimeFit) -> dict[tuple[str, str], Coef]:
    """TVTP slopes as effects on logit P(bull to bull) ('stay') and logit P(bear to bull) ('exit').

    statsmodels models P(S_t = 0 | S_{t-1} = i); when regime 0 is the bear regime the
    probabilities of interest are complements, which flips the sign of the logit coefficients.
    """
    bull = 1 - fit.bear
    out = {}
    for j, key in enumerate(fit.tvtp_keys, start=1):
        if bull == 0:
            stay, exit_ = fit.coefs[f"p[0->0].tvtp{j}"], fit.coefs[f"p[1->0].tvtp{j}"]
            out[("stay", key)], out[("exit", key)] = stay, exit_
        else:
            stay, exit_ = fit.coefs[f"p[1->0].tvtp{j}"], fit.coefs[f"p[0->0].tvtp{j}"]
            out[("stay", key)] = Coef(-stay.estimate, stay.se, stay.pvalue)
            out[("exit", key)] = Coef(-exit_.estimate, exit_.se, exit_.pvalue)
    return out


def lr_test(fit: RegimeFit, fixed: RegimeFit) -> tuple[float, int, float]:
    stat = 2 * (fit.llf - fixed.llf)
    df = len(fit.params) - len(fixed.params)
    return stat, df, float(1 - stats.chi2.cdf(stat, df))


def tvtp_table(fixed: RegimeFit, tvtps: dict[str, RegimeFit], quality: dict[str, float]) -> Table:
    fits = [fixed, *tvtps.values()]
    names = ["Fixed transitions", *tvtps]
    slopes = [tvtp_slopes(f) if f.kind == "tvtp" else {} for f in fits]
    sections = []
    for kind, title in (("stay", "Logit of P(bull to bull): slope on lagged predictor"),
                        ("exit", "Logit of P(bear to bull): slope on lagged predictor")):
        rows = []
        for key in TVTP_KEYS:
            rows += coef_rows(FEATURE_LABELS[key], [s.get((kind, key)) for s in slopes], 2)
        sections.append(Section(title, rows))
    lrs = [lr_test(f, fixed) if f.kind == "tvtp" else None for f in fits]
    sections.append(Section("Regimes (transition probabilities at the predictors' sample means)", [
        Row("Bull mean / bear mean (%)", [f"{fmt(f.means[0], 2)} / {fmt(f.means[1], 2)}" for f in fits]),
        Row("Bull sd / bear sd (%)", [f"{fmt(np.sqrt(f.variances[0]), 2)} / {fmt(np.sqrt(f.variances[1]), 2)}" for f in fits]),
        Row("P(bull to bull)", [fmt(f.transition[0, 0], 3) for f in fits]),
        Row("P(bear to bear)", [fmt(f.transition[1, 1], 3) for f in fits]),
    ]))
    sections.append(Section("Fit", [
        Row("Log-likelihood", [fmt(f.llf, 1) for f in fits]),
        Row("LR statistic against fixed (df)", ["" if lr is None else f"{fmt(lr[0], 1)} ({lr[1]})" for lr in lrs]),
        Row("LR p-value", ["" if lr is None else fmt_p(lr[2]) for lr in lrs]),
        Row("AIC", [fmt(f.aic, 1) for f in fits]),
        Row("BIC", [fmt(f.bic, 1) for f in fits]),
        Row("AUC of filtered bear probability", [fmt(quality[n], 3) for n in names]),
    ]))
    return Table(
        key="tvtp", title="Markov-switching models with time-varying transition probabilities",
        columns=names, sections=sections,
        notes=[f"MS-AR(1) models of monthly real returns, {_ym(fixed.index[0])}-{_ym(fixed.index[-1])}. In the TVTP "
               "models the probability of moving from regime i at t - 1 to the bull regime at t is a logistic function "
               "of the standardized predictors at t - 1 (Diebold, Lee and Weinbach, 1994; Filardo, 1994). Slopes are "
               "per one standard deviation, with standard errors from the numerical Hessian in parentheses. The "
               "likelihood-ratio test compares each model with fixed transitions (chi-squared with two degrees of "
               "freedom per predictor). AUC compares the filtered bear-regime probability with the dated bear state "
               "(in sample). " + STAR_NOTE],
        stub_width="2.2fr", size="7.5pt",
    )


def original_spec_table(ols: dict, beta: dict, horizons: tuple[int, ...]) -> Table:
    sections = []
    for f in ORIGINAL_FEATURES:
        rows = coef_rows(f.label, [ols[(f.key, h)].coefs[f.key] for h in horizons] + [beta[(f.key, h)].coefs[f.key] for h in horizons])
        rows.append(Row("R² / pseudo-R²", [fmt(ols[(f.key, h)].stats["r2"], 3) for h in horizons]
                        + [fmt(beta[(f.key, h)].stats["pseudo_r2"], 3) for h in horizons]))
        sections.append(Section(None, rows))
    k0 = ORIGINAL_FEATURES[0].key
    sections.append(Section(None, [Row("Observations", [f"{ols[(k0, h)].nobs:,}" for h in horizons] + [f"{beta[(k0, h)].nobs:,}" for h in horizons])]))
    lags = sorted({ols[(k0, h)].stats["nw_lags"] for h in horizons})
    first = ols[(k0, horizons[0])]
    return Table(
        key="original_spec", title="Corrected award-version design: regime probability h months ahead on each predictor",
        columns=[_h(h) for h in horizons] * 2,
        groups=[("OLS (percentage points)", len(horizons)), ("Beta regression (logit link)", len(horizons))], sections=sections,
        notes=["Each cell is a separate univariate regression of the filtered bear-regime probability Q(t+h) from the "
               "MS-AR(1) model on the standardized predictor at t. OLS coefficients are in percentage points of "
               f"probability. Newey-West standard errors in parentheses ({', '.join(str(int(x)) for x in lags)} lags by "
               f"horizon). Forecast origins {_ym(first.start)} to {_ym(first.end)} for h = {horizons[0]}. The beta-"
               "regression pseudo-R² is the squared correlation of the linear predictor with logit(Q). " + STAR_NOTE
               + " Q uses full-sample parameters, so these are in-sample associations, not forecasts."],
        stub_width="2.1fr", size="8pt",
    )


SECTIONS_B = (("Valuation", ("log_dy", "log_cape")), ("Macroeconomic", ("infl_yoy", "d_rate_12")), ("Market", ("mom_12", "vol_12")))


def logit_table(logit: dict[int, FitSummary], probit: dict[int, FitSummary], horizons: tuple[int, ...]) -> Table:
    fits = [logit[h] for h in horizons] + [probit[h] for h in horizons]
    sections = []
    for title, keys in SECTIONS_B:
        rows = []
        for k in keys:
            rows += coef_rows(FEATURE_LABELS[k], [f.coefs[k] for f in fits], 2)
        sections.append(Section(title, rows))
    sections.append(Section(None, coef_rows("Constant", [f.coefs["const"] for f in fits], 2) + [
        Row("Pseudo-R² (McFadden)", [fmt(f.stats["pseudo_r2"], 3) for f in fits]),
        Row("Log-likelihood", [fmt(f.stats["llf"], 1) for f in fits]),
        Row("Observations", [f"{f.nobs:,}" for f in fits]),
    ]))
    lags = ", ".join(str(int(f.stats["nw_lags"])) for f in fits[: len(horizons)])
    return Table(
        key="logit", title="Full-sample logit and probit models of a dated bear market h months ahead",
        columns=[_h(h) for h in horizons] * 2, groups=[("Logit", len(horizons)), ("Probit", len(horizons))], sections=sections,
        notes=["Dependent variable: 1 if month t+h lies in a dated bear market. Predictors are measured at t and "
               f"standardized. Newey-West standard errors in parentheses ({lags} lags by horizon). Forecast origins "
               f"{_ym(fits[0].start)} to {_ym(fits[0].end)} for h = {horizons[0]}. " + STAR_NOTE
               + " In-sample estimates over the whole period, not real-time forecasts."],
        stub_width="2.3fr", size="8pt",
    )


def oos_table(met: pd.DataFrame, models: tuple[str, ...], horizons: tuple[int, ...], key: str, title: str, extra_note: str = "") -> Table:
    sections = []
    for h in horizons:
        rows = []
        for m in models:
            r = met.loc[(h, m)]
            rows.append(Row(MODEL_LABELS[m], [fmt(r.brier, 3), fmt(100 * r.bss, 1), fmt(r.log_loss, 3), fmt(r.auc, 3),
                                              "" if m == "uncond" else fmt_p(r.p_uncond),
                                              "" if m in BASELINES else fmt_p(r.p_persist),
                                              "" if m in BASELINES else fmt_p(r.p_persist_long)]))
        n, share = int(met.loc[(h, "uncond"), "n"]), met.loc[(h, "uncond"), "bear_share"]
        sections.append(Section(f"h = {h} ({n} forecasts, bear share {fmt(100 * share, 1)}%)", rows))
    return Table(
        key=key, title=title, columns=["Brier", "Skill (%)", "Log loss", "AUC", "p vs uncond.", "p vs persist.", f"p vs persist., {BLOCK - 1} lags"],
        sections=sections,
        notes=["Expanding-window forecasts made at each month-end origin using only data available then: predictors with "
               "publication lags, bear dates obtained from prices through the origin, and models re-estimated on that "
               "information. Lower Brier score and log loss are better; skill is the percentage reduction in Brier score "
               f"relative to the unconditional frequency. Log loss truncates probabilities to [{LOG_LOSS_FLOOR:g}, "
               f"{1 - LOG_LOSS_FLOOR:g}]. The p-values are one-sided Diebold-Mariano tests (Harvey-Leybourne-Newbold "
               "correction) of equal Brier score against the alternative that the model is more accurate than the "
               "baseline, with the conventional max(h - 1, 1) Bartlett lags; the last column uses "
               f"{BLOCK - 1} lags, which allows for the strong autocorrelation of loss differences during long bear "
               "markets." + extra_note],
        stub_width="2.5fr", widths=["0.7fr", "0.7fr", "0.7fr", "0.6fr", "0.8fr", "0.8fr", "1fr"], size="8pt",
    )


def murphy_table(murphy: pd.DataFrame, models: tuple[str, ...], horizons: tuple[int, ...]) -> Table:
    rows = []
    for m in models:
        cells = []
        for h in horizons:
            r = murphy.loc[(h, m)]
            cells += [fmt(100 * r.reliability, 2), fmt(100 * r.resolution, 2)]
        rows.append(Row(MODEL_LABELS[m], cells))
    unc = Row("Uncertainty (all models)", sum(([fmt(100 * murphy.loc[(h, models[0])].uncertainty, 2), ""] for h in horizons), []))
    rem = max(abs(murphy.loc[(h, m)].remainder) for h in horizons for m in models)
    return Table(
        key="murphy", title="Murphy decomposition of out-of-sample Brier scores (x 100)",
        columns=["Rel.", "Res."] * len(horizons), groups=[(_h(h), 2) for h in horizons],
        sections=[Section(None, rows), Section(None, [unc])],
        notes=["Brier = reliability - resolution + uncertainty (Murphy, 1973), with forecasts grouped into "
               f"{MURPHY_BINS} equal-width bins. Reliability (lower is better) measures miscalibration; resolution "
               "(higher is better) measures how much the observed bear frequency varies across forecast bins. The "
               "remainder due to variation of forecasts within bins is at most "
               f"{fmt(100 * rem, 2)} (x 100) in absolute value."],
        stub_width="2.5fr", size="8pt",
    )


def inference_table(mcs: pd.DataFrame, models: tuple[str, ...], horizons: tuple[int, ...], block: int) -> Table:
    rows = []
    for m in models:
        cells = []
        for h in horizons:
            p = mcs.loc[(h, m), "p_mcs"]
            cells.append(fmt(p, 3) + ("*" if p >= 0.10 else ""))
        rows.append(Row(MODEL_LABELS[m], cells, "coef"))
    return Table(
        key="mcs", title="Model confidence set p-values for out-of-sample Brier loss",
        columns=[_h(h) for h in horizons], sections=[Section(None, rows)],
        notes=[f"Hansen, Lunde and Nason (2011) T_max procedure on squared forecast errors, circular block bootstrap "
               f"with {block}-month blocks and {BOOT_REPS:,} draws. A star marks models in the 90% model confidence "
               "set (p >= 0.10): the set of models that cannot be distinguished from the best at the 10% level."],
        stub_width="2.6fr", size="8pt",
    )


def spa_table(spa: pd.DataFrame, gw: pd.DataFrame, horizons: tuple[int, ...]) -> Table:
    rows = [Row(r.label, [str(int(r.n_models)), MODEL_LABELS.get(r.best, r.best), fmt_p(r.p_consistent), fmt_p(r.p_upper)])
            for r in spa.itertuples()]
    sections = [Section("Superior predictive ability against persistence", rows)]
    rows = []
    for h in horizons:
        r = gw.loc[h]
        rows.append(Row(f"h = {h}", ["", MODEL_LABELS[r.model], fmt_p(r.p_gw), f"{fmt(r.stat, 2)} ({fmt_p(r.p_dm_long)})"]))
    sections.append(Section("Conditional predictive ability: best model against persistence", rows))
    return Table(
        key="spa", title="Tests of superior and conditional predictive ability against persistence",
        columns=["Models", "Best model", "p-value", "Reality Check p / GW stat (DM p)"], sections=sections,
        notes=["Upper panel: Hansen (2005) consistent SPA p-value and White (2000) Reality Check p-value for the null "
               "that no model has lower expected Brier loss than persistence, circular block bootstrap with "
               f"{BLOCK}-month blocks and {BOOT_REPS:,} draws; 'Best model' has the largest studentized gain. The joint "
               "rows treat every (model, horizon) pair as a separate forecast on the origins common to all horizons. "
               "Lower panel: Giacomini and White (2006) Wald test of equal conditional accuracy of the most accurate "
               "model and persistence, with test functions (1, real-time bear state) known at the origin and a "
               f"Bartlett long-run variance with {BLOCK - 1} lags; the last column gives the statistic and, in "
               f"parentheses, the one-sided unconditional Diebold-Mariano p-value with the same {BLOCK - 1} lags."],
        stub_width="1.9fr", widths=["0.5fr", "2.7fr", "0.6fr", "1.2fr"], size="8pt",
    )


def combination_table(comb: pd.DataFrame, horizons: tuple[int, ...]) -> Table:
    rows = [Row(r.label, [fmt(100 * r[f"bss_h{h}"], 1) + stars(r[f"p_h{h}"]) for h in horizons], "coef")
            for _, r in comb.iterrows()]
    return Table(
        key="combination", title="Forecast combinations: out-of-sample Brier skill (%)",
        columns=[_h(h) for h in horizons], sections=[Section(None, rows)],
        notes=["The equal-weight combination averages the univariate logits. Dynamic model averaging (Raftery, Kárný "
               "and Ettler, 2010) weights forecasts by their exponentially discounted predictive likelihood, using only "
               "outcomes known at the origin; alpha is the forgetting factor (alpha = 1 is recursive Bayesian model "
               "averaging). " + DM_STARS],
        stub_width="2.8fr", size="8pt",
    )


def mspe_table(archived: pd.DataFrame, corrected: pd.DataFrame, horizons: tuple[int, ...], period: str) -> Table:
    def grid(df: pd.DataFrame, value: str, keys: list[str], labels: dict[str, str], cw: bool) -> list[Row]:
        rows = []
        for key in keys:
            cells = []
            for model in ("OLS", "Beta"):
                for h in horizons:
                    r = df[(df.model == model) & (df.predictor == key) & (df.k == h)].iloc[0]
                    cells.append(fmt(r[value], 3) + (stars(r.cw_p) if cw else ""))
            rows.append(Row(labels[key], cells, "coef" if cw else "stat"))
        return rows

    corr_keys = ORIGINAL_KEYS + ["q_now"]
    labels_c = {f.key: f.label for f in ORIGINAL_FEATURES} | {"q_now": "Benchmark: regime probability at t"}
    return Table(
        key="mspe", title="Forecasting the regime probability: unrestricted versus intercept-only models",
        columns=[_h(h) for h in horizons] * 2, groups=[("OLS", len(horizons)), ("Beta regression", len(horizons))],
        sections=[
            Section("A. Award-version design and formula (squared mean error ratio)", grid(archived, "archived_ratio", list(ARCHIVED_PREDICTORS), ARCHIVED_PREDICTORS, False)),
            Section("B. Award-version design, correct mean squared prediction error ratio", grid(archived, "mspe_ratio", list(ARCHIVED_PREDICTORS), ARCHIVED_PREDICTORS, False)),
            Section("C. Corrected design: past-only predictors, true h-month lead, expanding window", grid(corrected, "mspe_ratio", corr_keys, labels_c, True)),
        ],
        notes=["Entries are ratios of the unrestricted model's loss to the intercept-only model's loss; values below one "
               "favor the predictor. Panels A and B re-run the award version's code path on one45.csv (target Q(t-k), "
               "regime model with the next month's price, single 80/20 split with the test period starting in 2011). "
               "Panel A uses its formula (mean error)² / (mean error)², which is not a mean squared error. Panel C "
               f"forecasts Q(t+h) from predictors observable at t with expanding-window refits on the Shiller data, "
               f"origins {period}. The benchmark row uses Q(t) itself as the predictor. Stars in Panel C mark Clark-West "
               "(2007) tests: * p < 0.10, ** p < 0.05, *** p < 0.01."],
        stub_width="2.3fr", size="8pt",
    )


def replication_table(rep: pd.DataFrame) -> Table:
    return Table(
        key="replication", title="Award-version results, their replication, and the corrected estimates",
        columns=["Award version (reported)", "Replicated", "Corrected"],
        sections=[Section(None, [Row(r.label, [r.reported, r.replicated, r.corrected]) for r in rep.itertuples()])],
        notes=["Reported values are transcribed from the award PDF (v2/data/archived_reported.csv). 'Replicated' re-runs "
               "the award version's code path on one45.csv, including the future-price regressor, the backward target "
               "Q(t-k) and its loss ratio. 'Corrected' uses the MS-AR(1) model on returns from the Shiller workbook, "
               "past-only predictors, the forward target Q(t+k) and expanding-window forecasts. Corrected coefficients "
               "are per one-standard-deviation change of a growth-rate transformation and are comparable in sign and "
               "significance only."],
        stub_width="2.6fr",
    )


def summary_table(met: pd.DataFrame, horizons: tuple[int, ...], models: tuple[str, ...], challengers: tuple[str, ...]) -> Table:
    """Compact Brier-score summary for the README."""
    rows = []
    for h in horizons:
        cells = [fmt(met.loc[(h, m)].brier, 3) if m == "uncond" else
                 f"{fmt(met.loc[(h, m)].brier, 3)} ({fmt(100 * met.loc[(h, m)].bss, 1)}%)" for m in models]
        cells.append(fmt_p(min(met.loc[(h, m), "p_persist_long"] for m in challengers)))
        rows.append(Row(f"{h} month{'s' if h > 1 else ''}", cells))
    return Table(
        key="summary", title="Out-of-sample Brier scores (skill relative to the unconditional frequency)",
        columns=[MODEL_LABELS[m] for m in models] + ["Best p vs persistence"], sections=[Section(None, rows)],
        notes=[f"Lower is better. Real-time expanding-window forecasts. The last column is the smallest one-sided "
               f"Diebold-Mariano p-value ({BLOCK - 1} Bartlett lags) against persistence among the {len(challengers)} "
               "non-baseline models of the main design, not adjusted for multiple comparisons."],
        stub="Horizon",
    )


ROBUST_LABELS = {"persist": "Persistence", "ms": "MS-AR(1)", "logit_dy": "Logit: dividend yield",
                 "logit_all": f"Logit: {len(FORECAST_KEYS)} main predictors"}


def _skill_cell(r: pd.Series) -> str:
    return fmt(100 * r.bss, 1) + stars(r.p_uncond)


def regime_spec_table(specs: list[SpecSummary], quality: list[dict[str, float]], main_label: str) -> Table:
    def per_regime(attr: str, digits: int, which: int) -> list[str]:
        out = []
        for s in specs:
            vals = getattr(s, attr)
            if s.k == 2:
                out.append("" if which == 1 else fmt(vals[0 if which == 0 else 1], digits))
            else:
                out.append(fmt(vals[which], digits))
        return out

    def block(title: str, attr: str, digits: int) -> Section:
        return Section(title, [Row("Bull (highest mean)", per_regime(attr, digits, 0)),
                               Row("Middle (three regimes)", per_regime(attr, digits, 1)),
                               Row("Bear (lowest mean)", per_regime(attr, digits, 2))])

    return Table(
        key="regime_specs", title="Robustness of the regime model: specification and sample", columns=[s.name for s in specs],
        sections=[
            block("Mean monthly real return (%)", "means", 2), block("Volatility (sd, %)", "sds", 2),
            block("Expected duration (months)", "durations", 1),
            Section("Fit", [Row("AR(1) coefficient", [fmt(s.ar, 3) if s.ar is not None else "" for s in specs]),
                            Row("Parameters", [str(s.n_params) for s in specs]), Row("Log-likelihood", [fmt(s.llf, 1) for s in specs]),
                            Row("AIC", [fmt(s.aic, 1) for s in specs]), Row("BIC", [fmt(s.bic, 1) for s in specs]),
                            Row("Observations", [f"{s.nobs:,}" for s in specs])]),
            Section("Filtered bear probability against the dated bear state", [Row("AUC", [fmt(q["auc"], 3) for q in quality]),
                                                                              Row("Correlation", [fmt(q["corr"], 2) for q in quality])]),
        ],
        notes=[f"Two-regime models unless stated; monthly real returns. The first five columns use {main_label}; AIC and "
               "BIC are comparable only within that group. 'Mean and variance' is the switching mean-variance model "
               "without the AR term; 'Variance only' lets only the variance switch (the bear regime is the high-variance "
               "one); 'Mean only' lets only the mean switch. In the three-regime model the bear regime has the lowest "
               "mean. The last two columns re-estimate the main MS-AR(1) on each subsample. AUC and correlation compare "
               "the filtered bear-regime probability with the contemporaneous dated bear indicator (in sample)."],
        stub_width="1.9fr", size="7.5pt",
    )


def robust_oos_table(variants: dict[str, pd.DataFrame], labels: dict[str, str], horizons: tuple[int, ...]) -> Table:
    sections = [Section(name, [Row(labels[key], [_skill_cell(met.loc[(h, m)]) for h in horizons], "coef")
                               for key, met in variants.items()]) for m, name in ROBUST_LABELS.items()]
    return Table(
        key="robust_oos", title="Robustness of out-of-sample Brier skill (%) to dating, estimation window and evaluation period",
        columns=[_h(h) for h in horizons], sections=sections,
        notes=["Skill is the percentage reduction in Brier score relative to the unconditional frequency estimated in the "
               "same variant. Each dating variant re-dates bear markets (symmetric thresholds) and re-runs the complete "
               "real-time exercise, including the vintage labels and the real-time state. The rolling variant estimates "
               f"every model on the most recent {ROLLING_WINDOW // 12} years of training data. The evaluation-period rows "
               f"score the main forecasts on subsets of target months; the crisis excluded is {_ym(CRISIS[0])}-"
               f"{_ym(CRISIS[1])}. " + DM_STARS],
        stub_width="2.4fr", size="8pt",
    )


def dating_table(summaries: dict[str, dict[str, float]], labels: dict[str, str], since: str, span: str) -> Table:
    rows = [Row(labels[k], [str(v["n_bears"]), str(v["n_bears_since"]), fmt(100 * v["bear_share_since"], 1),
                            fmt(v["median_decline"], 1)]) for k, v in summaries.items()]
    return Table(
        key="dating", title="Bear markets under alternative dating rules",
        columns=[f"Bear markets, {span}", f"Since {since}", f"Bear share since {since} (%)", "Median decline (%)"],
        sections=[Section(None, rows)],
        notes=["Symmetric thresholds: a bear market starts when the index falls the stated percentage below its peak and "
               "ends when it rises the same percentage above its trough. Nominal dating uses the S&P Composite monthly "
               "average price without deflating."],
        stub="Dating rule", stub_width="2fr",
    )


def predictors_table(met: pd.DataFrame, horizons: tuple[int, ...]) -> Table:
    def row(label: str, m: str) -> Row:
        return Row(label, [_skill_cell(met.loc[(h, m)]) for h in horizons] + [fmt(met.loc[(horizons[0], m)].auc, 3)], "coef")

    return Table(
        key="predictors", title="Out-of-sample Brier skill (%) of individual predictors and combinations",
        columns=[_h(h) for h in horizons] + ["AUC, h = 1"],
        sections=[
            Section("Baseline", [row("Persistence", "persist")]),
            Section("Univariate logits: main predictors", [row(FEATURE_LABELS[k], f"uni_{k}") for k in FORECAST_KEYS]),
            Section("Univariate logits: additional predictors", [row(FEATURE_LABELS[k], f"uni_{k}") for k in EXTRA_KEYS]),
            Section("Multi-predictor forecasts", [
                row(f"Equal-weight combination ({len(ALL_KEYS)} univariate logits)", "combo"),
                row(f"DMA of the {len(ALL_KEYS)} univariate logits", "dma_uni"),
                row(f"Logit: all {len(ALL_KEYS)} predictors", "logit_ext"),
            ]),
        ],
        notes=["Real-time expanding-window forecasts with the main dating rule; every model is re-estimated at each origin "
               "on data available then. Skill is relative to the unconditional frequency. " + DM_STARS],
        stub_width="2.8fr", size="8pt",
    )


def bootstrap_table(boot: pd.DataFrame, models: tuple[str, ...], horizons: tuple[int, ...]) -> Table:
    sections = []
    for h in horizons:
        rows = []
        for m in models:
            r = boot.loc[(h, m)]
            rows.append(Row(MODEL_LABELS[m], [fmt(100 * r.bss, 1), f"[{fmt(100 * r.bss_lo, 1)}, {fmt(100 * r.bss_hi, 1)}]",
                                              "" if m == "persist" else f"[{fmt(100 * r.gain_lo, 1)}, {fmt(100 * r.gain_hi, 1)}]",
                                              "" if m == "persist" else fmt(r.share_beats_persist, 2)]))
        sections.append(Section(f"h = {h}", rows))
    return Table(
        key="bootstrap", title="Block-bootstrap uncertainty of out-of-sample Brier skill",
        columns=["Skill (%)", "90% interval", "Gain over persistence (pp), 90% interval", "Share of draws beating persistence"],
        sections=sections,
        notes=[f"Circular moving-block bootstrap of target months with blocks of {BLOCK} months and {BOOT_REPS:,} "
               "replications, resampling all models jointly. Intervals are 5th and 95th percentiles. The gain over "
               "persistence is the model's skill minus the skill of persistence in the same draw."],
        stub_width="2.3fr", widths=["0.8fr", "1.1fr", "1.5fr", "1.2fr"], size="8pt",
    )


# =============================================================================================
# 12. Figures (one restrained style; Okabe-Ito colorblind-safe palette)
# =============================================================================================

INK, MUTED, GRID, SHADE = "#1a1a1a", "#5f5f5f", "#e3e3e3", "#d4d4d4"
MODEL_COLORS = {
    "logit_state": "#D55E00", "logit_all": "#0072B2", "ms": "#009E73", "persist": "#E69F00", "probit_all": "#56B4E9",
    "logit_dy": "#CC79A7", "uncond": "#8c8c8c", "tvtp": "#000000", "gbt_rich": "#D55E00", "enet_rich": "#56B4E9",
    "dma_all": "#009E73", "combo": "#CC79A7",
}
MODEL_MARKERS = {"tvtp": "D", "enet_rich": "^", "gbt_rich": "^", "dma_all": "s", "combo": "s"}
HORIZON_COLORS = {1: "#0072B2", 3: "#009E73", 6: "#E69F00", 12: "#D55E00"}
SOURCE = (f"Source: R. J. Shiller, U.S. Stock Markets 1871-Present and CAPE Ratio (shillerdata.com, "
          f"downloaded {SHILLER_DOWNLOADED}); author's calculations.")
FIGURE_MODELS = ("persist", "ms", "logit_dy", "logit_all")

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10, "axes.titleweight": "bold",
    "axes.titlelocation": "left", "axes.labelsize": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
    "axes.linewidth": 0.7, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.6, "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.frameon": False, "legend.fontsize": 8, "lines.linewidth": 1.4,
    "savefig.dpi": 300, "svg.fonttype": "none", "svg.hashsalt": "psm-v2", "figure.dpi": 100,
})


def _save(fig: plt.Figure, directory: Path, name: str) -> None:
    fig.text(0.01, -0.01, SOURCE, fontsize=6.5, color=MUTED, ha="left", va="top")
    directory.mkdir(parents=True, exist_ok=True)
    fig.savefig(directory / f"{name}.png", bbox_inches="tight", facecolor="white", metadata={"Software": None})
    fig.savefig(directory / f"{name}.svg", bbox_inches="tight", facecolor="white", metadata={"Date": None, "Creator": None})
    plt.close(fig)


def _spans(labels: pd.Series) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Contiguous runs of label == 1 as (first month, month after the last)."""
    spans, start, idx = [], None, labels.index
    for i, v in enumerate(labels.to_numpy()):
        if v == 1 and start is None:
            start = idx[i]
        if v != 1 and start is not None:
            spans.append((start, idx[i]))
            start = None
    if start is not None:
        spans.append((start, idx[-1] + pd.DateOffset(months=1)))
    return spans


def shade_bears(ax: plt.Axes, labels: pd.Series) -> None:
    for a, b in _spans(labels):
        ax.axvspan(a, b, color=SHADE, alpha=0.6, lw=0, zorder=0)


def _date_axis(ax: plt.Axes, years: int) -> None:
    ax.xaxis.set_major_locator(mdates.YearLocator(years))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.margins(x=0.005)


def _log_axis(ax: plt.Axes) -> None:
    ax.set_yscale("log")
    ax.yaxis.set_major_locator(LogLocator(base=10, subs=(1.0, 2.0, 5.0)))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_minor_formatter(NullFormatter())


def fig_price(price: pd.Series, labels: pd.Series, directory: Path, base: str) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    shade_bears(ax, labels)
    ax.plot(price.index, price, color=INK, lw=1.0)
    _log_axis(ax)
    ax.set_ylabel(f"Real price index, {base} dollars (log)")
    ax.set_title(f"Real S&P 500 and dated bear markets, {price.index[0]:%Y}-{price.index[-1]:%Y}")
    _date_axis(ax, 10)
    ax.text(0.01, 0.97, "Shaded: bear market (peak-to-trough decline of at least 20%)", transform=ax.transAxes,
            fontsize=7.5, color=MUTED, va="top")
    _save(fig, directory, "fig1_price_bears")


def fig_regime_probabilities(fit: RegimeFit, labels: pd.Series, directory: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 4.6), sharex=True)
    for ax, series, title in (
        (axes[0], fit.filtered, "Filtered probability P(bear regime at t | returns through t): usable in real time"),
        (axes[1], fit.smoothed, "Smoothed probability P(bear regime at t | all returns): retrospective dating only"),
    ):
        shade_bears(ax, labels.reindex(series.index))
        ax.fill_between(series.index, 0, series, color="#0072B2", alpha=0.25, lw=0)
        ax.plot(series.index, series, color="#0072B2", lw=0.8)
        ax.set_ylim(0, 1)
        ax.set_yticks([0, 0.5, 1])
        ax.set_ylabel("Probability")
        ax.set_title(title, fontsize=8.5, fontweight="normal")
    _date_axis(axes[1], 5)
    fig.suptitle(f"MS-AR(1) bear-regime probability, {fit.index[0]:%Y}-{fit.index[-1]:%Y} (shaded: dated bear markets)",
                 x=0.01, ha="left", fontsize=10, fontweight="bold")
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    _save(fig, directory, "fig2_regime_probabilities")


def fig_oos_paths(fc: pd.DataFrame, labels: pd.Series, horizons: tuple[int, ...], models: tuple[str, ...], directory: Path) -> None:
    fig, axes = plt.subplots(len(horizons), 1, figsize=(7.2, 1.9 * len(horizons) + 0.6), sharex=True)
    for ax, h in zip(np.atleast_1d(axes), horizons):
        sub = fc[fc.horizon == h]
        shade_bears(ax, labels.loc[sub.target_date.min(): sub.target_date.max()])
        for m in models:
            s = sub[sub.model == m].set_index("target_date")["p"]
            ax.plot(s.index, s, color=MODEL_COLORS[m], lw=1.0, label=MODEL_LABELS[m])
        ax.set_ylim(0, 1)
        ax.set_yticks([0, 0.5, 1])
        ax.set_ylabel("Probability")
        ax.set_title(f"{h}-month-ahead forecast of a bear market", fontsize=8.5, fontweight="normal")
    axes = np.atleast_1d(axes)
    handles, lbls = axes[0].get_legend_handles_labels()
    _date_axis(axes[-1], 5)
    fig.suptitle("Out-of-sample bear-market probabilities, expanding window (shaded: dated bear markets)",
                 x=0.01, ha="left", fontsize=10, fontweight="bold", y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.935))
    fig.legend(handles, lbls, loc="upper left", bbox_to_anchor=(0.01, 0.968), ncol=len(models), fontsize=7.5,
               handlelength=1.8, columnspacing=1.2)
    _save(fig, directory, "fig3_oos_forecasts")


def _panel_grid() -> tuple[plt.Figure, np.ndarray]:
    fig, axes = plt.subplots(2, 2, figsize=(6.4, 6.9), sharex=True, sharey=True)
    return fig, axes.ravel()


def _shared_legend(fig: plt.Figure, ax: plt.Axes) -> None:
    handles, lbls = ax.get_legend_handles_labels()
    fig.legend(handles, lbls, loc="upper left", ncol=2, bbox_to_anchor=(0.01, 0.965), fontsize=7.5, handlelength=1.8,
               columnspacing=1.2)


def fig_calibration(fc: pd.DataFrame, horizons: tuple[int, ...], models: tuple[str, ...], directory: Path) -> None:
    fig, axes = _panel_grid()
    for ax, h in zip(axes, horizons):
        ax.grid(True, axis="both")
        ax.plot([0, 1], [0, 1], color=MUTED, lw=0.8, ls=":")
        sub = fc[fc.horizon == h]
        for m in models:
            s = sub[sub.model == m]
            cal = calibration(s.p.to_numpy(), s.y.to_numpy(), bins=6)
            ax.plot(cal.forecast, cal.observed, color=MODEL_COLORS[m], marker="o", ms=4, lw=1.1, label=MODEL_LABELS[m])
        ax.set_title(f"h = {h} month{'s' if h > 1 else ''}", fontsize=9)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
    for ax in axes[2:]:
        ax.set_xlabel("Forecast probability")
    for ax in axes[::2]:
        ax.set_ylabel("Observed bear frequency")
    fig.suptitle("Calibration of out-of-sample forecasts (six forecast-quantile bins)", x=0.01, ha="left", fontsize=10,
                 fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    _shared_legend(fig, axes[0])
    _save(fig, directory, "fig4_calibration")


def fig_roc(fc: pd.DataFrame, horizons: tuple[int, ...], models: tuple[str, ...], met: pd.DataFrame, directory: Path) -> None:
    fig, axes = _panel_grid()
    for ax, h in zip(axes, horizons):
        ax.grid(True, axis="both")
        ax.plot([0, 1], [0, 1], color=MUTED, lw=0.8, ls=":")
        sub = fc[fc.horizon == h]
        for j, m in enumerate(models):
            s = sub[sub.model == m]
            fpr, tpr = roc_curve(s.p.to_numpy(), s.y.to_numpy())
            ax.plot(fpr, tpr, color=MODEL_COLORS[m], lw=1.2, label=MODEL_LABELS[m], drawstyle="steps-post")
            ax.text(0.97, 0.05 + 0.07 * (len(models) - 1 - j), f"AUC {met.loc[(h, m), 'auc']:.2f}", transform=ax.transAxes,
                    ha="right", fontsize=7.5, color=MODEL_COLORS[m], fontweight="bold")
        ax.set_title(f"h = {h} month{'s' if h > 1 else ''}", fontsize=9)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
    for ax in axes[2:]:
        ax.set_xlabel("False-positive rate")
    for ax in axes[::2]:
        ax.set_ylabel("True-positive rate")
    fig.suptitle("ROC curves of out-of-sample bear-market forecasts", x=0.01, ha="left", fontsize=10, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    _shared_legend(fig, axes[0])
    _save(fig, directory, "fig5_roc")


def fig_forest(fits: dict[int, FitSummary], directory: Path) -> None:
    keys = [k for k in next(iter(fits.values())).coefs if k != "const"]
    fig, ax = plt.subplots(figsize=(7.2, 0.55 * len(keys) + 1.4))
    ax.grid(True, axis="x")
    ax.grid(False, axis="y")
    ax.axvline(0, color=MUTED, lw=0.8)
    for (h, fit), off in zip(fits.items(), np.linspace(-0.27, 0.27, len(fits))):
        y = np.arange(len(keys))[::-1] + off
        est = np.array([fit.coefs[k].estimate for k in keys])
        lo, hi = np.array([fit.coefs[k].ci() for k in keys]).T
        ax.errorbar(est, y, xerr=[est - lo, hi - est], fmt="o", ms=4.5, color=HORIZON_COLORS[h], elinewidth=1.2,
                    capsize=0, label=f"h = {h}")
    ax.set_yticks(np.arange(len(keys))[::-1])
    ax.set_yticklabels([FEATURE_LABELS[k] for k in keys])
    ax.set_xlabel("Logit coefficient per one-standard-deviation change (95% Newey-West interval)")
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=len(fits), fontsize=7.5)
    ax.set_title("Predictors of a bear market h months ahead, full-sample logit", pad=22)
    _save(fig, directory, "fig6_logit_forest")


def fig_replication(pairs: dict[str, pd.DataFrame], directory: Path) -> None:
    fig, axes = plt.subplots(1, len(pairs), figsize=(7.2, 2.7))
    for ax, (title, df) in zip(axes, pairs.items()):
        ax.grid(True, axis="both")
        lo, hi = min(df.reported.min(), df.replicated.min()), max(df.reported.max(), df.replicated.max())
        pad = 0.05 * (hi - lo)
        ax.plot([lo - pad, hi + pad], [lo - pad, hi + pad], color=MUTED, lw=0.8, ls=":")
        ax.scatter(df.reported, df.replicated, s=14, color="#0072B2", edgecolor="white", linewidth=0.5, zorder=3)
        ax.set_title(title, fontsize=8.5, fontweight="normal")
        ax.set_xlabel("Award version (reported)")
        ax.text(0.04, 0.95, f"n = {len(df)}, corr = {np.corrcoef(df.reported, df.replicated)[0, 1]:.3f}",
                transform=ax.transAxes, fontsize=7.5, color=INK, va="top")
    axes[0].set_ylabel("Replicated (Python)")
    fig.suptitle("Replication of the award version's code path on its archived data", x=0.01, ha="left", fontsize=10,
                 fontweight="bold")
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    _save(fig, directory, "fig7_replication")


def fig_skill_intervals(boot: pd.DataFrame, models: tuple[str, ...], horizons: tuple[int, ...], directory: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 3.3))
    ax.axhline(0, color=MUTED, lw=0.8, ls="--")
    x = np.arange(len(horizons))
    for m, off in zip(models, np.linspace(-0.24, 0.24, len(models))):
        est = np.array([100 * boot.loc[(h, m), "bss"] for h in horizons])
        lo = np.array([100 * boot.loc[(h, m), "bss_lo"] for h in horizons])
        hi = np.array([100 * boot.loc[(h, m), "bss_hi"] for h in horizons])
        ax.errorbar(x + off, est, yerr=[est - lo, hi - est], fmt="o", ms=4.5, color=MODEL_COLORS[m], elinewidth=1.2,
                    capsize=0, label=MODEL_LABELS[m])
    ax.set_xticks(x)
    ax.set_xticklabels([f"{h} month{'s' if h > 1 else ''}" for h in horizons])
    ax.set_xlabel("Forecast horizon")
    ax.set_ylabel("Brier skill vs unconditional (%)")
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=len(models), fontsize=7.5)
    ax.set_title(f"Out-of-sample skill with 90% block-bootstrap intervals ({BLOCK}-month blocks)", pad=22)
    _save(fig, directory, "fig8_skill_intervals")


def fig_tvtp(fit: RegimeFit, fixed: RegimeFit, labels: pd.Series, directory: Path) -> None:
    """In-sample probability of leaving the bull regime: time-varying against fixed."""
    s = fit.p_bull_bear
    fig, ax = plt.subplots(figsize=(7.2, 2.9))
    shade_bears(ax, labels.reindex(s.index))
    ax.plot(s.index, s, color=INK, lw=0.9, label="TVTP: P(bull to bear) given predictors at t - 1")
    ax.axhline(fixed.transition[0, 1], color="#E69F00", lw=1.2, ls="--", label="Fixed transitions: P(bull to bear)")
    ax.set_ylim(0, 1)
    ax.set_ylabel("Probability")
    _date_axis(ax, 5)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, fontsize=7.5)
    ax.set_title("TVTP model: probability of switching from bull to bear (in sample)", pad=22)
    _save(fig, directory, "fig9_tvtp")


def fig_murphy(murphy: pd.DataFrame, models: tuple[str, ...], horizons: tuple[int, ...], directory: Path) -> None:
    """Resolution against reliability for each model and horizon."""
    fig, axes = plt.subplots(1, len(horizons), figsize=(7.2, 2.9), sharey=False)
    for ax, h in zip(axes, horizons):
        ax.grid(True, axis="both")
        for m in models:
            r = murphy.loc[(h, m)]
            ax.scatter(100 * r.reliability, 100 * r.resolution, s=24, color=MODEL_COLORS.get(m, MUTED),
                       marker=MODEL_MARKERS.get(m, "o"),
                       edgecolor="white", linewidth=0.5, zorder=3, label=MODEL_LABELS[m])
        ax.set_title(f"h = {h}", fontsize=9)
        ax.set_xlabel("Reliability (x 100)")
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)
    axes[0].set_ylabel("Resolution (x 100)")
    handles, lbls = axes[0].get_legend_handles_labels()
    fig.suptitle("Murphy decomposition: resolution (higher is better) against reliability (lower is better)",
                 x=0.01, ha="left", fontsize=10, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.8))
    fig.legend(handles, lbls, loc="upper left", bbox_to_anchor=(0.01, 0.92), ncol=4, fontsize=7, handlelength=1.2,
               columnspacing=1.0)
    _save(fig, directory, "fig10_murphy")


def fig_hero(price: pd.Series, labels: pd.Series, fc: pd.DataFrame, model: str, horizon: int, directory: Path) -> None:
    """README figure: real price with dated bears above the real-time forecast."""
    def path(m: str) -> pd.Series:
        return fc[(fc.horizon == horizon) & (fc.model == m)].set_index("target_date")["p"]

    sub, base = path(model), path("persist")
    p = price.loc[sub.index.min(): sub.index.max()]
    lab = labels.loc[p.index]
    fig, axes = plt.subplots(2, 1, figsize=(8, 4.6), sharex=True, gridspec_kw={"height_ratios": [1.3, 1]})
    shade_bears(axes[0], lab)
    axes[0].plot(p.index, p, color=INK, lw=1.0)
    _log_axis(axes[0])
    axes[0].set_ylabel("Real S&P 500 (log)")
    axes[0].set_title("Real S&P 500 with dated bear markets (shaded)", fontsize=9, fontweight="normal")
    shade_bears(axes[1], lab)
    axes[1].plot(sub.index, sub, color=MODEL_COLORS[model], lw=1.1, label=MODEL_LABELS[model], zorder=3)
    axes[1].plot(base.index, base, color=MODEL_COLORS["persist"], lw=0.9, label=MODEL_LABELS["persist"])
    axes[1].set_ylim(0, 1)
    axes[1].set_yticks([0, 0.5, 1])
    axes[1].set_ylabel("Probability")
    axes[1].set_title(f"Real-time {horizon}-month-ahead bear-market probability (out of sample)", fontsize=9, fontweight="normal")
    axes[1].legend(loc="lower right", bbox_to_anchor=(1, 1.0), fontsize=7.5, ncol=2)
    _date_axis(axes[1], 5)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    _save(fig, directory, "hero")


# =============================================================================================
# 13. Pipeline stages
# =============================================================================================


def save_stage(name: str, obj: dict) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    with (CACHE / f"{name}.pkl").open("wb") as fh:
        pickle.dump(obj, fh, protocol=pickle.HIGHEST_PROTOCOL)


def load_stage(name: str) -> dict:
    path = CACHE / f"{name}.pkl"
    if not path.exists():
        raise SystemExit(f"{path} not found: run `python thesis.py {name}` first")
    with path.open("rb") as fh:
        return pickle.load(fh)


def results_dir() -> Path:
    path = OUTPUT / "results"
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_csv(frame: pd.DataFrame, name: str, **kwargs: Any) -> None:
    """CSV output with fixed float formatting; '.gz' files are written without a timestamp."""
    path = results_dir() / name
    if name.endswith(".gz"):
        kwargs["compression"] = {"method": "gzip", "mtime": 0}
    frame.to_csv(path, float_format="%.8g", **kwargs)


def stage_data() -> dict:
    """Shiller workbook -> validated panel, comparison with one45.csv, predictors, bear dating."""
    shiller = load_shiller()
    panel = shiller.panel
    one45 = load_one45()
    comparison, differences = compare_with_one45(shiller.frame, one45)
    audit = audit_archived_leads(one45)
    price = real_price_index(panel).dropna()
    idx = price.index
    returns = real_returns(panel).reindex(idx)
    features = build_features(panel).reindex(idx)
    labels = label_series(price)
    ep = episodes(price)
    cpi_end = float(panel["cpi"].iloc[-1])
    columns = pd.DataFrame([{"sheet": SHILLER_SHEET, "column": pos, "name": name, "heading": heading,
                             "description": SHILLER_DESCRIPTIONS[name]} for pos, (name, heading) in SHILLER_COLUMNS.items()])
    write_csv(columns, "shiller_columns.csv", index=False)
    write_csv(panel, "shiller_panel.csv", index_label="date")
    write_csv(pd.concat([(price * cpi_end).rename("real_price"), returns, labels, features], axis=1), "panel.csv",
              index_label="date")
    write_csv(ep, "episodes.csv", index=False)
    write_csv(comparison, "one45_comparison.csv", index=False)
    write_csv(differences, "one45_differences.csv", index=False)
    write_csv(audit, "archived_lead_audit.csv", index=False)
    info = {
        "url": SHILLER_URL, "page": SHILLER_PAGE, "sha256": sha256(SHILLER_FILE), "bytes": SHILLER_FILE.stat().st_size,
        "downloaded": SHILLER_DOWNLOADED, "last_modified": SHILLER_LAST_MODIFIED, "sheet": SHILLER_SHEET,
        "first": shiller.frame.index[0], "last_row": shiller.frame.index[-1], "end": shiller.end,
        "footnotes": shiller.footnotes,
    }
    log(f"data: Shiller workbook {info['first']:%Y-%m} to {info['last_row']:%Y-%m}, sample ends {shiller.end:%Y-%m}")
    return {"info": info, "panel": panel, "one45": one45, "comparison": comparison, "differences": differences,
            "audit": audit, "price": price, "returns": returns, "features": features, "labels": labels,
            "episodes": ep, "nominal": panel["price"].reindex(idx), "cpi_end": cpi_end}


def stage_models(d: dict) -> dict:
    """In-sample models: regimes (fixed and time-varying transitions, alternative specifications),
    logit and probit, the award-version design corrected, and the replication of its code path."""
    returns, features, labels = d["returns"], d["features"], d["labels"]
    main = returns.loc[MAIN_START:]
    end = returns.index[-1]
    span_main, span_full = f"{MAIN_START:%Y}-{end:%Y}", f"{returns.index[1]:%Y}-{end:%Y}"
    fits = {
        f"MS, {span_main}": fit_regimes(main, "mean_var"),
        f"MS-AR(1), {span_main}": fit_regimes(main, "ar1"),
        f"MS, {span_full}": fit_regimes(returns, "mean_var"),
        f"MS-AR(1), {span_full}": fit_regimes(returns, "ar1"),
    }
    ar1, mv = fits[f"MS-AR(1), {span_main}"], fits[f"MS, {span_main}"]
    log("models: Markov-switching regimes")

    tvtp = {FEATURE_LABELS[k]: fit_tvtp(main, features, keys=(k,), fixed=ar1) for k in TVTP_KEYS}
    tvtp["All four"] = fit_tvtp(main, features, keys=TVTP_KEYS, fixed=ar1)
    for fit in tvtp.values():
        if fit.nobs != ar1.nobs:
            raise RuntimeError("TVTP and fixed-transition samples differ")
    bear_main = labels["bear"]
    tvtp_quality = {name: auc(f.filtered.to_numpy(), bear_main.reindex(f.index).to_numpy())
                    for name, f in {"Fixed transitions": ar1, **tvtp}.items()}
    log("models: time-varying transition probabilities")

    before, after = returns.loc[MAIN_START: SPLIT - pd.DateOffset(months=1)], returns.loc[SPLIT:]
    specs = [
        spec_from_fit("MS-AR(1)", ar1),
        spec_from_fit("Mean and variance", mv),
        fit_spec("Variance only", main, 2, False, True),
        fit_spec("Mean only", main, 2, True, False),
        fit_spec("Three regimes", main, 3, True, True),
        spec_from_fit(f"MS-AR(1), {MAIN_START:%Y}-{SPLIT.year - 1}", fit_regimes(before, "ar1")),
        spec_from_fit(f"MS-AR(1), {SPLIT:%Y}-{end:%Y}", fit_regimes(after, "ar1")),
    ]
    spec_quality = []
    for s in specs:
        y = bear_main.reindex(s.bear_filtered.index)
        spec_quality.append({"auc": auc(s.bear_filtered.to_numpy(), y.to_numpy()),
                             "corr": float(np.corrcoef(s.bear_filtered, y)[0, 1])})
    log("models: alternative regime specifications")

    fx = features[FORECAST_KEYS]
    fz = standardize(fx.dropna())
    logit = {h: fit_binary(bear_main, fz, h, "logit") for h in HORIZONS}
    probit = {h: fit_binary(bear_main, fz, h, "probit") for h in HORIZONS}

    q = ar1.filtered
    orig = standardize(features.loc[q.index, ORIGINAL_KEYS])
    ols = {(k, h): fit_ols(q, orig[[k]], h, scale=100) for k in ORIGINAL_KEYS for h in HORIZONS}
    beta = {(k, h): fit_beta(q, orig[[k]], h) for k in ORIGINAL_KEYS for h in HORIZONS}
    log("models: logit, probit and the corrected award-version regressions")

    adf = archived_frame(d["one45"])
    arch = fit_archived_regimes(adf)
    arch_is = archived_in_sample(adf, arch.regime_prob)
    arch_mspe = archived_mspe(adf, arch.regime_prob, HORIZONS)
    arch_mspe_all = archived_mspe(adf, arch.regime_prob, ARCHIVED_HORIZONS)
    first_test = arch_mspe[arch_mspe.k == 1].test_start.iloc[0]
    q_origins = q.index[q.index >= first_test]
    q_inputs = features.loc[q.index, ORIGINAL_KEYS].assign(q_now=q)
    q_fc = regime_prob_forecasts(q, q_inputs, q_origins, HORIZONS, q.index[0])
    q_mspe = mspe_summary(q_fc)
    write_csv(arch_is, "replication_in_sample.csv", index=False)
    write_csv(arch_mspe_all, "replication_mspe.csv", index=False)
    write_csv(q_mspe, "regime_prob_mspe.csv", index=False)
    write_csv(pd.DataFrame({"filtered": ar1.filtered, "smoothed": ar1.smoothed}), "regime_probabilities.csv", index_label="date")
    log("models: replication and regime-probability forecasts")
    scatter = replication_pairs(arch_is, arch_mspe_all)
    return {"fits": fits, "ar1": ar1, "scatter": scatter, "mv": mv, "tvtp": tvtp, "tvtp_quality": tvtp_quality, "specs": specs,
            "spec_quality": spec_quality, "logit": logit, "probit": probit, "ols": ols, "beta": beta, "arch": arch,
            "arch_is": arch_is, "arch_mspe": arch_mspe, "arch_mspe_all": arch_mspe_all, "q_mspe": q_mspe,
            "q_origins": q_origins, "first_test": first_test}


DATING_RULES = {"real15": ("Real prices, 15%", 0.15), "main": ("Real prices, 20% (main)", BEAR_DECLINE),
                "real25": ("Real prices, 25%", 0.25), "nominal20": ("Nominal prices, 20%", BEAR_DECLINE)}
VARIANT_LABELS = {"main": "Main (real prices, 20%, expanding)", "real15": "Dating threshold 15%",
                  "real25": "Dating threshold 25%", "nominal20": "Nominal prices, 20%",
                  "rolling": f"Rolling {ROLLING_WINDOW // 12}-year window"}


def stage_forecast(d: dict) -> dict:
    """Real-time forecasts for the main design and the alternative designs, plus combinations."""
    price, returns, features, labels, nominal = d["price"], d["returns"], d["features"], d["labels"], d["nominal"]
    idx = price.index
    origins = idx[(idx >= MAIN_START) & (idx < idx[-1])]
    ms_v = fit_vintage_regimes(returns, origins)
    log(f"forecast: {len(ms_v.fits)} vintage MS-AR(1) fits")
    tv_v = fit_vintage_tvtp(returns, features, origins, ms_v)
    log(f"forecast: {len(tv_v.fits)} vintage TVTP fits")
    specs = [RunSpec("main", VARIANT_LABELS["main"], price, labels, BEAR_DECLINE, MAIN_MODELS)]
    for key in ("real15", "real25", "nominal20"):
        p = nominal if key == "nominal20" else price
        decline = DATING_RULES[key][1]
        specs.append(RunSpec(key, VARIANT_LABELS[key], p, label_series(p, decline, decline), decline, ROBUST_MODELS))
    specs.append(RunSpec("rolling", VARIANT_LABELS["rolling"], price, labels, BEAR_DECLINE, ROBUST_MODELS, ROLLING_WINDOW))
    runs, extra = run_forecasts(specs, features, returns, origins, HORIZONS, {"ms": ms_v, "tvtp": tv_v})
    main = runs.pop("main")
    vint = extra["vintages"]
    dma = {(name, a): dma_combination(main, members, name, vint, idx, a)
           for a in DMA_ALPHAS for name, members in (("dma_uni", UNIVARIATE), ("dma_all", DMA_ALL_MEMBERS))}
    fc = pd.concat([main, dma[("dma_uni", DMA_ALPHA)], dma[("dma_all", DMA_ALPHA)]], ignore_index=True)
    write_csv(fc, "bear_forecasts.csv.gz", index=False)
    write_csv(pd.concat(runs, names=["variant"]).reset_index(level=0), "bear_forecasts_variants.csv.gz", index=False)
    write_csv(extra["ml_choices"], "ml_hyperparameters.csv", index=False)
    log("forecast: done")
    return {"fc": fc, "variants": runs, "dma": dma, "ml_choices": extra["ml_choices"], "origins": origins,
            "n_refits": len(ms_v.fits)}


def gw_instruments(fc: pd.DataFrame, horizon: int, model: str, bear_now: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    """Loss differential (model minus persistence) and the test functions known at each origin:
    a constant and the real-time bear state."""
    wide, y = wide_losses(fc, horizon)
    loss = wide.sub(y, axis=0) ** 2
    diff = (loss[model] - loss["persist"]).to_numpy()
    state = bear_now.reindex(wide.index).to_numpy(dtype=float)
    return diff, np.column_stack([np.ones(len(diff)), state])


def stage_robust(d: dict, f: dict) -> dict:
    """Evaluation and inference: scores, alternative designs, bootstrap, Murphy decomposition,
    model confidence set, superior and conditional predictive ability."""
    fc, variants = f["fc"], f["variants"]
    met = score(fc)
    write_csv(met, "bear_oos_metrics.csv")
    challengers = tuple(m for m in MAIN_MODELS + ("dma_uni", "dma_all") if m not in BASELINES)

    variant_met = {"main": score(fc, ROBUST_MODELS)}
    for key, run in variants.items():
        variant_met[key] = score(run, ROBUST_MODELS)
    t = fc.target_date
    subsets = {
        "pre": (f"Targets {t.min():%Y}-{SPLIT.year - 1}", fc[t < SPLIT]),
        "post": (f"Targets {SPLIT:%Y}-{t.max():%Y}", fc[t >= SPLIT]),
        "nocrisis": ("Excluding 2007-2009 crisis", fc[(t < CRISIS[0]) | (t > CRISIS[1])]),
    }
    for key, (_, sub) in subsets.items():
        variant_met[key] = score(sub, ROBUST_MODELS)
    write_csv(pd.concat(variant_met, names=["variant"]), "robustness_oos_metrics.csv")
    log("robust: scores")

    boot_models = ("persist", "ms", "tvtp", "logit_dy", "logit_all", "probit_all", "logit_state", "enet_rich", "gbt_rich", "dma_all")
    boot = bootstrap_skill(fc, boot_models)
    boot_sens = {b: bootstrap_skill(fc, ("persist", "logit_all"), block=b) for b in (12, 36)}
    write_csv(boot, "bootstrap_skill.csv")

    murphy_rows = []
    for h in HORIZONS:
        wide, y = wide_losses(fc, h)
        murphy_rows += [{"horizon": h, "model": m, **murphy_decomposition(wide[m].to_numpy(), y)}
                        for m in MAIN_MODELS + ("dma_uni", "dma_all")]
    murphy = pd.DataFrame(murphy_rows).set_index(["horizon", "model"])
    write_csv(murphy, "murphy_decomposition.csv")
    log("robust: bootstrap and Murphy decomposition")

    rng = np.random.default_rng(SEED)
    mcs_rows, spa_rows, gw_rows, acf = [], [], {}, {}
    all_models = MAIN_MODELS + ("dma_uni", "dma_all")
    for h in HORIZONS:
        wide, y = wide_losses(fc, h)
        loss = wide.sub(y, axis=0) ** 2
        diffs = loss[list(challengers)].sub(loss["persist"], axis=0)
        acf[h] = diffs.apply(lambda x: x.autocorr(1))
        idx = block_indices(len(y), BLOCK, BOOT_REPS, rng)
        pvals = model_confidence_set(loss[list(all_models)].to_numpy(), idx)
        mcs_rows += [{"horizon": h, "model": m, "p_mcs": p, "mean_loss": float(loss[m].mean())} for m, p in zip(all_models, pvals)]
        spa = spa_test(loss[["persist"]].to_numpy() - loss[list(challengers)].to_numpy(), idx)
        spa_rows.append({"key": f"h{h}", "label": f"Main design, h = {h}", "n_models": len(challengers),
                         **spa, "best": challengers[spa["best"]]})
        best = met.loc[h].loc[list(challengers)].brier.idxmin()
        diff, z = gw_instruments(fc, h, best, d["labels"]["bear_now"])
        stat, p = giacomini_white(diff, z, BLOCK - 1)
        gw_rows[h] = {"model": best, "stat": stat, "p_gw": p, "p_dm": met.loc[(h, best), "p_persist"],
                      "p_dm_long": met.loc[(h, best), "p_persist_long"],
                      "mean_diff_bull": float(diff[z[:, 1] == 0].mean()), "mean_diff_bear": float(diff[z[:, 1] == 1].mean())}
    log("robust: model confidence sets, SPA and GW tests")

    def joint_gains(frame: pd.DataFrame, models: tuple[str, ...]) -> tuple[np.ndarray, list[str]]:
        """Loss of persistence minus loss of every (model, horizon) pair, on the origins common to
        all horizons."""
        common = None
        for h in HORIZONS:
            index = wide_losses(frame, h)[0].index
            common = index if common is None else common.intersection(index)
        cols, names = [], []
        for h in HORIZONS:
            wide, y = wide_losses(frame, h)
            loss = (wide.sub(y, axis=0) ** 2).loc[common]
            cols += [loss["persist"].to_numpy() - loss[m].to_numpy() for m in models]
            names += [m for m in models]
        return np.column_stack(cols), names

    robust_challengers = tuple(m for m in ROBUST_MODELS if m not in BASELINES)
    for key, frame, models, label in (
        [("joint", fc, challengers, "Main design, all horizons")]
        + [(k, variants[k], robust_challengers, VARIANT_LABELS[k] + ", all horizons") for k in variants]
    ):
        gains, names = joint_gains(frame, models)
        spa = spa_test(gains, block_indices(len(gains), BLOCK, BOOT_REPS, rng))
        spa_rows.append({"key": key, "label": label, "n_models": gains.shape[1], **spa, "best": names[spa["best"]]})
    gains, _ = joint_gains(fc, challengers)
    spa12 = spa_test(gains, block_indices(len(gains), 12, BOOT_REPS, rng))
    spa = pd.DataFrame(spa_rows).set_index("key")
    mcs = pd.DataFrame(mcs_rows).set_index(["horizon", "model"])
    gw = pd.DataFrame.from_dict(gw_rows, orient="index")
    write_csv(spa, "spa_tests.csv")
    write_csv(mcs, "model_confidence_set.csv")
    write_csv(gw, "giacomini_white.csv", index_label="horizon")

    dma_met = {key: score(pd.concat([fc[fc.model.isin(BASELINES)], frame], ignore_index=True), [key[0]])
               for key, frame in f["dma"].items()}
    log("robust: done")
    return {"met": met, "variant_met": variant_met, "subsets": {k: v[0] for k, v in subsets.items()}, "boot": boot,
            "boot_models": boot_models, "boot_sens": boot_sens, "murphy": murphy, "mcs": mcs, "spa": spa,
            "spa12": spa12, "gw": gw, "acf": pd.DataFrame(acf), "dma_met": dma_met, "challengers": challengers}


# =============================================================================================
# 14. Tables, numbers.json, figures and the paper
# =============================================================================================


def _n(x: float, digits: int = 3) -> str:
    return fmt(float(x), digits)


def metric_numbers(met: pd.DataFrame) -> dict:
    """Formatted metrics as numbers[model][f"h{h}"][stat]."""
    out: dict = {}
    for (h, m), r in met.iterrows():
        out.setdefault(m, {})[f"h{h}"] = {
            "brier": _n(r.brier, 3), "bss": _n(100 * r.bss, 1), "ll": _n(r.log_loss, 3) if "log_loss" in r else "",
            "auc": _n(r.auc, 3), "p_unc": fmt_p(r.p_uncond), "p_per": fmt_p(r.p_persist),
            "p_per_long": fmt_p(r.p_persist_long),
        }
    return out


def _count_word(n: int) -> str:
    words = {0: "none", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight",
             9: "nine", 10: "ten", 11: "eleven", 12: "twelve"}
    return words.get(n, str(n))


def stage_tables(d: dict, m: dict, f: dict, r: dict) -> None:
    """Write every table (Typst and Markdown) and output/numbers.json."""
    tables = OUTPUT / "tables"
    info, labels, ep, features = d["info"], d["labels"], d["episodes"], d["features"]
    idx = d["price"].index
    end = idx[-1]
    main_label = f"{MAIN_START:%B %Y} to {end:%B %Y}"
    span_full = f"{idx[0]:%Y}-{end:%Y}"
    met, fc = r["met"], f["fc"]
    challengers = r["challengers"]
    numbers: dict = {}

    # --- design and data -------------------------------------------------------------------
    numbers["design"] = {
        "decline": f"{100 * BEAR_DECLINE:.0f}", "rise": f"{100 * BULL_RISE:.0f}", "cpi_lag": str(CPI_LAG),
        "fund_lag": str(FUNDAMENTALS_LAG), "horizons": ", ".join(map(str, HORIZONS)), "floor": f"{LOG_LOSS_FLOOR:g}",
        "main_sample": main_label, "main_start_year": f"{MAIN_START:%Y}", "end_year": f"{end:%Y}",
        "full_start_year": f"{idx[0]:%Y}", "split": f"{SPLIT:%Y}", "split_prev": f"{SPLIT.year - 1}",
        "n_forecast_features": str(len(FORECAST_KEYS)), "n_all_features": str(len(ALL_KEYS)),
        "n_extra_features": str(len(EXTRA_KEYS)), "n_original_features": str(len(ORIGINAL_KEYS)),
        "n_core_models": str(len(CORE_MODELS)), "n_challengers": str(len(challengers)),
        "rolling_years": str(ROLLING_WINDOW // 12), "block": str(BLOCK), "reps": f"{BOOT_REPS:,}",
        "dma_alpha": f"{DMA_ALPHA:g}", "dma_alphas": ", ".join(f"{a:g}" for a in DMA_ALPHAS),
        "ml_validation_years": str(ML_VALIDATION // 12), "murphy_bins": str(MURPHY_BINS),
        "enet_c": ", ".join(f"{c:g}" for c in sorted({c for c, _ in ENET_GRID})),
        "enet_l1": ", ".join(f"{a:g}" for a in sorted({a for _, a in ENET_GRID})),
        "gbt_depth": ", ".join(str(x) for x in sorted({a for a, _ in GBT_GRID})),
        "gbt_iter": ", ".join(str(x) for x in sorted({b for _, b in GBT_GRID})),
        "gbt_lr": f"{GBT_LEARNING_RATE:g}", "n_enet_grid": str(len(ENET_GRID)), "n_gbt_grid": str(len(GBT_GRID)),
        "crisis": f"{_ym(CRISIS[0])} to {_ym(CRISIS[1])}",
    }
    comp = d["comparison"]
    differ = comp[comp.n_differ > 0]
    numbers["source"] = {
        "url": info["url"], "page": info["page"], "sha256": info["sha256"], "sha_short": info["sha256"][:12],
        "megabytes": _n(info["bytes"] / 1e6, 1), "downloaded": info["downloaded"], "last_modified": info["last_modified"],
        "sheet": info["sheet"], "first": month_label(info["first"]), "last_row": month_label(info["last_row"]),
        "end": month_label(info["end"]), "footnote": "; ".join(info["footnotes"]),
        "n_months": f"{len(idx):,}", "sample_start": month_label(idx[0]),
        "compare_series": str(len(comp)), "compare_identical": str(int((comp.n_differ == 0).sum())),
        "compare_months": f"{int(comp.months.max()):,}", "compare_first": month_label(comp["first"].min()),
        "compare_last": month_label(comp["last"].max()),
        "compare_n_cells": str(int(comp.n_differ.sum())),
        "compare_first_diff": month_label(differ.first_differ.min()) if len(differ) else "",
        "compare_max_pct": _n(differ.max_abs_rel_pct.max(), 1) if len(differ) else "0",
    }
    audit = d["audit"].iloc[0]
    main_labels = labels.loc[MAIN_START:]
    first_valid = features[ALL_KEYS].dropna().index[0]
    numbers["data"] = {
        "first_valid": month_label(first_valid), "n_bears": str(len(ep)),
        "n_bears_main": str(int((ep.peak >= MAIN_START).sum())),
        "bear_share_full": _n(100 * labels.bear.mean(), 1), "bear_share_main": _n(100 * main_labels.bear.mean(), 1),
        "median_bear_months": _n(ep.months.median(), 0), "median_decline": _n(-ep.decline_pct.median(), 1),
        "median_confirm_lag": _n(np.median([months_between(p, c) for p, c in zip(ep.peak, ep.confirmed)]), 0),
        "last_peak": f"{ep.peak.iloc[-1]:%B %Y}", "last_trough": f"{ep.trough.iloc[-1]:%B %Y}",
        "audit_future": f"{int(audit.match_future):,}", "audit_pairs": f"{int(audit.pairs_future):,}",
        "audit_past": str(int(audit.match_past)), "base": month_label(end),
        "decline_2020": _n(100 * (1 - d["price"].loc["2020-03-01":"2020-12-01"].min() / d["price"].loc["2019-01-01":"2020-02-01"].max()), 1),
    }
    write_table(variables_table(features.loc[MAIN_START:], main_label), tables)
    write_table(episodes_table(ep, span_full), tables)
    write_table(data_comparison_table(comp, f"{info['last_modified']}"), tables)

    # --- regimes ------------------------------------------------------------------------------
    ar1, mv = m["ar1"], m["mv"]
    full_ar1 = list(m["fits"].values())[3]
    write_table(regime_table(m["fits"]), tables)
    q = ar1.filtered
    lab_q = labels.bear.reindex(q.index)
    numbers["ms"] = {
        "bull_mean": _n(ar1.means[0], 2), "bear_mean": _n(ar1.means[1], 2),
        "bull_sd": _n(np.sqrt(ar1.variances[0]), 2), "bear_sd": _n(np.sqrt(ar1.variances[1]), 2),
        "p_bull": _n(ar1.transition[0, 0], 3), "p_bear": _n(ar1.transition[1, 1], 3),
        "dur_bull": _n(ar1.durations[0], 1), "dur_bear": _n(ar1.durations[1], 1), "ar": _n(ar1.ar, 3),
        "aic_ar": _n(ar1.aic, 1), "aic_mv": _n(mv.aic, 1),
        "auc_filtered_now": _n(auc(q.to_numpy(), lab_q.to_numpy()), 3),
        "auc_smoothed_now": _n(auc(ar1.smoothed.to_numpy(), lab_q.to_numpy()), 3),
        "full_dur_bull": _n(full_ar1.durations[0], 1), "full_dur_bear": _n(full_ar1.durations[1], 1),
        "full_bear_sd": _n(np.sqrt(full_ar1.variances[1]), 2),
    }
    tv = m["tvtp"]
    write_table(tvtp_table(ar1, tv, m["tvtp_quality"]), tables)
    numbers["tvtp"] = {}
    for key, (name, fit) in zip([*TVTP_KEYS, "all"], tv.items()):
        stat, df, p = lr_test(fit, ar1)
        slopes = tvtp_slopes(fit)
        numbers["tvtp"][key] = {
            "lr": _n(stat, 1), "df": str(df), "p": fmt_p(p), "aic": _n(fit.aic, 1), "bic": _n(fit.bic, 1),
            "auc": _n(m["tvtp_quality"][name], 3), "bull_mean": _n(fit.means[0], 2), "bear_mean": _n(fit.means[1], 2),
            "bear_sd": _n(np.sqrt(fit.variances[1]), 2),
            "p_bull": _n(fit.transition[0, 0], 3), "p_bear": _n(fit.transition[1, 1], 3),
            **{f"stay_{k}": coef_cell(slopes[("stay", k)]) for k in fit.tvtp_keys},
            **{f"exit_{k}": coef_cell(slopes[("exit", k)]) for k in fit.tvtp_keys},
        }
    numbers["tvtp"]["fixed_bic"] = _n(ar1.bic, 1)
    numbers["tvtp"]["fixed_aic"] = _n(ar1.aic, 1)
    numbers["tvtp"]["fixed_auc"] = _n(m["tvtp_quality"]["Fixed transitions"], 3)
    numbers["tvtp"]["n_bic_better"] = str(sum(f.bic < ar1.bic for f in tv.values()))
    numbers["tvtp"]["pbb_min"] = _n(tv["All four"].p_bull_bear.min(), 3)
    numbers["tvtp"]["pbb_max"] = _n(tv["All four"].p_bull_bear.max(), 3)
    numbers["tvtp"]["pbb_fixed"] = _n(ar1.transition[0, 1], 3)

    # --- in-sample binary models and the award-version design ---------------------------------
    logit, probit = m["logit"], m["probit"]
    write_table(logit_table(logit, probit, HORIZONS), tables)
    numbers["logit"] = {"start": month_label(logit[1].start),
                        **{f"r2_h{h}": _n(logit[h].stats["pseudo_r2"], 3) for h in HORIZONS},
                        **{f"{k}_h{h}": coef_cell(logit[h].coefs[k]) for k in FORECAST_KEYS for h in HORIZONS}}
    ols, beta = m["ols"], m["beta"]
    write_table(original_spec_table(ols, beta, HORIZONS), tables)
    numbers["orig"] = {
        **{f"sig5_h{h}": str(sum(ols[(k, h)].coefs[k].pvalue < 0.05 for k in ORIGINAL_KEYS)) for h in HORIZONS},
        "n_pred": str(len(ORIGINAL_KEYS)), "max_r2": _n(max(x.stats["r2"] for x in ols.values()), 3),
        "max_r2_label": FEATURE_LABELS[max(ols, key=lambda kh: ols[kh].stats["r2"])[0]],
        "div_h1": coef_cell(ols[("div_growth", 1)].coefs["div_growth"]), "tr_h1": coef_cell(ols[("tr_ret", 1)].coefs["tr_ret"]),
        "trse_h1_r2": _n(ols[("trse_growth", 1)].stats["r2"], 3),
    }
    q_mspe, arch_mspe, arch_is = m["q_mspe"], m["arch_mspe"], m["arch_is"]
    q_or = m["q_origins"]
    write_table(mspe_table(arch_mspe, q_mspe, HORIZONS, f"{_ym(q_or[0])} to {_ym(q_or[-1] - pd.DateOffset(months=1))} for h = 1"), tables)
    ols_c = q_mspe[(q_mspe.model == "OLS") & (q_mspe.predictor != "q_now")]
    q_now = q_mspe[(q_mspe.model == "OLS") & (q_mspe.predictor == "q_now")].set_index("k")
    numbers["mspe"] = {
        "test_start": month_label(m["first_test"]), "n_below1_ols": str(int((ols_c.mspe_ratio < 1).sum())),
        "n_cells": str(len(ols_c)), "n_cw10_ols": str(int((ols_c.cw_p < 0.10).sum())),
        "min_ratio_ols": _n(ols_c.mspe_ratio.min(), 3), **{f"qnow_h{h}": _n(q_now.loc[h, "mspe_ratio"], 3) for h in HORIZONS},
    }
    reported = pd.read_csv(ARCHIVED_REPORTED_FILE)

    def rep_val(table: str, pred: str, k: int, stat: str) -> float:
        row = reported[(reported.table == table) & (reported.predictor == pred) & (reported.k == k) & (reported.statistic == stat)]
        return float(row["value"].iloc[0])

    def arch_val(pred: str, k: int, col: str) -> float:
        return float(arch_is[(arch_is.predictor == pred) & (arch_is.k == k)][col].iloc[0])

    def mspe_val(df: pd.DataFrame, model: str, pred: str, k: int, col: str) -> float:
        return float(df[(df.model == model) & (df.predictor == pred) & (df.k == k)][col].iloc[0])

    rep_t = reported[reported.table == "transition"].set_index("statistic")["value"]
    arch = m["arch"]
    rep_rows = [
        ("P(bull to bull)", _n(rep_t["p_bull_bull"]), _n(arch.transition[0, 0]), _n(ar1.transition[0, 0])),
        ("P(bear to bear)", _n(rep_t["p_bear_bear"]), _n(arch.transition[1, 1]), _n(ar1.transition[1, 1])),
        ("Dividend, k = 1: coefficient", _n(rep_val("ols_in_sample", "realdividend", 1, "coef")),
         _n(arch_val("realdividend", 1, "coef")), coef_cell(ols[("div_growth", 1)].coefs["div_growth"]) + " pp"),
        ("Dividend, k = 6: R²", _n(rep_val("ols_in_sample", "realdividend", 6, "r2")), _n(arch_val("realdividend", 6, "r2")),
         _n(ols[("div_growth", 6)].stats["r2"])),
        ("Total return, k = 1: R²", _n(rep_val("ols_in_sample", "realtotalreturn", 1, "r2")),
         _n(arch_val("realtotalreturn", 1, "r2")), _n(ols[("tr_ret", 1)].stats["r2"])),
        ("Dividend, k = 1: OLS forecast ratio", _n(rep_val("ols_forecast_ratio", "realdividend", 1, "ratio")),
         _n(mspe_val(arch_mspe, "OLS", "realdividend", 1, "archived_ratio")), _n(mspe_val(q_mspe, "OLS", "div_growth", 1, "mspe_ratio"))),
        ("Total return, k = 1: OLS forecast ratio", _n(rep_val("ols_forecast_ratio", "realtotalreturn", 1, "ratio")),
         _n(mspe_val(arch_mspe, "OLS", "realtotalreturn", 1, "archived_ratio")), _n(mspe_val(q_mspe, "OLS", "tr_ret", 1, "mspe_ratio"))),
    ]
    rep_df = pd.DataFrame(rep_rows, columns=["label", "reported", "replicated", "corrected"])
    write_csv(rep_df, "replication_summary.csv", index=False)
    write_table(replication_table(rep_df), tables)
    corr = [np.corrcoef(v.reported, v.replicated)[0, 1] for v in m["scatter"].values()]
    numbers["rep"] = {
        "p_bull_reported": _n(rep_t["p_bull_bull"]), "p_bear_reported": _n(rep_t["p_bear_bear"]),
        "p_bull_replicated": _n(arch.transition[0, 0]), "p_bear_replicated": _n(arch.transition[1, 1]),
        "corr_coef": _n(corr[0], 3), "corr_r2": _n(corr[1], 3), "corr_ratio": _n(corr[2], 3),
        "div_ratio_reported": _n(rep_val("ols_forecast_ratio", "realdividend", 1, "ratio")),
        "div_ratio_true": _n(mspe_val(arch_mspe, "OLS", "realdividend", 1, "mspe_ratio")),
        "div_ratio_corrected": _n(mspe_val(q_mspe, "OLS", "div_growth", 1, "mspe_ratio")),
    }

    # --- out-of-sample results ------------------------------------------------------------------
    period = f"{fc.target_date.min():%Y:%m}-{fc.target_date.max():%Y:%m}"
    write_table(oos_table(met, CORE_MODELS, HORIZONS, "oos", f"Out-of-sample accuracy of real-time bear-market forecasts, targets {period}",
                          " Markov-switching parameters are re-estimated each January (filtered probabilities only)."), tables)
    write_table(oos_table(met, ("uncond", "persist") + MODERN_MODELS, HORIZONS, "modern",
                          f"Out-of-sample accuracy of time-varying-transition, machine-learning and combination forecasts, targets {period}",
                          " The TVTP model and the machine-learning models are re-estimated each January; the elastic net "
                          "and gradient boosting choose their hyperparameters by validation on the last "
                          f"{ML_VALIDATION // 12} years of each training window. The rich set adds the five additional "
                          "predictors and the real-time bear state."), tables)
    write_table(summary_table(met, HORIZONS, ("uncond", "persist", "ms", "logit_dy", "logit_all", "gbt_rich"), challengers), tables)
    o = metric_numbers(met)
    o["period"] = period
    o["first_origin"] = month_label(f["origins"][0])
    o["last_origin"] = month_label(f["origins"][-1])
    o["n_refits"] = str(f["n_refits"])
    for h in HORIZONS:
        sub = met.loc[h]
        best = sub.loc[list(challengers)].brier.idxmin()
        o[f"h{h}"] = {"n": f"{int(sub.loc['uncond', 'n']):,}", "share": _n(100 * sub.loc["uncond", "bear_share"], 1),
                      "best": MODEL_LABELS[best], "best_key": best,
                      "n_beat_persist": str(int((sub.loc[list(challengers)].brier < sub.loc["persist", "brier"]).sum())),
                      "n_beat_uncond": str(int((sub.loc[list(challengers)].bss > 0).sum()))}
    ch = met[met.index.get_level_values("model").isin(challengers)]
    o["n_tests"] = str(len(ch))
    o["n_sig_persist"] = str(int((ch.p_persist < 0.05).sum()))
    o["n_sig_persist_word"] = _count_word(int((ch.p_persist < 0.05).sum()))
    o["min_p_persist"] = fmt_p(ch.p_persist.min())
    o["min_p_model"] = MODEL_LABELS[ch.p_persist.idxmin()[1]]
    o["min_p_h"] = str(ch.p_persist.idxmin()[0])
    o["n_sig_persist_long"] = str(int((ch.p_persist_long < 0.05).sum()))
    o["min_p_persist_long"] = fmt_p(ch.p_persist_long.min())
    o["min_p_long_model"] = MODEL_LABELS[ch.p_persist_long.idxmin()[1]]
    o["n_sig_persist_h1"] = str(int((ch.loc[1].p_persist < 0.05).sum()))
    o["n_challengers_h"] = str(len(challengers))
    numbers["oos"] = o

    choices = f["ml_choices"]
    numbers["ml"] = {}
    for name in ML_MODELS:
        sub = choices[choices.model == name]
        top = sub.params.value_counts()
        a, b = (float(x) for x in top.index[0].strip("()").split(", "))
        label = f"C = {a:g} and mixing weight {b:g}" if name.startswith("enet") else f"depth {a:g} and {b:g} rounds"
        numbers["ml"][name] = {"top": label, "top_share": _n(100 * top.iloc[0] / len(sub), 0), "n_fits": str(len(sub))}
    numbers["ml"]["n_refits"] = str(choices.origin.nunique())

    murphy = r["murphy"]
    murphy_models = ("uncond", "persist", "ms", "tvtp", "logit_dy", "logit_all", "logit_state", "enet", "enet_rich",
                     "gbt", "gbt_rich", "combo", "dma_all")
    write_table(murphy_table(murphy, murphy_models, HORIZONS), tables)
    numbers["murphy"] = {mm: {f"h{h}": {"rel": _n(100 * murphy.loc[(h, mm)].reliability, 2),
                                         "res": _n(100 * murphy.loc[(h, mm)].resolution, 2)} for h in HORIZONS}
                         for mm in murphy_models}
    numbers["murphy"]["unc"] = {f"h{h}": _n(100 * murphy.loc[(h, "uncond")].uncertainty, 2) for h in HORIZONS}
    for h in HORIZONS:
        sub = murphy.loc[h].loc[list(challengers)]
        numbers["murphy"][f"best_res_h{h}"] = MODEL_LABELS[sub.resolution.idxmax()]
        numbers["murphy"][f"worst_rel_h{h}"] = MODEL_LABELS[sub.reliability.idxmax()]

    mcs, spa, gw = r["mcs"], r["spa"], r["gw"]
    mcs_models = ("uncond", "persist", "ms", "tvtp", "logit_dy", "logit_all", "probit_all", "logit_state", "enet",
                  "enet_rich", "gbt", "gbt_rich", "logit_ext", "combo", "dma_uni", "dma_all")
    write_table(inference_table(mcs, mcs_models, HORIZONS, BLOCK), tables)
    write_table(spa_table(spa, gw, HORIZONS), tables)
    numbers["mcs"] = {}
    for h in HORIZONS:
        sub = mcs.loc[h]
        members = [mm for mm in sub.index if sub.loc[mm, "p_mcs"] >= 0.10]
        numbers["mcs"][f"h{h}"] = {"n_in": str(len(members)), "n_models": str(len(sub)),
                                   "persist_p": _n(sub.loc["persist", "p_mcs"], 3),
                                   "persist_in": "yes" if "persist" in members else "no",
                                   "uncond_in": "yes" if "uncond" in members else "no",
                                   "uncond_p": _n(sub.loc["uncond", "p_mcs"], 3)}
    numbers["spa"] = {key: {"p_c": fmt_p(row.p_consistent), "p_rc": fmt_p(row.p_upper), "p_l": fmt_p(row.p_lower),
                            "best": MODEL_LABELS.get(row.best, row.best), "n": str(int(row.n_models))}
                      for key, row in spa.iterrows()}
    numbers["spa"]["b12_p_c"] = fmt_p(r["spa12"]["p_consistent"])
    numbers["spa"]["min_variant_p"] = fmt_p(spa.loc[list(f["variants"])].p_consistent.min())
    numbers["acf"] = {f"h{h}": {"median": _n(r["acf"][h].median(), 2), "min": _n(r["acf"][h].min(), 2),
                                "max": _n(r["acf"][h].max(), 2)} for h in HORIZONS}
    numbers["gw"] = {f"h{h}": {"model": MODEL_LABELS[gw.loc[h, "model"]], "p": fmt_p(gw.loc[h, "p_gw"]),
                               "stat": _n(gw.loc[h, "stat"], 2), "p_dm": fmt_p(gw.loc[h, "p_dm"]),
                               "p_dm_long": fmt_p(gw.loc[h, "p_dm_long"]),
                               "bull": _n(1000 * gw.loc[h, "mean_diff_bull"], 1), "bear": _n(1000 * gw.loc[h, "mean_diff_bear"], 1)}
                     for h in HORIZONS}

    comb_rows = [{"label": "Equal-weight combination", **{f"bss_h{h}": met.loc[(h, "combo")].bss for h in HORIZONS},
                  **{f"p_h{h}": met.loc[(h, "combo")].p_uncond for h in HORIZONS}}]
    numbers["comb"] = {}
    for (name, a), dm in r["dma_met"].items():
        label = f"DMA, {'univariate logits' if name == 'dma_uni' else 'all models'}, alpha = {a:g}"
        comb_rows.append({"label": label, **{f"bss_h{h}": dm.loc[(h, name)].bss for h in HORIZONS},
                          **{f"p_h{h}": dm.loc[(h, name)].p_uncond for h in HORIZONS}})
        numbers["comb"][f"{name}_{str(a).replace('.', '')}"] = {f"h{h}": _n(100 * dm.loc[(h, name)].bss, 1) for h in HORIZONS}
    write_table(combination_table(pd.DataFrame(comb_rows), HORIZONS), tables)

    # --- robustness ------------------------------------------------------------------------------
    rob: dict = {}
    write_table(regime_spec_table(m["specs"], m["spec_quality"], main_label), tables)
    spec_keys = ["ar1", "mv", "var_only", "mean_only", "three", "pre", "post"]
    rob["spec"] = {
        k: {"auc": _n(qq["auc"], 3), "aic": _n(s.aic, 1), "bic": _n(s.bic, 1), "bull_mean": _n(s.means[0], 2),
            "bear_mean": _n(s.means[-1], 2), "bull_sd": _n(s.sds[0], 2), "bear_sd": _n(s.sds[-1], 2),
            "dur_bull": _n(s.durations[0], 1), "dur_bear": _n(s.durations[-1], 1),
            **({"mid_mean": _n(s.means[1], 2), "dur_mid": _n(s.durations[1], 1)} if s.k == 3 else {})}
        for k, s, qq in zip(spec_keys, m["specs"], m["spec_quality"])
    }
    price, nominal = d["price"], d["nominal"]
    dating = {}
    for key, (_, dec) in DATING_RULES.items():
        p = nominal if key == "nominal20" else price
        lab, e = label_series(p, dec, dec), episodes(p, dec, dec)
        dating[key] = {"n_bears": len(e), "n_bears_since": int((e.peak >= MAIN_START).sum()),
                       "bear_share_since": float(lab.bear.loc[MAIN_START:].mean()), "median_decline": float(-e.decline_pct.median())}
    write_table(dating_table(dating, {k: v[0] for k, v in DATING_RULES.items()}, f"{MAIN_START:%Y}", span_full), tables)
    rob["dating"] = {k: {"n": str(v["n_bears"]), "n_since": str(v["n_bears_since"]), "share": _n(100 * v["bear_share_since"], 1)}
                     for k, v in dating.items()}
    vlabels = {**VARIANT_LABELS, **{k: v for k, v in r["subsets"].items()}}
    write_table(robust_oos_table(r["variant_met"], vlabels, HORIZONS), tables)
    rob["var"] = {k: metric_numbers(v) for k, v in r["variant_met"].items()}
    write_table(predictors_table(met, HORIZONS), tables)
    write_table(bootstrap_table(r["boot"], ("persist", "ms", "tvtp", "logit_dy", "logit_all", "enet_rich", "gbt_rich", "dma_all"), HORIZONS), tables)
    boot = r["boot"]
    rob["boot"] = {mm: {f"h{h}": {"lo": _n(100 * boot.loc[(h, mm), "bss_lo"], 1), "hi": _n(100 * boot.loc[(h, mm), "bss_hi"], 1),
                                  "glo": _n(100 * boot.loc[(h, mm), "gain_lo"], 1), "ghi": _n(100 * boot.loc[(h, mm), "gain_hi"], 1),
                                  "share": _n(boot.loc[(h, mm), "share_beats_persist"], 2)} for h in HORIZONS}
                   for mm in r["boot_models"]}
    rob["boot_sens"] = {f"b{b}": {mm: {"lo": _n(100 * v.loc[(1, mm), "bss_lo"], 1), "hi": _n(100 * v.loc[(1, mm), "bss_hi"], 1)}
                                  for mm in ("persist", "logit_all")} for b, v in r["boot_sens"].items()}
    uni = met[met.index.get_level_values("model").isin(UNIVARIATE)]
    rob["pred_best"] = {f"h{h}": FEATURE_LABELS[uni.loc[h].bss.idxmax().removeprefix("uni_")] for h in HORIZONS}
    numbers["rob"] = rob
    numbers["hero"] = {"h": "1", "model": MODEL_LABELS["logit_all"]}
    (OUTPUT / "numbers.json").write_text(json.dumps(numbers, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def stage_figures(d: dict, m: dict, f: dict, r: dict) -> None:
    figs = OUTPUT / "figures"
    price, labels, fc = d["price"], d["labels"], f["fc"]
    fig_price(price * d["cpi_end"], labels.bear, figs, f"{price.index[-1]:%B %Y}")
    fig_regime_probabilities(m["ar1"], labels.bear, figs)
    fig_oos_paths(fc, labels.bear, (1, 6, 12), FIGURE_MODELS, figs)
    fig_calibration(fc, HORIZONS, FIGURE_MODELS, figs)
    fig_roc(fc, HORIZONS, FIGURE_MODELS, r["met"], figs)
    fig_forest(m["logit"], figs)
    fig_replication(m["scatter"], figs)
    fig_skill_intervals(r["boot"], ("persist", "ms", "logit_dy", "logit_all", "gbt_rich"), HORIZONS, figs)
    fig_tvtp(m["tvtp"]["All four"], m["ar1"], labels.bear, figs)
    fig_murphy(r["murphy"], ("uncond", "persist", "ms", "tvtp", "logit_dy", "logit_all", "enet_rich", "gbt_rich", "combo", "dma_all"), HORIZONS, figs)
    fig_hero(price * d["cpi_end"], labels.bear, fc, "logit_all", 1, figs)


def stage_paper(source: Path = PAPER_SOURCE, target: Path = PAPER_PDF) -> None:
    """Compile the Typst paper with the v2 directory as root so it can read output/."""
    typst.compile(str(source), output=str(target), root=str(ROOT))
    log(f"paper compiled to {target}")


# =============================================================================================
# 15. Command line
# =============================================================================================

STAGES = ("data", "models", "forecast", "robust", "tables", "figures", "paper")


def run_stage(name: str) -> None:
    if name == "data":
        save_stage("data", stage_data())
    elif name == "models":
        save_stage("models", stage_models(load_stage("data")))
    elif name == "forecast":
        save_stage("forecast", stage_forecast(load_stage("data")))
    elif name == "robust":
        save_stage("robust", stage_robust(load_stage("data"), load_stage("forecast")))
    elif name == "tables":
        stage_tables(load_stage("data"), load_stage("models"), load_stage("forecast"), load_stage("robust"))
    elif name == "figures":
        stage_figures(load_stage("data"), load_stage("models"), load_stage("forecast"), load_stage("robust"))
    elif name == "paper":
        stage_paper()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stages", nargs="*", choices=("all", *STAGES), metavar="stage",
                        help=f"one or more of: all, {', '.join(STAGES)} (default: all)")
    parser.add_argument("--keep", action="store_true", help="with `all`: keep existing outputs instead of starting clean")
    args = parser.parse_args(argv)
    requested = args.stages or ["all"]
    stages = list(STAGES) if "all" in requested else requested
    if "all" in requested and not args.keep:
        for path in (OUTPUT, CACHE):
            if path.exists():
                shutil.rmtree(path)
    np.random.seed(SEED)
    for name in stages:
        run_stage(name)
        log(f"stage {name} finished")


if __name__ == "__main__":
    # Run through the importable module so that cached objects pickle as `thesis.*` and can be
    # read back by any later stage, test or interactive session.
    sys.path.insert(0, str(ROOT))
    import thesis

    thesis.main()
