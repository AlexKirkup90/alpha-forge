from __future__ import annotations

from typing import Mapping


def cross_sectional_ic(factor: Mapping[str, float], next_ret: Mapping[str, float]) -> float:
    keys = list(set(factor) & set(next_ret))
    if len(keys) < 2:
        return 0.0
    x = [float(factor[k]) for k in keys]
    y = [float(next_ret[k]) for k in keys]
    mx = sum(x) / len(x)
    my = sum(y) / len(y)
    sx = (sum((v - mx) ** 2 for v in x) / (len(x) - 1)) ** 0.5
    sy = (sum((v - my) ** 2 for v in y) / (len(y) - 1)) ** 0.5
    if sx == 0 or sy == 0:
        return 0.0
    cov = sum((a - mx) * (b - my) for a, b in zip(x, y)) / (len(x) - 1)
    return cov / (sx * sy)


def hit_rate(pred_sign: Mapping[str, float], realized: Mapping[str, float]) -> float:
    keys = list(set(pred_sign) & set(realized))
    if not keys:
        return 0.0
    hits = sum(1 for k in keys if float(pred_sign[k]) * float(realized[k]) > 0)
    return hits / len(keys)


def quintile_spread(
    factor: Mapping[str, float],
    next_ret: Mapping[str, float],
    q: int = 5,
) -> float:
    keys = list(set(factor) & set(next_ret))
    if len(keys) < q or q <= 1:
        return 0.0
    keys.sort(key=lambda k: factor[k])
    n = len(keys)
    bucket = n // q
    if bucket == 0:
        return 0.0
    low = keys[:bucket]
    high = keys[-bucket:]
    r_low = sum(float(next_ret[k]) for k in low) / len(low)
    r_high = sum(float(next_ret[k]) for k in high) / len(high)
    return float(r_high - r_low)


def breadth(weights: Mapping[str, float]) -> float:
    return float(sum(1 for v in weights.values() if abs(float(v)) > 0))


def hhi(weights: Mapping[str, float]) -> float:
    total = sum(abs(float(v)) for v in weights.values()) or 1.0
    return float(sum((abs(float(v)) / total) ** 2 for v in weights.values()))
