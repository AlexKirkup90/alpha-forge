"""Performance metrics computed on weekly return series."""
from __future__ import annotations

import math
from typing import Literal

import numpy as np
import pandas as pd


def align_series(a: pd.Series, b: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Align two series on the intersection of their indices and drop NaNs."""
    aligned = pd.concat([a, b], axis=1, join="inner").dropna()
    if aligned.empty:
        return a.iloc[0:0], b.iloc[0:0]
    return aligned.iloc[:, 0], aligned.iloc[:, 1]


def annualize_mean_std(
    returns: pd.Series, freq: Literal["weekly", "daily"] = "weekly"
) -> tuple[float, float]:
    """Annualize mean and standard deviation for weekly or daily frequency."""
    if returns.empty:
        return (np.nan, np.nan)
    scale_mean = 52 if freq == "weekly" else 252
    scale_std = math.sqrt(52) if freq == "weekly" else math.sqrt(252)
    mean_ann = float(returns.mean() * scale_mean)
    std_ann = float(returns.std(ddof=1) * scale_std)
    return mean_ann, std_ann


def sharpe(
    returns: pd.Series, risk_free: float = 0.0, freq: Literal["weekly", "daily"] = "weekly"
) -> float:
    """Compute the annualized Sharpe ratio."""
    if returns.empty:
        return np.nan
    excess = returns - risk_free
    std = excess.std(ddof=1)
    if std == 0:
        return np.inf if excess.mean() > 0 else 0.0
    scale = math.sqrt(52) if freq == "weekly" else math.sqrt(252)
    return float(excess.mean() / std * scale)


def sortino(
    returns: pd.Series, risk_free: float = 0.0, freq: Literal["weekly", "daily"] = "weekly"
) -> float:
    """Compute the annualized Sortino ratio."""
    if returns.empty:
        return np.nan
    excess = returns - risk_free
    downside = np.minimum(excess, 0.0)
    downside_std = downside.std(ddof=1)
    if downside_std == 0:
        return np.inf if excess.mean() > 0 else 0.0
    scale = math.sqrt(52) if freq == "weekly" else math.sqrt(252)
    return float(excess.mean() / downside_std * scale)


def alpha_beta(returns: pd.Series, benchmark: pd.Series) -> tuple[float, float]:
    """Estimate weekly alpha and beta via OLS."""
    r_strat, r_bench = align_series(returns, benchmark)
    if r_strat.empty:
        return (np.nan, np.nan)
    cov = float(r_strat.cov(r_bench, ddof=1))
    var = float(r_bench.var(ddof=1))
    if var == 0:
        return (np.nan, np.nan)
    beta = cov / var
    alpha = float(r_strat.mean() - beta * r_bench.mean())
    return alpha, beta


def deflated_sharpe(
    observed_sharpe: float, n: int, m: int, autocorr: float = 0.0
) -> float:
    """Approximate the Deflated Sharpe Ratio following López de Prado."""
    if m < 1 or n <= 1:
        return np.nan
    if not np.isfinite(observed_sharpe):
        return np.nan
    if abs(autocorr) >= 1:
        return np.nan
    n_eff = n * (1 - autocorr) / (1 + autocorr)
    if n_eff <= 1:
        return np.nan
    se = math.sqrt((1 + 0.5 * observed_sharpe**2) / (n_eff - 1))
    bias = 0.0
    if m > 1:
        bias = se * math.sqrt(2.0 * math.log(m))
    z = 0.0 if se == 0 else (observed_sharpe - bias) / se
    return float(0.5 * (1.0 + math.erf(z / math.sqrt(2.0))))
