from __future__ import annotations

from typing import Sequence


def compute_drawdown(equity: Sequence[float]) -> list[float]:
    dd: list[float] = []
    peak = float("-inf")
    for value in equity:
        x = float(value)
        peak = max(peak, x)
        dd.append(0.0 if peak <= 0 else (peak - x) / peak)
    return dd


def governor_signal(
    equity: Sequence[float],
    realized_vol: Sequence[float],
    dd_soft: float = 0.1,
    dd_hard: float = 0.2,
    vol_thresh: float = 0.25,
    up_hysteresis: float = 0.02,
    down_hysteresis: float = 0.02,
) -> list[float]:
    """
    Returns exposure in [0,1] per point. Reduce when drawdown > dd_soft or vol > vol_thresh,
    cut to ~0 at dd_hard; restore slowly with hysteresis.
    """
    dd = compute_drawdown(equity)
    out: list[float] = []
    exp = 1.0
    for d, vol in zip(dd, realized_vol):
        if d >= dd_hard:
            exp = 0.1
        elif d >= dd_soft or vol >= vol_thresh:
            exp = max(0.3, exp - down_hysteresis)
        else:
            exp = min(1.0, exp + up_hysteresis)
        out.append(exp)
    return out


def apply_governor(weights_series: Sequence[float], signal: Sequence[float]) -> list[float]:
    return [float(w) * float(s) for w, s in zip(weights_series, signal)]
