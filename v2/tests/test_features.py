"""No predictor may use information from after its forecast origin."""

import numpy as np
import pandas as pd
import pytest

from psm.data import ARCHIVED_LEAD_COLUMNS
from psm.features import ALLOWED_RAW_COLUMNS, build_features, real_price_index


@pytest.mark.parametrize("cut", ["1935-06-01", "1974-09-01", "2008-10-01"])
def test_features_unchanged_when_future_data_change(raw, cut):
    """Perturb every raw value after `cut`; features dated at or before `cut` must not move."""
    rng = np.random.default_rng(0)
    base = build_features(raw)
    shocked = raw.copy()
    future = shocked.index > pd.Timestamp(cut)
    shocked.loc[future] = shocked.loc[future] * rng.uniform(0.5, 1.5, size=shocked.loc[future].shape)
    after = build_features(shocked)
    pd.testing.assert_frame_equal(base.loc[:cut], after.loc[:cut])
    # Sanity: the shock does reach later rows.
    assert not base.loc[cut:].iloc[2:].equals(after.loc[cut:].iloc[2:])


def test_features_ignore_archived_lead_columns(raw):
    pd.testing.assert_frame_equal(
        build_features(raw), build_features(raw.drop(columns=list(ARCHIVED_LEAD_COLUMNS)))
    )
    assert not set(ARCHIVED_LEAD_COLUMNS) & set(ALLOWED_RAW_COLUMNS)


def test_publication_lags_are_applied(raw):
    """CPI enters with a one-month lag and dividends with a six-month lag."""
    f = build_features(raw)
    t = pd.Timestamp("1990-07-01")
    cpi = raw["infl"]
    expected_infl = 100 * (np.log(cpi.loc["1990-06-01"]) - np.log(cpi.loc["1990-05-01"]))
    assert f.loc[t, "infl_m"] == pytest.approx(expected_infl)
    expected_dy = np.log(raw.loc["1990-01-01", "dividend"] / raw.loc[t, "spprice"])
    assert f.loc[t, "log_dy"] == pytest.approx(expected_dy)


def test_real_price_uses_lagged_cpi(raw):
    p = real_price_index(raw)
    ratio = (p / (raw["spprice"] / raw["infl"].shift(1))).dropna()
    assert np.allclose(ratio, ratio.median(), rtol=1e-3)  # archived values are rounded to cents
