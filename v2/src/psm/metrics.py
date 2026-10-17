"""Forecast evaluation metrics and tests of equal predictive accuracy."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

LOG_LOSS_FLOOR = 1e-3


def brier(p: np.ndarray, y: np.ndarray) -> float:
    """Mean squared error of probability forecasts."""
    return float(np.mean((np.asarray(p) - np.asarray(y)) ** 2))


def log_loss(p: np.ndarray, y: np.ndarray, floor: float = LOG_LOSS_FLOOR) -> float:
    """Mean negative log-likelihood; probabilities are truncated to [floor, 1 - floor]."""
    q = np.clip(np.asarray(p, dtype=float), floor, 1 - floor)
    y = np.asarray(y)
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
    """Mean forecast and observed frequency within forecast quantile bins.

    Quantile (rather than equal-width) bins keep every point backed by roughly
    n / bins forecasts; tied forecasts share a bin.
    """
    p, y = np.asarray(p, dtype=float), np.asarray(y, dtype=float)
    which = pd.qcut(p, bins, labels=False, duplicates="drop")
    rows = []
    for b in np.unique(which):
        mask = which == b
        rows.append(
            {"bin": int(b), "forecast": p[mask].mean(), "observed": y[mask].mean(), "count": int(mask.sum())}
        )
    return pd.DataFrame(rows)


def _hac_variance(d: np.ndarray, lags: int) -> float:
    d = d - d.mean()
    n = len(d)
    var = d @ d / n
    for k in range(1, lags + 1):
        w = 1 - k / (lags + 1)
        var += 2 * w * (d[k:] @ d[:-k]) / n
    return float(var)


def diebold_mariano(loss_model: np.ndarray, loss_ref: np.ndarray, horizon: int) -> tuple[float, float]:
    """DM statistic for mean(loss_model - loss_ref) with the HLN small-sample correction.

    Returns (statistic, one-sided p-value) for H1: the model has lower expected loss.
    Bartlett-kernel HAC variance with h - 1 lags, at least one.
    """
    d = np.asarray(loss_model) - np.asarray(loss_ref)
    n = len(d)
    lags = max(horizon - 1, 1)
    var = _hac_variance(d, lags)
    if var <= 0:
        return float("nan"), float("nan")
    dm = d.mean() / np.sqrt(var / n)
    hln = np.sqrt((n + 1 - 2 * horizon + horizon * (horizon - 1) / n) / n)
    stat = float(dm * hln)
    return stat, float(stats.t.cdf(stat, df=n - 1))


def clark_west(
    actual: np.ndarray, pred_restricted: np.ndarray, pred_unrestricted: np.ndarray, horizon: int
) -> tuple[float, float]:
    """Clark-West (2007) MSPE-adjusted test for nested models.

    Returns (statistic, one-sided p-value) for H1: the unrestricted model is more accurate.
    """
    e1 = np.asarray(actual) - np.asarray(pred_restricted)
    e2 = np.asarray(actual) - np.asarray(pred_unrestricted)
    f = e1**2 - (e2**2 - (np.asarray(pred_restricted) - np.asarray(pred_unrestricted)) ** 2)
    var = _hac_variance(f, max(horizon - 1, 1))
    if var <= 0:
        return float("nan"), float("nan")
    stat = float(f.mean() / np.sqrt(var / len(f)))
    return stat, float(1 - stats.norm.cdf(stat))
