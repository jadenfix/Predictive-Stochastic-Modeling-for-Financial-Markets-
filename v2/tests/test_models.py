"""Estimators used inside the real-time loop: Newton solvers and the machine-learning wrappers."""

import numpy as np
import pandas as pd
import statsmodels.api as sm

import thesis as T


def _data(seed: int, n: int = 400) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    X = sm.add_constant(rng.normal(size=(n, 3)))
    y = (rng.uniform(size=n) < 1 / (1 + np.exp(-(X @ np.array([-0.5, 1.0, -0.7, 0.2]))))).astype(float)
    return X, y


def test_newton_logit_and_probit_match_statsmodels():
    X, y = _data(2)
    assert np.allclose(T.newton_binary(y, X, "logit"), sm.Logit(y, X).fit(disp=0).params, atol=1e-7)
    assert np.allclose(T.newton_binary(y, X, "probit"), sm.Probit(y, X).fit(disp=0).params, atol=1e-6)


def test_ml_selection_is_deterministic_and_uses_the_grid():
    X, y = _data(3, 600)
    for kind, grid in (("enet", T.ENET_GRID), ("gbt", T.GBT_GRID)):
        a, b = T.fit_ml(kind, X[:, 1:], y, 3, validation=120), T.fit_ml(kind, X[:, 1:], y, 3, validation=120)
        assert a.params in grid and a.params == b.params
        assert a.predict(X[0, 1:]) == b.predict(X[0, 1:])
        assert 0 < a.predict(X[0, 1:]) < 1


def test_ml_validation_ignores_the_last_rows_when_fitting_candidates():
    """Changing the labels in the validation block can change the choice, but changing labels in
    the gap between the estimation and validation blocks cannot affect any candidate fit."""
    X, y = _data(4, 500)
    horizon, validation = 6, 100
    gap = slice(len(y) - validation - horizon, len(y) - validation)
    y2 = y.copy()
    y2[gap] = 1 - y2[gap]
    f1 = T.fit_ml("enet", X[:, 1:], y, horizon, validation)
    f2 = T.fit_ml("enet", X[:, 1:], y2, horizon, validation)
    assert f1.params == f2.params


def test_ols_and_logit_wrappers_report_hac_errors():
    rng = np.random.default_rng(5)
    idx = pd.date_range("1950-01-01", periods=300, freq="MS")
    x = pd.DataFrame({"x": rng.normal(size=300)}, index=idx)
    target = pd.Series((rng.uniform(size=300) < 0.3).astype(float), index=idx)
    fit = T.fit_binary(target, x, 3)
    assert fit.nobs == 297 and fit.stats["nw_lags"] == T.nw_lags(297, 3)
    assert fit.start == idx[0] and fit.end == idx[-4]
