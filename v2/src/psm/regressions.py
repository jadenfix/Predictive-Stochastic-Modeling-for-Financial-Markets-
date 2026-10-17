"""Predictive regressions with a uniform result container for tables and figures.

* OLS of the regime probability Q_{t+h} on x_t, Newey-West (HAC) errors;
* beta regression of Q_{t+h} on x_t (logit mean link, Ferrari and Cribari-Neto, 2004);
* logit and probit of the dated bear indicator y_{t+h} on x_t, HAC errors.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.othermod.betareg import BetaModel


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
    end: pd.Timestamp  # last forecast origin
    stats: dict[str, float] = field(default_factory=dict)
    se_type: str = ""


def nw_lags(nobs: int, horizon: int) -> int:
    """Newey-West truncation lag: max(h, ceil(0.75 T^{1/3}))."""
    return max(horizon, math.ceil(0.75 * nobs ** (1 / 3)))


def align(target: pd.Series, features: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Pair x_t with target_{t+h}; rows are indexed by the forecast origin t."""
    lead = target.shift(-horizon).rename("target")
    return pd.concat([lead, features], axis=1).dropna()


def squeeze_unit(q: pd.Series) -> pd.Series:
    """Map [0, 1] into (0, 1): (q (n - 1) + 0.5) / n (Smithson and Verkuilen, 2006)."""
    n = len(q)
    return (q * (n - 1) + 0.5) / n


def _coefs(res, names: list[str]) -> dict[str, Coef]:
    """Mean-equation coefficients (beta regression also carries a precision term)."""
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
    return FitSummary(
        model="OLS",
        horizon=horizon,
        coefs=_coefs(res, ["const", *features.columns]),
        nobs=int(res.nobs),
        start=data.index[0],
        end=data.index[-1],
        stats={"r2": float(res.rsquared), "adj_r2": float(res.rsquared_adj), "nw_lags": lags},
        se_type=f"Newey-West ({lags} lags)",
    )


def fit_beta(target: pd.Series, features: pd.DataFrame, horizon: int) -> FitSummary:
    """Beta regression of target_{t+h} in (0, 1) on x_t, Newey-West standard errors."""
    data = align(squeeze_unit(target), features, horizon)
    X = sm.add_constant(data[features.columns])
    lags = nw_lags(len(data), horizon)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = BetaModel(data["target"], X).fit(
            disp=0, maxiter=500, cov_type="HAC", cov_kwds={"maxlags": lags}
        )
    eta = X.to_numpy() @ np.asarray(res.params[: X.shape[1]])
    logit_y = np.log(data["target"] / (1 - data["target"]))
    pseudo_r2 = float(np.corrcoef(eta, logit_y)[0, 1] ** 2) if X.shape[1] > 1 else 0.0
    return FitSummary(
        model="Beta",
        horizon=horizon,
        coefs=_coefs(res, ["const", *features.columns]),
        nobs=int(res.nobs),
        start=data.index[0],
        end=data.index[-1],
        stats={
            "pseudo_r2": pseudo_r2,
            "llf": float(res.llf),
            "aic": float(res.aic),
            "precision": float(np.exp(res.params.iloc[-1])),
            "nw_lags": lags,
        },
        se_type=f"Newey-West ({lags} lags)",
    )


def fit_binary(
    target: pd.Series, features: pd.DataFrame, horizon: int, link: str = "logit"
) -> FitSummary:
    """Logit or probit of the bear indicator y_{t+h} on x_t with Newey-West errors."""
    data = align(target, features, horizon)
    X = sm.add_constant(data[features.columns])
    lags = nw_lags(len(data), horizon)
    cls = {"logit": sm.Logit, "probit": sm.Probit}[link]
    res = cls(data["target"], X).fit(
        disp=0, maxiter=200, cov_type="HAC", cov_kwds={"maxlags": lags}
    )
    return FitSummary(
        model=link.capitalize(),
        horizon=horizon,
        coefs=_coefs(res, ["const", *features.columns]),
        nobs=int(res.nobs),
        start=data.index[0],
        end=data.index[-1],
        stats={
            "pseudo_r2": float(res.prsquared),
            "llf": float(res.llf),
            "aic": float(res.aic),
            "nw_lags": lags,
        },
        se_type=f"Newey-West ({lags} lags)",
    )
