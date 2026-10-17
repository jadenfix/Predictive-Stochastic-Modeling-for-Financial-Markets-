"""Two-regime Markov-switching models for monthly real S&P 500 returns.

Two specifications are estimated by maximum likelihood with statsmodels:

* ``"mean_var"``: r_t = mu_{S_t} + e_t, e_t ~ N(0, sigma2_{S_t});
* ``"ar1"``:      r_t - mu_{S_t} = phi (r_{t-1} - mu_{S_{t-1}}) + e_t (Hamilton, 1989).

Starting values come from a fixed grid, so estimation is deterministic. The
bear regime is the one with the lower mean return.
"""

from __future__ import annotations

import itertools
import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd
from statsmodels.tsa.regime_switching.markov_autoregression import MarkovAutoregression
from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression

from psm.regressions import Coef

KINDS = ("mean_var", "ar1")


def _model(returns: pd.Series, kind: str):
    y = returns.to_numpy(dtype=float)
    if kind == "mean_var":
        return MarkovRegression(y, k_regimes=2, trend="c", switching_variance=True)
    if kind == "ar1":
        return MarkovAutoregression(
            y, k_regimes=2, order=1, switching_ar=False, switching_variance=True
        )
    raise ValueError(f"unknown kind {kind!r}")


def _start_grid(returns: pd.Series, kind: str, names: list[str]) -> list[np.ndarray]:
    m, s2 = float(returns.mean()), float(returns.var())
    s = np.sqrt(s2)
    grid = []
    for (p00, p11), gap, ratio in itertools.product(
        [(0.97, 0.90), (0.95, 0.80), (0.90, 0.60)], [0.5, 1.5], [3.0, 8.0]
    ):
        values = {
            "p[0->0]": p00,
            "p[1->0]": 1 - p11,
            "const[0]": m + 0.2 * gap * s,
            "const[1]": m - gap * s,
            "sigma2[0]": s2 * 2 / (1 + ratio),
            "sigma2[1]": s2 * 2 * ratio / (1 + ratio),
            "ar.L1": 0.2,
        }
        grid.append(np.array([values[n] for n in names]))
    return grid


@dataclass(frozen=True)
class RegimeFit:
    """A fitted two-regime model with regimes ordered as (bull, bear)."""

    kind: str
    index: pd.DatetimeIndex
    params: np.ndarray
    bear: int  # position of the bear regime in the statsmodels parameterization
    llf: float
    aic: float
    bic: float
    nobs: int
    means: tuple[float, float]  # (bull, bear) mean monthly return, percent
    variances: tuple[float, float]  # (bull, bear) innovation variance
    transition: np.ndarray  # row-stochastic, rows/cols ordered (bull, bear)
    ar: float | None
    filtered: pd.Series  # P(bear at t | returns through t)
    smoothed: pd.Series  # P(bear at t | full sample); retrospective only
    coefs: dict[str, Coef]  # named estimates with standard errors

    @property
    def durations(self) -> tuple[float, float]:
        """Expected regime durations in months, 1 / (1 - p_ii)."""
        return tuple(float(1 / (1 - self.transition[i, i])) for i in range(2))

    def forecast(self, horizon: int) -> pd.Series:
        """P(bear at t + h | returns through t), propagated from filtered probabilities."""
        return bear_forecast(self.filtered, self.transition, horizon)


def bear_forecast(filtered_bear: pd.Series, transition: np.ndarray, horizon: int) -> pd.Series:
    """Propagate filtered bear probabilities h steps with a (bull, bear) transition matrix."""
    step = np.linalg.matrix_power(transition, horizon)
    probs = np.column_stack([1 - filtered_bear.to_numpy(), filtered_bear.to_numpy()])
    return pd.Series((probs @ step)[:, 1], index=filtered_bear.index, name=f"ms_h{horizon}")


def _named_coefs(res, bull: int, bear: int) -> dict[str, Coef]:
    names = res.model.param_names
    est = dict(zip(names, np.asarray(res.params)))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        se = dict(zip(names, np.asarray(res.bse)))
        pv = dict(zip(names, np.asarray(res.pvalues)))

    def stay(i: int) -> Coef:
        # p[i->i]; statsmodels estimates p[0->0] and p[1->0] directly.
        if i == 0:
            return Coef(est["p[0->0]"], se["p[0->0]"], np.nan)
        return Coef(1 - est["p[1->0]"], se["p[1->0]"], np.nan)

    out = {
        "mean_bull": Coef(est[f"const[{bull}]"], se[f"const[{bull}]"], pv[f"const[{bull}]"]),
        "mean_bear": Coef(est[f"const[{bear}]"], se[f"const[{bear}]"], pv[f"const[{bear}]"]),
        "sigma2_bull": Coef(est[f"sigma2[{bull}]"], se[f"sigma2[{bull}]"], np.nan),
        "sigma2_bear": Coef(est[f"sigma2[{bear}]"], se[f"sigma2[{bear}]"], np.nan),
        "p_bull_bull": stay(bull),
        "p_bear_bear": stay(bear),
    }
    if "ar.L1" in est:
        out["ar"] = Coef(est["ar.L1"], se["ar.L1"], pv["ar.L1"])
    return out


def _summarize(kind: str, res, model_index: pd.DatetimeIndex) -> RegimeFit:
    names = res.model.param_names
    p = dict(zip(names, res.params))
    consts = np.array([p["const[0]"], p["const[1]"]])
    bear = int(np.argmin(consts))
    bull = 1 - bear
    col_stoch = res.regime_transition[:, :, 0]  # [i, j] = P(S_t = i | S_{t-1} = j)
    row = col_stoch.T
    order = [bull, bear]
    transition = row[np.ix_(order, order)]
    sig = np.array([p["sigma2[0]"], p["sigma2[1]"]])
    filtered = np.asarray(res.filtered_marginal_probabilities)[:, bear]
    smoothed = np.asarray(res.smoothed_marginal_probabilities)[:, bear]
    return RegimeFit(
        kind=kind,
        index=model_index,
        params=np.asarray(res.params),
        bear=bear,
        llf=float(res.llf),
        aic=float(res.aic),
        bic=float(res.bic),
        nobs=int(res.nobs),
        means=(float(consts[bull]), float(consts[bear])),
        variances=(float(sig[bull]), float(sig[bear])),
        transition=transition,
        ar=float(p["ar.L1"]) if "ar.L1" in p else None,
        filtered=pd.Series(filtered, index=model_index, name="filtered"),
        smoothed=pd.Series(smoothed, index=model_index, name="smoothed"),
        coefs=_named_coefs(res, bull, bear),
    )


def fit_regimes(
    returns: pd.Series, kind: str = "mean_var", warm_start: np.ndarray | None = None
) -> RegimeFit:
    """Fit a two-regime model by ML from a fixed grid of starting values."""
    returns = returns.dropna()
    model = _model(returns, kind)
    model_index = returns.index[len(returns) - model.nobs :]
    starts = _start_grid(returns, kind, list(model.param_names))
    if warm_start is not None:
        starts.insert(0, np.asarray(warm_start))
    best = None
    for start in starts:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                res = model.fit(start_params=start, disp=False, maxiter=500)
            except (np.linalg.LinAlgError, ValueError):
                continue
        if not np.isfinite(res.llf) or np.any(~np.isfinite(res.params)):
            continue
        if best is None or res.llf > best.llf + 1e-9:
            best = res
    if best is None:
        raise RuntimeError("Markov-switching estimation failed from every start")
    return _summarize(kind, best, model_index)


def refilter(returns: pd.Series, fit: RegimeFit) -> pd.Series:
    """Filtered bear probabilities on a (longer) return history with fixed parameters."""
    returns = returns.dropna()
    model = _model(returns, fit.kind)
    res = model.filter(fit.params)
    model_index = returns.index[len(returns) - model.nobs :]
    return pd.Series(
        np.asarray(res.filtered_marginal_probabilities)[:, fit.bear], index=model_index
    )
