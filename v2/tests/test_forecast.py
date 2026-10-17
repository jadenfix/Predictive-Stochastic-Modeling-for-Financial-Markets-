"""The out-of-sample engine must not see prices, labels or predictors after the origin."""

import numpy as np
import pandas as pd

from psm.features import FORECAST_FEATURES, build_features, real_price_index, real_returns
from psm.forecast import bear_forecasts, fit_vintage_regimes
from psm.labels import label_series


def _run(raw: pd.DataFrame, origins: pd.DatetimeIndex) -> pd.DataFrame:
    price = real_price_index(raw).dropna()
    idx = price.index
    feats = build_features(raw).reindex(idx)[[f.key for f in FORECAST_FEATURES]]
    returns = real_returns(raw).reindex(idx)
    labels = label_series(price)
    vint = fit_vintage_regimes(returns.loc[: origins[-1]], origins)
    return bear_forecasts(price, feats, labels.bear_now, labels.bear, returns, vint, origins, (1, 6))


def test_forecasts_invariant_to_data_after_origin(raw):
    sample = raw.loc[:"1975-12-01"]
    origins = pd.DatetimeIndex(["1969-06-01", "1970-01-01"])
    base = _run(sample, origins)
    shocked = sample.copy()
    later = shocked.index > origins[-1]
    rng = np.random.default_rng(3)
    shocked.loc[later] = shocked.loc[later] * rng.uniform(0.3, 1.7, size=shocked.loc[later].shape)
    after = _run(shocked, origins)
    pd.testing.assert_series_equal(base["p"], after["p"])
    assert (base["n_train"] > 0).all()
