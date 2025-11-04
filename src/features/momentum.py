from __future__ import annotations

from typing import Mapping, Sequence


def price_momentum(
    prices: Mapping[str, Sequence[float]],
    lookbacks: list[int] | None = None,
) -> dict[str, dict[int, float]]:
    """
    prices: ticker -> sequence of weekly CLOSE prices (oldest...newest).
    Returns: ticker -> {lookback_weeks -> momentum_return (last/prev - 1)}.
    """
    if lookbacks is None:
        lookbacks = [13, 26, 52]
    out: dict[str, dict[int, float]] = {}
    for tkr, series in prices.items():
        n = len(series)
        res: dict[int, float] = {}
        if n < 3:
            out[tkr] = res
            continue
        last = float(series[-1])
        for lb in lookbacks:
            if lb < 0:
                continue
            if n - lb - 1 < 0:
                continue
            prev = float(series[-lb - 1])
            if prev != 0.0:
                res[lb] = last / prev - 1.0
        out[tkr] = res
    return out
