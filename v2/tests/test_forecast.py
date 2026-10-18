"""The real-time engine must not see prices, labels, returns or predictors after the origin."""

import numpy as np
import pandas as pd
import pytest

import thesis as T

MODELS = ("uncond", "persist", "ms", "tvtp", "logit_dy", "logit_all", "probit_all", "logit_state", "enet", "gbt_rich",
          "uni_log_dy", "uni_drawdown", "combo")


def _run(panel: pd.DataFrame, origins: pd.DatetimeIndex, window: int | None = None) -> pd.DataFrame:
    price = T.real_price_index(panel).dropna()
    idx = price.index
    features = T.build_features(panel).reindex(idx)
    returns = T.real_returns(panel).reindex(idx)
    labels = T.label_series(price)
    ms = T.fit_vintage_regimes(returns.loc[: origins[-1]], origins)
    tv = T.fit_vintage_tvtp(returns.loc[: origins[-1]], features.loc[: origins[-1]], origins, ms)
    spec = T.RunSpec("main", "main", price, labels, T.BEAR_DECLINE, MODELS, window)
    runs, extra = T.run_forecasts([spec], features, returns, origins, (1, 6), {"ms": ms, "tvtp": tv})
    fc = runs["main"]
    dma = T.dma_combination(fc, ("persist", "logit_all", "gbt_rich"), "dma", extra["vintages"], idx)
    return pd.concat([fc, dma], ignore_index=True)


@pytest.fixture(scope="module")
def small(panel):
    return panel.loc[:"1975-12-01"]


def test_forecasts_invariant_to_data_after_origin(small):
    origins = pd.DatetimeIndex(["1969-06-01", "1969-12-01", "1970-01-01"])
    base = _run(small, origins)
    shocked = small.copy()
    later = shocked.index > origins[-1]
    shocked.loc[later] = shocked.loc[later] * np.random.default_rng(3).uniform(0.3, 1.7, shocked.loc[later].shape)
    after = _run(shocked, origins)
    assert set(base.model) == set(MODELS) | {"dma"}
    pd.testing.assert_series_equal(base["p"], after["p"])
    assert (base[base.model != "dma"]["n_train"] > 0).all()


def test_rolling_window_limits_training_sample(panel):
    sample = panel.loc[:"1965-12-01"]
    price = T.real_price_index(sample).dropna()
    idx = price.index
    features = T.build_features(sample).reindex(idx)
    labels = T.label_series(price)
    origins = pd.DatetimeIndex(["1964-01-01"])
    models = ("uncond", "persist", "logit_dy")
    specs = [T.RunSpec("expanding", "", price, labels, 0.2, models), T.RunSpec("rolling", "", price, labels, 0.2, models, 120)]
    runs, _ = T.run_forecasts(specs, features, T.real_returns(sample).reindex(idx), origins, (1,), {})
    assert (runs["rolling"].n_train == 120).all() and (runs["expanding"].n_train > 120).all()


def test_dma_starts_with_equal_weights_and_uses_only_scored_forecasts():
    dates = pd.date_range("2000-01-01", periods=30, freq="MS")
    rows = []
    for i, o in enumerate(dates[10:20]):
        for m, p in (("a", 0.9), ("b", 0.1)):
            rows.append({"origin": o, "horizon": 3, "target_date": dates[13 + i], "y": 1, "model": m, "p": p})
    fc = pd.DataFrame(rows)
    vintages = {o: np.ones(dates.get_loc(o) + 1, dtype=np.int8) for o in dates[10:20]}
    out = T.dma_combination(fc, ("a", "b"), "dma", vintages, dates, alpha=1.0).set_index("origin")
    first = dates[10]
    assert out.loc[first, "p"] == pytest.approx(0.5) and out.loc[first, "n_train"] == 0
    # At origin 13 exactly one forecast (made at 10, target 13) has been scored.
    assert out.loc[dates[13], "n_train"] == 1
    w_a = 0.9 / (0.9 + 0.1)
    assert out.loc[dates[13], "p"] == pytest.approx(w_a * 0.9 + (1 - w_a) * 0.1)
