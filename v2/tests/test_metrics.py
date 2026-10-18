"""Scoring rules and tests of predictive ability on known and synthetic cases."""

import numpy as np
import pytest

import thesis as T


def test_scores_on_known_values():
    y = np.array([0, 0, 1, 1])
    p = np.array([0.1, 0.4, 0.35, 0.8])
    assert T.brier(p, y) == pytest.approx(np.mean([0.01, 0.16, 0.4225, 0.04]))
    assert T.auc(p, y) == pytest.approx(0.75)
    assert T.log_loss(np.array([0.0, 1.0]), np.array([0, 1])) == pytest.approx(-np.log(0.999))
    assert T.auc(np.full(4, 0.5), np.array([0, 1, 0, 1])) == 0.5


def test_calibration_bins_cover_all_forecasts():
    rng = np.random.default_rng(0)
    p = rng.uniform(size=500)
    cal = T.calibration(p, rng.uniform(size=500) < p, bins=5)
    assert cal["count"].sum() == 500 and len(cal) == 5


def test_murphy_decomposition_is_exact_for_binned_forecasts():
    rng = np.random.default_rng(1)
    p = rng.choice([0.05, 0.25, 0.55, 0.85], size=2000)  # one forecast value per bin
    y = (rng.uniform(size=2000) < p).astype(float)
    m = T.murphy_decomposition(p, y)
    assert m["remainder"] == pytest.approx(0, abs=1e-12)
    assert m["brier"] == pytest.approx(m["reliability"] - m["resolution"] + m["uncertainty"])
    climatology = T.murphy_decomposition(np.full(2000, y.mean()), y)
    assert climatology["resolution"] == pytest.approx(0) and climatology["reliability"] == pytest.approx(0)


def test_dm_and_cw_point_the_right_way():
    rng = np.random.default_rng(2)
    assert T.diebold_mariano(rng.uniform(0, 0.1, 300), rng.uniform(0.2, 0.3, 300), 1)[1] < 0.01
    actual = rng.normal(size=300)
    assert T.clark_west(actual, np.zeros(300), actual + rng.normal(0, 0.1, 300), 1)[1] < 0.01


def test_giacomini_white_size_and_power():
    rng = np.random.default_rng(3)
    n = 600
    state = (rng.uniform(size=n) < 0.3).astype(float)
    z = np.column_stack([np.ones(n), state])
    null = rng.normal(0, 1, n)
    assert T.giacomini_white(null, z, 0)[1] > 0.01
    # Same unconditional mean of zero, but the model is better in one state and worse in the other.
    alt = rng.normal(0, 1, n) + np.where(state == 1, -0.7, 0.3)
    stat, p = T.giacomini_white(alt - alt.mean(), z, 0)
    assert p < 0.001


def test_model_confidence_set_on_synthetic_losses():
    rng = np.random.default_rng(4)
    n = 600
    base = rng.normal(1.0, 0.3, n)
    losses = np.column_stack([base, base + rng.normal(0, 0.05, n), base + 0.3 + rng.normal(0, 0.05, n),
                              base + 0.6 + rng.normal(0, 0.05, n)])
    idx = T.block_indices(n, 10, 500, np.random.default_rng(5))
    p = T.model_confidence_set(losses, idx)
    assert p[0] >= 0.10 and p[1] >= 0.10  # the two equivalent best models stay in the set
    assert p[2] < 0.05 and p[3] < 0.05  # clearly worse models are eliminated
    assert p.max() == 1.0


def test_spa_rejects_only_when_a_model_beats_the_benchmark():
    rng = np.random.default_rng(6)
    n = 500
    idx = T.block_indices(n, 10, 1000, np.random.default_rng(7))
    worse = -0.2 + rng.normal(0, 1, (n, 5))  # benchmark loss minus model loss: all models worse
    assert T.spa_test(worse, idx)["p_consistent"] > 0.5
    better = worse.copy()
    better[:, 2] += 0.5  # one model now beats the benchmark
    out = T.spa_test(better, idx)
    assert out["p_consistent"] < 0.01 and out["best"] == 2
    assert out["p_lower"] <= out["p_consistent"] <= out["p_upper"]


def test_block_indices_are_contiguous_circular_blocks():
    idx = T.block_indices(50, 7, 20, np.random.default_rng(0))
    assert idx.shape == (20, 50) and idx.min() >= 0 and idx.max() < 50
    assert ((idx[:, 1:7] - idx[:, :6]) % 50 == 1).all()
