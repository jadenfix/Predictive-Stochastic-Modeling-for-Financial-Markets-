import numpy as np
import pandas as pd
import pytest

import thesis as T

# Peak at 3 (130), trough at 7 (90): a 30.8% fall, then a 33% rise.
PATH = np.array([100, 110, 120, 130, 120, 110, 100, 90, 100, 110, 120, 125.0])


def test_bear_runs_from_month_after_peak_to_trough():
    d = T.date_bear_markets(PATH)
    assert d.labels.tolist() == [0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0]
    # 130 * 0.8 = 104 is first breached at index 6; 90 * 1.2 = 108 first reached at index 9.
    assert [(tp.kind, tp.index, tp.confirmed_at) for tp in d.turning_points] == [("peak", 3, 6), ("trough", 7, 9)]


def test_realtime_state_switches_only_when_threshold_is_crossed():
    assert T.date_bear_markets(PATH).realtime_state.tolist() == [0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0]


def test_decline_below_threshold_is_not_a_bear():
    assert T.date_bear_markets(np.array([100, 110, 95, 89.5, 100, 120.0])).labels.sum() == 0


def test_open_bear_is_labeled_through_the_end():
    assert T.date_bear_markets(np.array([100, 120, 110, 90, 85, 88.0])).labels.tolist() == [0, 0, 1, 1, 1, 1]


def test_realtime_state_is_causal():
    prices = 100 * np.exp(np.cumsum(np.random.default_rng(1).normal(0, 0.05, 400)))
    full = T.date_bear_markets(prices).realtime_state
    for t in (50, 150, 300):
        assert np.array_equal(T.date_bear_markets(prices[: t + 1]).realtime_state, full[: t + 1])


def test_vintage_labels_use_only_data_through_the_origin():
    """The engine dates the price history through each origin; earlier labels can be revised."""
    assert T.date_bear_markets(PATH[:6]).labels.sum() == 0  # by month 5 the fall is only 15%
    assert T.date_bear_markets(PATH[:7]).labels.tolist() == [0, 0, 0, 0, 1, 1, 1]


def test_episode_table():
    idx = pd.date_range("2000-01-01", periods=len(PATH), freq="MS")
    row = T.episodes(pd.Series(PATH, index=idx)).iloc[0]
    assert row.peak == idx[3] and row.trough == idx[7] and row.months == 4 and row.confirmed == idx[6]
    assert row.decline_pct == pytest.approx(100 * (90 / 130 - 1))


def test_invalid_inputs():
    with pytest.raises(ValueError):
        T.date_bear_markets(np.array([1.0, -2.0]))
    with pytest.raises(ValueError):
        T.date_bear_markets(np.array([1.0, 2.0]), decline=1.5)
