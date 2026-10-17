"""Replication of the archived (award) specification, flaws included.

This module deliberately reproduces three problems of the archived `code.R`
so their effect can be measured. Nothing here feeds the corrected analysis.

1. The Markov-switching equation regresses 100 ln P_t on the archived
   `realpricelag` column, which holds next month's price P_{t+1}.
2. `dplyr::lag(Q, k)` builds the "k months ahead" target, so the regressions
   relate Q_{t-k} (the past) to the predictor change at t.
3. The "MSPE ratio" divides squared mean errors, (mean e_u)^2 / (mean e_r)^2,
   rather than mean squared errors.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.othermod.betareg import BetaModel
from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression

from psm.config import THESIS_SAMPLE
from psm.regressions import squeeze_unit

# Archived predictors (first differences of raw levels) and their table names.
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


@dataclass(frozen=True)
class ArchivedRegimes:
    regime_prob: pd.Series  # filtered probability of the high-variance ("bear") regime
    transition: np.ndarray  # row-stochastic, ordered (bull, bear)
    llf: float


def archived_frame(raw: pd.DataFrame) -> pd.DataFrame:
    """The archived design matrix: rows 1959:12-2023:12, differenced, first row dropped."""
    df = raw.loc[THESIS_SAMPLE.start - pd.DateOffset(months=1) : THESIS_SAMPLE.end].copy()
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
        start = np.array(
            [p00, 1 - p11, ols.params[0] + 1, ols.params[0] - 1, ols.params[1], ols.params[1],
             ols.mse_resid * 0.5, ols.mse_resid * 2]
        )
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
    names = best.model.param_names
    p = dict(zip(names, best.params))
    bear = int(np.argmax([p["sigma2[0]"], p["sigma2[1]"]]))
    order = [1 - bear, bear]
    row = best.regime_transition[:, :, 0].T
    prob = np.asarray(best.filtered_marginal_probabilities)[:, bear]
    return ArchivedRegimes(
        regime_prob=pd.Series(prob, index=df.index, name="Q_archived"),
        transition=row[np.ix_(order, order)],
        llf=float(best.llf),
    )


def archived_target(q: pd.Series, k: int) -> pd.Series:
    """`dplyr::lag(Q, k)`: the value k months *earlier*, mislabeled 'ahead k'."""
    return q.shift(k)


def archived_in_sample(df: pd.DataFrame, q: pd.Series) -> pd.DataFrame:
    """Archived univariate OLS with classical standard errors, as `lm()` reports them."""
    rows = []
    for col in ARCHIVED_PREDICTORS:
        for k in ARCHIVED_HORIZONS:
            data = pd.concat([archived_target(q, k).rename("y"), df[col]], axis=1).iloc[k:]
            res = sm.OLS(data["y"], sm.add_constant(data[col])).fit()
            rows.append(
                {
                    "predictor": col,
                    "k": k,
                    "coef": float(res.params[col]),
                    "se": float(res.bse[col]),
                    "r2": float(res.rsquared),
                    "nobs": int(res.nobs),
                }
            )
    return pd.DataFrame(rows)


def archived_mspe(df: pd.DataFrame, q: pd.Series, horizons: tuple[int, ...]) -> pd.DataFrame:
    """Archived 80/20 holdout: both the archived ratio and the correct MSPE ratio."""
    rows = []
    cut = int(round(0.8 * (len(df) - 1)))  # code.R reuses the k = 1 split point for every k
    for k in horizons:
        data = pd.concat([archived_target(q, k).rename("y"), df[list(ARCHIVED_PREDICTORS)]], axis=1)
        data = data.iloc[k:]
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
                rows.append(
                    {
                        "model": model,
                        "predictor": col,
                        "k": k,
                        "test_start": test.index[0],
                        "archived_ratio": float(eu.mean() ** 2 / er.mean() ** 2),
                        "mspe_ratio": float(np.mean(eu**2) / np.mean(er**2)),
                    }
                )
    return pd.DataFrame(rows)
