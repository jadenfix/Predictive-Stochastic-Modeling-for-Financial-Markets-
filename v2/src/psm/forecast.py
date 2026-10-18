"""Expanding-window, real-time out-of-sample forecasting.

At each forecast origin t every model is re-estimated using only information
available at the end of month t:

* predictors x_s for s <= t (already lagged for publication in `psm.features`);
* bear labels obtained by dating the price history *through t only*
  ("vintage" labels), so a pair (x_s, y_{s+h}) enters training only if s + h <= t;
* Markov-switching parameters re-estimated every January on returns through t,
  with filtered (never smoothed) probabilities.
"""

from __future__ import annotations

import warnings
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.othermod.betareg import BetaModel

from psm.config import BEAR_DECLINE, BULL_RISE
from psm.labels import date_bear_markets
from psm.regimes import RegimeFit, bear_forecast, fit_regimes, refilter
from psm.regressions import squeeze_unit

# Model keys, in display order, with plain-English names.
BEAR_MODELS: dict[str, str] = {
    "uncond": "Unconditional frequency",
    "persist": "Persistence (real-time state)",
    "ms": "MS-AR(1) filtered probability",
    "logit_dy": "Logit: dividend yield",
    "logit_all": "Logit: all predictors",
    "probit_all": "Probit: all predictors",
    "logit_state": "Logit: all predictors + state",
}
BASELINES = ("uncond", "persist")


def _jeffreys(successes: float, n: float) -> float:
    return (successes + 0.5) / (n + 1)


def _zscore(train: np.ndarray, test: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mu, sd = train.mean(axis=0), train.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    return (train - mu) / sd, (test - mu) / sd


def _newton_logit(y: np.ndarray, X: np.ndarray, maxiter: int = 50, tol: float = 1e-10) -> np.ndarray | None:
    """Logit maximum likelihood by Newton-Raphson; None if it does not converge cleanly.

    Gives the same estimates as statsmodels' Logit (to numerical tolerance) at a
    fraction of the cost, which matters for the tens of thousands of refits in the
    out-of-sample and robustness exercises.
    """
    beta = np.zeros(X.shape[1])
    for _ in range(maxiter):
        eta = X @ beta
        p = 1 / (1 + np.exp(-eta))
        w = p * (1 - p)
        grad = X.T @ (y - p)
        hess = (X * w[:, None]).T @ X
        try:
            step = np.linalg.solve(hess, grad)
        except np.linalg.LinAlgError:
            return None
        beta = beta + step
        if not np.all(np.isfinite(beta)) or np.max(np.abs(beta)) > 30:
            return None
        if np.max(np.abs(step)) < tol:
            return beta
    return None


def _binary(link: str, y: np.ndarray, X: np.ndarray, x_new: np.ndarray) -> float:
    Xz, xz = _zscore(X, x_new[None, :])
    Xc = sm.add_constant(Xz, has_constant="add")
    xc = sm.add_constant(xz, has_constant="add")
    if link == "logit":
        beta = _newton_logit(np.asarray(y, dtype=float), Xc)
        if beta is not None:
            return float(1 / (1 + np.exp(-(xc @ beta)[0])))
    cls = {"logit": sm.Logit, "probit": sm.Probit}[link]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = cls(y, Xc).fit(disp=0, maxiter=200)
    return float(res.predict(xc)[0])


def _logit_odds(p: np.ndarray) -> np.ndarray:
    q = np.clip(p, 1e-4, 1 - 1e-4)
    return np.log(q / (1 - q))


@dataclass(frozen=True)
class VintageRegimes:
    """Markov-switching fits re-estimated each January on data through the origin."""

    fits: dict[pd.Timestamp, RegimeFit]

    def asof(self, origin: pd.Timestamp) -> RegimeFit:
        dates = [d for d in self.fits if d <= origin]
        return self.fits[max(dates)]


def fit_vintage_regimes(
    returns: pd.Series,
    origins: pd.DatetimeIndex,
    kind: str = "ar1",
    progress: Callable[[str], None] | None = None,
) -> VintageRegimes:
    """Estimate the regime model at the first origin and every January thereafter."""
    refit_dates = [origins[0], *[d for d in origins[1:] if d.month == 1]]
    fits: dict[pd.Timestamp, RegimeFit] = {}
    warm = None
    for date in refit_dates:
        fit = fit_regimes(returns.loc[:date], kind=kind, warm_start=warm)
        fits[date] = fit
        warm = fit.params
        if progress:
            progress(f"regime refit through {date:%Y-%m}")
    return VintageRegimes(fits)


def bear_forecasts(
    prices: pd.Series,
    features: pd.DataFrame,
    bear_now: pd.Series,
    final_labels: pd.Series,
    returns: pd.Series,
    vintages: VintageRegimes | None,
    origins: pd.DatetimeIndex,
    horizons: tuple[int, ...],
    dy_key: str = "log_dy",
    *,
    models: tuple[str, ...] | None = None,
    window: int | None = None,
    decline: float = BEAR_DECLINE,
    rise: float = BULL_RISE,
    univariate: tuple[str, ...] = (),
    combine: bool = False,
) -> pd.DataFrame:
    """Real-time probability forecasts of a bear market h months ahead.

    `models` selects a subset of `BEAR_MODELS` (default: all). `window` limits
    training to the most recent `window` forecast origins (rolling estimation;
    default expanding). `decline` and `rise` set the dating thresholds used for the
    vintage labels; `bear_now` and `final_labels` must be built with the same
    thresholds. Each key in `univariate` adds a one-predictor logit named
    ``uni_<key>``; `combine` adds ``combo``, the equal-weight average of those
    univariate forecasts. Returns a long frame with one row per (origin, horizon, model).
    """
    models = tuple(BEAR_MODELS) if models is None else models
    use_ms = "ms" in models
    if use_ms and vintages is None:
        raise ValueError("the MS model needs vintage regime fits")
    dates = prices.index
    pos = {d: i for i, d in enumerate(dates)}
    valid = features.notna().all(axis=1).to_numpy()
    feat = features.to_numpy(dtype=float)
    col = {c: i for i, c in enumerate(features.columns)}
    rows = []
    for origin in origins:
        t = pos[origin]
        vintage = date_bear_markets(prices.iloc[: t + 1].to_numpy(), decline, rise).labels
        if use_ms:
            fit = vintages.asof(origin)
            filtered = refilter(returns.loc[:origin], fit).reindex(dates[: t + 1])
        for h in horizons:
            if t + h >= len(dates):
                continue
            train = np.arange(0, t - h + 1)
            if window is not None:
                train = train[train > t - h - window]
            keep = valid[train]
            if use_ms:
                ms_h = bear_forecast(filtered, fit.transition, h).to_numpy()
                keep &= np.isfinite(ms_h[train])
            train = train[keep]
            y = vintage[train + h]
            X = feat[train]
            x_new = feat[t]
            state = bear_now.iloc[train].to_numpy()
            state_new = bear_now.iloc[t]
            preds: dict[str, float] = {}
            if "uncond" in models:
                preds["uncond"] = _jeffreys(y.sum(), len(y))
            if "persist" in models:
                same = state == state_new
                preds["persist"] = _jeffreys(y[same].sum(), same.sum())
            if use_ms:
                ms_odds = _logit_odds(ms_h[train])[:, None]
                preds["ms"] = _binary("logit", y, ms_odds, _logit_odds(ms_h[[t]]))
            if "logit_dy" in models:
                j = col[dy_key]
                preds["logit_dy"] = _binary("logit", y, feat[train][:, [j]], feat[t, [j]])
            if "logit_all" in models:
                preds["logit_all"] = _binary("logit", y, X, x_new)
            if "probit_all" in models:
                preds["probit_all"] = _binary("probit", y, X, x_new)
            if "logit_state" in models:
                preds["logit_state"] = _binary(
                    "logit", y, np.column_stack([X, state]), np.r_[x_new, state_new]
                )
            uni = []
            for key in univariate:
                j = col[key]
                uni.append(_binary("logit", y, feat[train][:, [j]], feat[t, [j]]))
                preds[f"uni_{key}"] = uni[-1]
            if combine and uni:
                preds["combo"] = float(np.mean(uni))
            target_date = dates[t + h]
            for model, p in preds.items():
                rows.append(
                    {
                        "origin": origin,
                        "horizon": h,
                        "target_date": target_date,
                        "y": int(final_labels.loc[target_date]),
                        "model": model,
                        "p": p,
                        "n_train": len(y),
                    }
                )
    return pd.DataFrame(rows)


def regime_prob_forecasts(
    target: pd.Series,
    features: pd.DataFrame,
    origins: pd.DatetimeIndex,
    horizons: tuple[int, ...],
    sample_start: pd.Timestamp,
) -> pd.DataFrame:
    """Expanding-window OLS and beta forecasts of the regime probability Q_{t+h}.

    Each predictor enters a separate univariate model, as in the archived thesis.
    The restricted benchmark is the training-sample mean (OLS) or the
    intercept-only beta regression. Returns one row per (origin, horizon, predictor).
    """
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
            y_beta = squeeze_unit(pd.Series(y)).to_numpy()
            actual = float(lead.iloc[t])
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
                    beta = BetaModel(y_beta, X).fit(
                        disp=0, maxiter=500, start_params=np.r_[b0.params[0], 0.0, b0.params[-1]]
                    )
                rows.append(
                    {
                        "origin": origin,
                        "horizon": h,
                        "predictor": key,
                        "actual": actual,
                        "ols_restricted": float(y.mean()),
                        "ols": float(ols.predict(x_new)[0]),
                        "beta_restricted": beta_restricted,
                        "beta": float(beta.predict(x_new)[0]),
                    }
                )
    return pd.DataFrame(rows)
