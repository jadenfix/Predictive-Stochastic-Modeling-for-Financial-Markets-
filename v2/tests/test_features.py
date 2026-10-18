"""No predictor may use information from after its forecast origin."""

import numpy as np
import pandas as pd
import pytest

import thesis as T


@pytest.mark.parametrize("cut", ["1935-06-01", "1974-09-01", "2008-10-01"])
def test_features_unchanged_when_future_data_change(panel, cut):
    """Perturb every value after `cut`; predictors dated at or before `cut` must not move."""
    rng = np.random.default_rng(0)
    base = T.build_features(panel)
    shocked = panel.copy()
    future = shocked.index > pd.Timestamp(cut)
    shocked.loc[future] = shocked.loc[future] * rng.uniform(0.5, 1.5, size=shocked.loc[future].shape)
    after = T.build_features(shocked)
    pd.testing.assert_frame_equal(base.loc[:cut], after.loc[:cut])
    assert not base.loc[cut:].iloc[2:].equals(after.loc[cut:].iloc[2:])


def test_features_read_only_the_declared_inputs(panel):
    pd.testing.assert_frame_equal(T.build_features(panel), T.build_features(panel[list(T.FEATURE_INPUTS)]))


def test_publication_lags_are_applied(panel):
    f = T.build_features(panel)
    t = pd.Timestamp("1990-07-01")
    cpi = panel["cpi"]
    assert f.loc[t, "infl_m"] == pytest.approx(100 * np.log(cpi.loc["1990-06-01"] / cpi.loc["1990-05-01"]))
    assert f.loc[t, "log_dy"] == pytest.approx(np.log(panel.loc["1990-01-01", "dividend"] / panel.loc[t, "price"]))
    assert f.loc[t, "log_payout"] == pytest.approx(
        np.log(panel.loc["1990-01-01", "dividend"] / panel.loc["1990-01-01", "earnings"]))


def test_real_price_uses_lagged_cpi(panel):
    p = T.real_price_index(panel)
    t = pd.Timestamp("2000-03-01")
    assert p.loc[t] == pytest.approx(panel.loc[t, "price"] / panel.loc["2000-02-01", "cpi"])


def test_real_bond_index_is_known_at_t(shiller):
    """Shiller's bond return in row t runs from t to t + 1; his real bond index at t compounds only
    the returns of earlier rows, so it is observable at t (parse_shiller enforces the identity)."""
    f = shiller.frame
    implied = f["real_bond"].shift(1) * f["bond_return"].shift(1) * f["cpi"].shift(1) / f["cpi"]
    assert np.allclose((f["real_bond"] / implied).dropna(), 1.0, atol=1e-9)
    assert "bond_return" not in T.FEATURE_INPUTS
