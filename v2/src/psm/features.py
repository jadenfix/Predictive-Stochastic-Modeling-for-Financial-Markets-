"""Past-only feature construction.

Every column produced here is indexed by the forecast origin t (end of month t)
and uses only information published by then. The archived `realpricelag*`
columns, which hold future prices, are never read in this module.

Timing conventions (see `psm.config`):
* monthly-average prices and the 10-year yield for month t are known at t;
* CPI enters with a one-month lag, so real quantities are deflated by CPI_{t-1};
* dividends and earnings enter with a six-month lag.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from psm.config import CPI_LAG, FUNDAMENTALS_LAG


@dataclass(frozen=True)
class Feature:
    """Metadata for one predictor: a plain-English name and its units."""

    key: str
    label: str
    unit: str


# Monthly-change predictors mirroring the seven series of the archived thesis.
ORIGINAL_FEATURES: tuple[Feature, ...] = (
    Feature("infl_m", "CPI inflation, monthly", "% per month"),
    Feature("d_rate", "Change in 10-year yield", "pp"),
    Feature("bond_ret", "Real bond return", "% per month"),
    Feature("div_growth", "Real dividend growth", "% per month"),
    Feature("tr_ret", "Real total return", "% per month"),
    Feature("trse_growth", "TR-scaled earnings growth", "% per month"),
    Feature("d_trcape", "Change in log TR-CAPE", "% per month"),
)

# State-variable predictors for the bear-market forecasting models.
FORECAST_FEATURES: tuple[Feature, ...] = (
    Feature("log_dy", "Log dividend yield", "log points"),
    Feature("log_cape", "Log CAPE", "log points"),
    Feature("infl_yoy", "CPI inflation, 12-month", "%"),
    Feature("d_rate_12", "12-month change in 10-year yield", "pp"),
    Feature("mom_12", "12-month real price change", "%"),
    Feature("vol_12", "12-month realized volatility", "% annualized"),
)

# Additional state predictors from the same Shiller file, used in the robustness section.
EXTRA_FEATURES: tuple[Feature, ...] = (
    Feature("ecy", "Excess CAPE yield", "%"),
    Feature("log_payout", "Log payout ratio", "log points"),
    Feature("earn_growth_12", "12-month real earnings growth", "%"),
    Feature("rate_level", "10-year Treasury yield", "%"),
    Feature("drawdown", "Drawdown from 12-month high", "%"),
)

FEATURE_LABELS: dict[str, str] = {
    f.key: f.label for f in ORIGINAL_FEATURES + FORECAST_FEATURES + EXTRA_FEATURES
}
FEATURE_LABELS["bear_now"] = "Real-time bear state"
FEATURE_LABELS["ms_bear"] = "MS-AR bear probability (logit)"

# Raw columns that may be read by the corrected pipeline.
ALLOWED_RAW_COLUMNS = (
    "spprice",
    "dividend",
    "earnings",
    "infl",
    "lrir10",
    "realprice",
    "realearnings",
    "realdividend",
    "realtrscaledearnings",
    "realbond",
)


def observable_real(real_series: pd.Series, cpi: pd.Series) -> pd.Series:
    """Re-deflate a Shiller real series by CPI_{t-1} instead of same-month CPI.

    Shiller's real series divide nominal values by CPI_t, which is not published
    until month t + 1. Multiplying by CPI_t / CPI_{t-1} yields the same nominal
    value deflated by the latest CPI available at the end of month t.
    """
    return real_series * cpi / cpi.shift(CPI_LAG)


def real_price_index(raw: pd.DataFrame) -> pd.Series:
    """Real S&P 500 price index observable at the end of each month."""
    return observable_real(raw["realprice"], raw["infl"]).rename("real_price")


def real_returns(raw: pd.DataFrame) -> pd.Series:
    """Monthly real price return in percent: 100 * dlog of the observable real index."""
    return (100 * np.log(real_price_index(raw)).diff()).rename("real_return")


def _ten_year_mean(series: pd.Series) -> pd.Series:
    return series.rolling(120, min_periods=120).mean()


def build_features(raw: pd.DataFrame) -> pd.DataFrame:
    """Construct all predictors on the raw month index (rows are forecast origins)."""
    missing = set(ALLOWED_RAW_COLUMNS) - set(raw.columns)
    if missing:
        raise KeyError(f"Missing raw columns: {sorted(missing)}")
    cpi = raw["infl"]
    log_cpi_avail = np.log(cpi.shift(CPI_LAG))
    infl_m = 100 * log_cpi_avail.diff()
    price = raw["spprice"]
    real_price = real_price_index(raw)
    dividend_avail = raw["dividend"].shift(FUNDAMENTALS_LAG)

    # Total return built from the price and the lagged dividend, deflated by lagged CPI.
    tr_ret = 100 * np.log((price + dividend_avail / 12) / price.shift(1)) - infl_m
    tr_index = np.exp(tr_ret.fillna(0).cumsum() / 100).where(tr_ret.notna())
    trse_avail = raw["realtrscaledearnings"].shift(FUNDAMENTALS_LAG)
    log_trcape = np.log(tr_index) - np.log(_ten_year_mean(trse_avail))

    real_bond = observable_real(raw["realbond"], cpi)
    real_earn_avail = raw["realearnings"].shift(FUNDAMENTALS_LAG)
    log_real_price = np.log(real_price)
    monthly_real = 100 * log_real_price.diff()

    out = pd.DataFrame(
        {
            "infl_m": infl_m,
            "d_rate": raw["lrir10"].diff(),
            "bond_ret": 100 * np.log(real_bond).diff(),
            "div_growth": 100 * np.log(raw["realdividend"].shift(FUNDAMENTALS_LAG)).diff(),
            "tr_ret": tr_ret,
            "trse_growth": 100 * np.log(trse_avail).diff(),
            "d_trcape": 100 * log_trcape.diff(),
            "log_dy": np.log(dividend_avail / price),
            "log_cape": log_real_price - np.log(_ten_year_mean(real_earn_avail)),
            "infl_yoy": 100 * (log_cpi_avail - log_cpi_avail.shift(12)),
            "d_rate_12": raw["lrir10"].diff(12),
            "mom_12": 100 * (log_real_price - log_real_price.shift(12)),
            "vol_12": monthly_real.rolling(12, min_periods=12).std() * np.sqrt(12),
            # Robustness predictors.
            "ecy": 100 * np.exp(-(log_real_price - np.log(_ten_year_mean(real_earn_avail))))
            - (raw["lrir10"] - 10 * (log_cpi_avail - log_cpi_avail.shift(120))),
            "log_payout": np.log(dividend_avail / raw["earnings"].shift(FUNDAMENTALS_LAG)),
            "earn_growth_12": 100 * (np.log(real_earn_avail) - np.log(real_earn_avail.shift(12))),
            "rate_level": raw["lrir10"],
            "drawdown": 100 * (log_real_price - log_real_price.rolling(12, min_periods=12).max()),
        },
        index=raw.index,
    )
    return out


def standardize(frame: pd.DataFrame, reference: pd.DataFrame | None = None) -> pd.DataFrame:
    """Z-score columns using the mean and standard deviation of `reference`."""
    ref = frame if reference is None else reference
    return (frame - ref.mean()) / ref.std(ddof=0)
