"""Filtered regime probabilities must not depend on later returns."""

import numpy as np
import pandas as pd

from psm.features import real_returns
from psm.regimes import bear_forecast, fit_regimes, refilter


def test_filtered_probabilities_are_causal(raw):
    r = real_returns(raw).loc["1960-01-01":]
    fit = fit_regimes(r.loc[:"1999-12-01"], "ar1")
    full = refilter(r, fit)
    cut = pd.Timestamp("1985-06-01")
    shocked = r.copy()
    shocked.loc[shocked.index > cut] *= np.random.default_rng(4).uniform(-3, 3, (shocked.index > cut).sum())
    after = refilter(shocked, fit)
    pd.testing.assert_series_equal(full.loc[:cut], after.loc[:cut])
    assert not np.allclose(full.loc[cut:].iloc[1:], after.loc[cut:].iloc[1:])


def test_regime_ordering_and_forecast_limits(raw):
    fit = fit_regimes(real_returns(raw).loc["1960-01-01":], "mean_var")
    assert fit.means[1] < fit.means[0]
    assert np.allclose(fit.transition.sum(axis=1), 1)
    far = bear_forecast(fit.filtered, fit.transition, 600)
    p = fit.transition
    stationary_bear = (1 - p[0, 0]) / (2 - p[0, 0] - p[1, 1])
    assert np.allclose(far, stationary_bear, atol=1e-6)
