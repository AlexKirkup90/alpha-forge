from __future__ import annotations

from typing import Mapping


def quality_composite(
    gross_profit_margin: Mapping[str, float],
    accruals: Mapping[str, float],
    leverage: Mapping[str, float],
    weights: tuple[float, float, float] = (0.5, -0.25, -0.25),
) -> dict[str, float]:
    """
    Simple quality proxy: higher GPM better (+), lower accruals better (-), lower leverage better (-).
    weights sum to ~1 in spirit (not required). Output is an unscaled score.
    """
    w_gpm, w_acc, w_lev = weights
    out: dict[str, float] = {}
    tickers = set(gross_profit_margin) | set(accruals) | set(leverage)
    for t in tickers:
        g = float(gross_profit_margin.get(t, 0.0))
        a = float(accruals.get(t, 0.0))
        lv = float(leverage.get(t, 0.0))
        out[t] = w_gpm * g + w_acc * a + w_lev * lv
    return out
