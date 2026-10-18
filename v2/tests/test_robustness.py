"""Robustness machinery: block bootstrap, rolling windows, alternative regime specifications."""

import numpy as np
import pandas as pd
import statsmodels.api as sm

from psm.features import FORECAST_FEATURES, build_features, real_price_index, real_returns
from psm.forecast import _newton_logit, bear_forecasts
from psm.labels import label_series
from psm.robustness import block_indices, bootstrap_skill, fit_spec


def test_block_indices_are_contiguous_circular_blocks():
    rng = np.random.default_rng(0)
    idx = block_indices(50, 7, 20, rng)
    assert idx.shape == (20, 50)
    assert idx.min() >= 0 and idx.max() < 50
    # Within a block, positions advance by one modulo n.
    step = (idx[:, 1:7] - idx[:, :6]) % 50
    assert (step == 1).all()


def test_bootstrap_gain_is_zero_for_a_copy_of_persistence():
    rng = np.random.default_rng(1)
    n = 120
    y = (rng.uniform(size=n) < 0.3).astype(int)
    p_u = np.full(n, 0.3)
    p_p = np.clip(0.3 + 0.4 * (y - 0.3) + rng.normal(0, 0.1, n), 0.01, 0.99)
    rows = []
    for m, p in (("uncond", p_u), ("persist", p_p), ("copy", p_p)):
        rows += [{"origin": i, "horizon": 1, "model": m, "p": p[i], "y": y[i]} for i in range(n)]
    boot = bootstrap_skill(pd.DataFrame(rows), ("persist", "copy"), block=12, reps=200)
    r = boot.loc[(1, "copy")]
    assert r.gain_lo == 0 and r.gain_hi == 0
    assert boot.loc[(1, "persist"), "bss_lo"] <= boot.loc[(1, "persist"), "bss"] <= boot.loc[(1, "persist"), "bss_hi"]


def test_newton_logit_matches_statsmodels():
    rng = np.random.default_rng(2)
    X = sm.add_constant(rng.normal(size=(400, 3)))
    y = (rng.uniform(size=400) < 1 / (1 + np.exp(-(X @ np.array([-0.5, 1.0, -0.7, 0.2]))))).astype(float)
    ours = _newton_logit(y, X)
    ref = sm.Logit(y, X).fit(disp=0).params
    assert np.allclose(ours, ref, atol=1e-7)


def test_rolling_window_limits_training_sample(raw):
    sample = raw.loc[:"1965-12-01"]
    price = real_price_index(sample).dropna()
    idx = price.index
    feats = build_features(sample).reindex(idx)[[f.key for f in FORECAST_FEATURES]]
    labels = label_series(price)
    origins = pd.DatetimeIndex(["1964-01-01"])
    kw = dict(models=("uncond", "persist", "logit_dy"))
    ret = real_returns(sample).reindex(idx)
    expanding = bear_forecasts(price, feats, labels.bear_now, labels.bear, ret, None, origins, (1,), **kw)
    rolling = bear_forecasts(price, feats, labels.bear_now, labels.bear, ret, None, origins, (1,), window=120, **kw)
    assert (rolling.n_train == 120).all()
    assert (expanding.n_train > 120).all()


def test_alternative_specs_order_regimes(raw):
    r = real_returns(raw).loc["1960-01-01":]
    var_only = fit_spec("v", r, 2, False, True)
    assert var_only.means[0] == var_only.means[1] and var_only.sds[1] > var_only.sds[0]
    three = fit_spec("t", r, 3, True, True)
    assert three.means[0] > three.means[1] > three.means[2]
    assert np.isfinite(three.llf) and len(three.bear_filtered) == three.nobs
