import numpy as np
import pytest

from psm.metrics import auc, brier, calibration, clark_west, diebold_mariano, log_loss


def test_scores_on_known_values():
    y = np.array([0, 0, 1, 1])
    p = np.array([0.1, 0.4, 0.35, 0.8])
    assert brier(p, y) == pytest.approx(np.mean([0.01, 0.16, 0.4225, 0.04]))
    assert auc(p, y) == pytest.approx(0.75)
    assert log_loss(np.array([0.0, 1.0]), np.array([0, 1])) == pytest.approx(-np.log(0.999))


def test_auc_perfect_and_ties():
    assert auc(np.array([0.1, 0.2, 0.8, 0.9]), np.array([0, 0, 1, 1])) == 1.0
    assert auc(np.full(4, 0.5), np.array([0, 1, 0, 1])) == 0.5


def test_calibration_bins_cover_all_forecasts():
    rng = np.random.default_rng(0)
    p = rng.uniform(size=500)
    y = rng.uniform(size=500) < p
    cal = calibration(p, y, bins=5)
    assert cal["count"].sum() == 500 and len(cal) == 5


def test_tests_point_the_right_way():
    rng = np.random.default_rng(2)
    good, bad = rng.uniform(0, 0.1, 300), rng.uniform(0.2, 0.3, 300)
    assert diebold_mariano(good, bad, 1)[1] < 0.01
    actual = rng.normal(size=300)
    _, p = clark_west(actual, np.zeros(300), actual + rng.normal(0, 0.1, 300), 1)
    assert p < 0.01
