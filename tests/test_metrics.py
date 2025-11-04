import math

import numpy as np
import pandas as pd

from src.metrics.perf import (
    alpha_beta,
    annualize_mean_std,
    deflated_sharpe,
    sharpe,
    sortino,
)


def test_sharpe_matches_expected():
    rng = np.random.default_rng(42)
    base = 0.01
    noise = rng.normal(0.0, 0.02, size=260)
    returns = pd.Series(base + noise)
    sr = sharpe(returns)
    expected = base / 0.02 * math.sqrt(52)
    assert math.isclose(sr, expected, rel_tol=0.15)


def test_sortino_positive_only_infinite():
    returns = pd.Series(np.full(20, 0.01))
    result = sortino(returns)
    assert math.isinf(result)


def test_sortino_mixed_returns():
    returns = pd.Series([0.01, -0.02, 0.015, -0.01, 0.02])
    result = sortino(returns)
    assert result > 0


def test_alpha_beta_estimation():
    rng = np.random.default_rng(7)
    bench = pd.Series(rng.normal(0.0, 0.01, size=200))
    noise = pd.Series(rng.normal(0.0, 0.005, size=200))
    strat = 0.001 + 1.2 * bench + noise
    alpha, beta = alpha_beta(strat, bench)
    assert math.isclose(alpha, 0.001, abs_tol=5e-4)
    assert math.isclose(beta, 1.2, rel_tol=0.05)


def test_annualize_mean_std_constants():
    returns = pd.Series(np.full(52, 0.01))
    mean_ann, std_ann = annualize_mean_std(returns)
    assert math.isclose(mean_ann, 0.52, rel_tol=1e-6)
    assert math.isclose(std_ann, 0.0, abs_tol=1e-8)


def test_deflated_sharpe_monotonicity():
    sr = 1.0
    low_n = deflated_sharpe(sr, n=30, m=10)
    high_n = deflated_sharpe(sr, n=260, m=10)
    more_trials = deflated_sharpe(sr, n=30, m=100)
    assert high_n > low_n
    assert more_trials < low_n
