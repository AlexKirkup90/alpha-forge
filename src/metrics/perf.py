"""Performance metrics computed on weekly return series without external deps."""
from __future__ import annotations

import math
from typing import Mapping, Sequence, TypeVar

T = TypeVar("T")


def _is_finite(value: float) -> bool:
    return math.isfinite(value)


def _to_series(data: Sequence[float] | Mapping[T, float]) -> tuple[list[T], list[float]]:
    """Convert a sequence or mapping to aligned (keys, values) lists.

    - For mappings, preserves the mapping's iteration order (assumed deterministic).
    - For sequences, keys are 0..n-1.
    """
    if isinstance(data, Mapping):
        keys = list(data.keys())
        values = [float(v) for v in data.values()]
        return keys, values
    keys_generic: list[T] = list(range(len(data)))  # type: ignore[arg-type]
    values = [float(v) for v in data]
    return keys_generic, values


def _mean(values: Sequence[float]) -> float:
    finite = [v for v in values if _is_finite(v)]
    if not finite:
        return math.nan
    return sum(finite) / len(finite)


def _std(values: Sequence[float]) -> float:
    """Sample standard deviation (ddof=1). Returns 0.0 for <2 finite obs."""
    finite = [v for v in values if _is_finite(v)]
    if len(finite) < 2:
        return 0.0
    mu = sum(finite) / len(finite)
    var = sum((v - mu) ** 2 for v in finite) / (len(finite) - 1)
    return math.sqrt(var)


def align_series(
    a: Sequence[float] | Mapping[T, float],
    b: Sequence[float] | Mapping[T, float],
) -> tuple[list[float], list[float]]:
    """Align two return collections by shared keys while dropping non-finite values.

    - If inputs are sequences, aligns by positional index.
    - If inputs are mappings, aligns by intersecting keys.
    - Non-finite values are dropped.
    """
    keys_a, values_a = _to_series(a)
    keys_b, values_b = _to_series(b)
    lookup_b = {key: value for key, value in zip(keys_b, values_b)}
    aligned_a: list[float] = []
    aligned_b: list[float] = []
    for key, value_a in zip(keys_a, values_a):
        if key not in lookup_b:
            continue
        value_b = lookup_b[key]
        if not (_is_finite(value_a) and _is_finite(value_b)):
            continue
        aligned_a.append(float(value_a))
        aligned_b.append(float(value_b))
    return aligned_a, aligned_b


def annualize_mean_std(
    returns: Sequence[float] | Mapping[T, float],
    freq: str = "weekly",
) -> tuple[float, float]:
    """Annualize mean and standard deviation for a returns collection."""
    _, values = _to_series(returns)
    if not values:
        return (math.nan, math.nan)
    scale_mean = 52 if freq == "weekly" else 252
    scale_std = math.sqrt(52) if freq == "weekly" else math.sqrt(252)
    mean_ann = _mean(values)
    std = _std(values)
    if math.isnan(mean_ann):
        return (math.nan, math.nan)
    return (mean_ann * scale_mean, std * scale_std)


def sharpe(
    returns: Sequence[float] | Mapping[T, float],
    risk_free: float = 0.0,
    freq: str = "weekly",
) -> float:
    """Compute the annualized Sharpe ratio."""
    _, values = _to_series(returns)
    if not values:
        return math.nan
    excess = [v - risk_free for v in values if _is_finite(v)]
    if not excess:
        return math.nan
    std = _std(excess)
    if std == 0:
        return math.inf if _mean(excess) > 0 else 0.0
    scale = math.sqrt(52) if freq == "weekly" else math.sqrt(252)
    return _mean(excess) / std * scale


def sortino(
    returns: Sequence[float] | Mapping[T, float],
    risk_free: float = 0.0,
    freq: str = "weekly",
) -> float:
    """Compute the annualized Sortino ratio."""
    _, values = _to_series(returns)
    if not values:
        return math.nan
    excess = [v - risk_free for v in values if _is_finite(v)]
    if not excess:
        return math.nan
    downside = [min(v, 0.0) for v in excess]
    downside_std = _std(downside)
    if downside_std == 0:
        return math.inf if _mean(excess) > 0 else 0.0
    scale = math.sqrt(52) if freq == "weekly" else math.sqrt(252)
    return _mean(excess) / downside_std * scale


def alpha_beta(
    returns: Sequence[float] | Mapping[T, float],
    benchmark: Sequence[float] | Mapping[T, float],
) -> tuple[float, float]:
    """Estimate weekly alpha and beta via simple OLS (closed-form)."""
    aligned_returns, aligned_bench = align_series(returns, benchmark)
    n = len(aligned_returns)
    if n < 2:
        return (math.nan, math.nan)
    mean_r = _mean(aligned_returns)
    mean_b = _mean(aligned_bench)
    cov = sum((r - mean_r) * (b - mean_b) for r, b in zip(aligned_returns, aligned_bench)) / (n - 1)
    var_b = sum((b - mean_b) ** 2 for b in aligned_bench) / (n - 1)
    if var_b == 0:
        return (math.nan, math.nan)
    beta = cov / var_b
    alpha = mean_r - beta * mean_b
    return (alpha, beta)


def deflated_sharpe(
    observed_sharpe: float,
    n: int,
    m: int,
    autocorr: float = 0.0,
) -> float:
    """Approximate the Deflated Sharpe Ratio following López de Prado.

    Parameters
    ----------
    observed_sharpe : observed annualized Sharpe ratio
    n : sample size (number of period returns)
    m : number of strategies tried (model selection correction)
    autocorr : lag-1 autocorrelation of returns (approx), range (-1,1)

    Returns
    -------
    float : probability-like score in [0,1] increasing with robustness.
    """
    if m < 1 or n <= 1:
        return math.nan
    if not math.isfinite(observed_sharpe):
        return math.nan
    if abs(autocorr) >= 1:
        return math.nan

    # Effective sample size with simple AR(1) correction
    n_eff = n * (1 - autocorr) / (1 + autocorr)
    if n_eff <= 1:
        return math.nan

    # Standard error of Sharpe under normal iid (approximate)
    se = math.sqrt((1 + 0.5 * observed_sharpe**2) / (n_eff - 1))

    # Multiple testing bias term
    bias = 0.0
    if m > 1:
        bias = se * math.sqrt(2.0 * math.log(m))

    # Z-score and CDF
    z = 0.0 if se == 0 else (observed_sharpe - bias) / se
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))