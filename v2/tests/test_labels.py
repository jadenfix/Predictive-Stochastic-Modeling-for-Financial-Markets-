import numpy as np
import pandas as pd
import pytest

from psm.labels import date_bear_markets, episodes, vintage_labels

# Peak at 3 (130), trough at 7 (90): a 30.8% fall, then a 33% rise.
PATH = np.array([100, 110, 120, 130, 120, 110, 100, 90, 100, 110, 120, 125.0])


def test_bear_runs_from_month_after_peak_to_trough():
    d = date_bear_markets(PATH)
    assert d.labels.tolist() == [0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0]
    kinds = [(tp.kind, tp.index, tp.confirmed_at) for tp in d.turning_points]
    # 130 * 0.8 = 104 is first breached at index 6; 90 * 1.2 = 108 first reached at index 9.
    assert kinds == [("peak", 3, 6), ("trough", 7, 9)]


def test_realtime_state_switches_only_when_threshold_is_crossed():
    d = date_bear_markets(PATH)
    assert d.realtime_state.tolist() == [0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0]


def test_decline_below_threshold_is_not_a_bear():
    path = np.array([100, 110, 95, 89.5, 100, 120.0])  # 18.6% decline from 110
    assert date_bear_markets(path).labels.sum() == 0


def test_open_bear_is_labeled_through_the_end():
    path = np.array([100, 120, 110, 90, 85, 88.0])
    assert date_bear_markets(path).labels.tolist() == [0, 0, 1, 1, 1, 1]


def test_realtime_state_is_causal():
    rng = np.random.default_rng(1)
    prices = 100 * np.exp(np.cumsum(rng.normal(0, 0.05, 400)))
    full = date_bear_markets(prices).realtime_state
    for t in (50, 150, 300):
        assert np.array_equal(date_bear_markets(prices[: t + 1]).realtime_state, full[: t + 1])


def test_vintage_labels_use_only_data_through_asof():
    idx = pd.date_range("2000-01-01", periods=len(PATH), freq="MS")
    prices = pd.Series(PATH, index=idx)
    v = vintage_labels(prices, idx[5])
    # By month 5 the fall is only 15%, so no bear has been dated yet.
    assert v.index[-1] == idx[5] and v.sum() == 0
    assert vintage_labels(prices, idx[6]).tolist() == [0, 0, 0, 0, 1, 1, 1]


def test_episode_table():
    idx = pd.date_range("2000-01-01", periods=len(PATH), freq="MS")
    ep = episodes(pd.Series(PATH, index=idx))
    assert len(ep) == 1
    row = ep.iloc[0]
    assert row.peak == idx[3] and row.trough == idx[7] and row.months == 4
    assert row.decline_pct == pytest.approx(100 * (90 / 130 - 1))


def test_invalid_inputs():
    with pytest.raises(ValueError):
        date_bear_markets(np.array([1.0, -2.0]))
    with pytest.raises(ValueError):
        date_bear_markets(np.array([1.0, 2.0]), decline=1.5)
