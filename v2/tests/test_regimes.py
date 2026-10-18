"""Regime models: causal filtering, regime ordering, and the time-varying transition model."""

import numpy as np
import pandas as pd
import pytest

import thesis as T


@pytest.fixture(scope="module")
def returns(panel):
    return T.real_returns(panel).loc["1960-01-01":]


def test_filtered_probabilities_are_causal(returns):
    fit = T.fit_regimes(returns.loc[:"1999-12-01"], "ar1")
    full = T.regime_track(returns, pd.DataFrame(index=returns.index), fit, (1,))[1]
    cut = pd.Timestamp("1985-06-01")
    shocked = returns.copy()
    later = shocked.index > cut
    shocked.loc[later] *= np.random.default_rng(4).uniform(-3, 3, later.sum())
    after = T.regime_track(shocked, pd.DataFrame(index=returns.index), fit, (1,))[1]
    pd.testing.assert_series_equal(full.loc[:cut], after.loc[:cut])
    assert not np.allclose(full.loc[cut:].iloc[1:], after.loc[cut:].iloc[1:])


def test_regime_ordering_and_forecast_limit(returns):
    fit = T.fit_regimes(returns, "mean_var")
    assert fit.means[1] < fit.means[0]
    assert np.allclose(fit.transition.sum(axis=1), 1)
    far = T.bear_forecast(fit.filtered.to_numpy(), fit.transition, 600)
    p = fit.transition
    assert np.allclose(far, (1 - p[0, 0]) / (2 - p[0, 0] - p[1, 1]), atol=1e-6)


def _simulate_tvtp(n: int, seed: int) -> tuple[pd.Series, pd.DataFrame]:
    """Two-regime returns whose bull-to-bear switching probability rises with a predictor x_{t-1}."""
    rng = np.random.default_rng(seed)
    x = rng.normal(size=n)
    s = np.zeros(n, dtype=int)
    for t in range(1, n):
        if s[t - 1] == 0:  # bull: P(stay bull) = logistic(3 - 1.5 x_{t-1})
            s[t] = int(rng.uniform() > 1 / (1 + np.exp(-(3.0 - 1.5 * x[t - 1]))))
        else:  # bear: P(back to bull) = 0.15
            s[t] = int(rng.uniform() > 0.15)
    r = np.where(s == 0, 1.0, -2.0) + np.where(s == 0, 2.0, 5.0) * rng.normal(size=n)
    idx = pd.date_range("1900-01-01", periods=n, freq="MS")
    return pd.Series(r, index=idx), pd.DataFrame({"x": x}, index=idx)


def test_tvtp_with_zero_slopes_is_the_fixed_model(returns, panel):
    """A known case: with all slopes set to zero, the TVTP likelihood and filter equal the fixed model's."""
    features = T.build_features(panel)
    fixed = T.fit_regimes(returns, "ar1")
    tv = T.fit_tvtp(returns, features, keys=("infl_yoy",), fixed=fixed, grid=False)
    lagged = features[["infl_yoy"]].shift(1)
    model = T._ms_model(returns, "tvtp", T._tvtp_lagged(returns, features, ("infl_yoy",), tv.tvtp_center))
    raw = dict(zip(fixed.param_names, fixed.params))
    zero = np.array([{"p[0->0].tvtp0": T._logit(raw["p[0->0]"]), "p[1->0].tvtp0": T._logit(raw["p[1->0]"])}.get(n, raw.get(n, 0.0))
                     for n in model.param_names])
    assert lagged.reindex(returns.index).notna().all().all()
    assert model.loglike(zero) == pytest.approx(fixed.llf, rel=1e-10)
    assert tv.llf >= fixed.llf - 1e-6  # nesting: the TVTP fit can only improve the likelihood


def test_tvtp_recovers_a_known_transition_effect():
    r, x = _simulate_tvtp(2500, 11)
    fit = T.fit_tvtp(r, x, keys=("x",))
    stay = T.tvtp_slopes(fit)[("stay", "x")]
    true = -1.5 * x["x"].std(ddof=0)  # slope per standard deviation of x
    assert fit.means[0] == pytest.approx(1.0, abs=0.3) and fit.means[1] == pytest.approx(-2.0, abs=1.0)
    assert abs(stay.estimate - true) < 3 * stay.se + 0.3


def test_tvtp_row_t_drives_the_transition_into_t(returns, panel):
    """statsmodels' exog_tvtp row t must affect filtered probabilities from month t on, never before."""
    features = T.build_features(panel)
    fit = T.fit_tvtp(returns, features, keys=("infl_yoy",), grid=False)
    design = T._tvtp_lagged(returns, features, ("infl_yoy",), fit.tvtp_center)
    base = T._ms_model(returns, "tvtp", design).filter(fit.params).filtered_marginal_probabilities[:, fit.bear]
    j = 300
    bumped = design.copy()
    bumped[j, 1] += 3.0
    after = T._ms_model(returns, "tvtp", bumped).filter(fit.params).filtered_marginal_probabilities[:, fit.bear]
    # Filtered series start at the second return (AR(1) trimming): row j maps to position j - 1.
    assert np.allclose(base[: j - 1], after[: j - 1])
    assert not np.isclose(base[j - 1], after[j - 1])


def test_tvtp_track_ignores_later_predictors_and_returns(returns, panel):
    features = T.build_features(panel)
    fit = T.fit_tvtp(returns.loc[:"1990-12-01"], features, grid=False)
    cut = pd.Timestamp("1985-06-01")
    base = T.regime_track(returns, features, fit, (1, 6))
    shocked_f, shocked_r = features.copy(), returns.copy()
    later_f, later_r = features.index > cut, returns.index > cut
    rng = np.random.default_rng(8)
    shocked_f.loc[later_f] = shocked_f.loc[later_f] * rng.uniform(0.5, 1.5, shocked_f.loc[later_f].shape)
    shocked_r.loc[later_r] = shocked_r.loc[later_r] * rng.uniform(-2, 2, later_r.sum())
    after = T.regime_track(shocked_r, shocked_f, fit, (1, 6))
    for h in (1, 6):
        pd.testing.assert_series_equal(base[h].loc[:cut], after[h].loc[:cut])


def test_alternative_specs_order_regimes(returns):
    var_only = T.fit_spec("v", returns, 2, False, True)
    assert var_only.means[0] == var_only.means[1] and var_only.sds[1] > var_only.sds[0]
    three = T.fit_spec("t", returns, 3, True, True)
    assert three.means[0] > three.means[1] > three.means[2]
    assert np.isfinite(three.llf) and len(three.bear_filtered) == three.nobs
