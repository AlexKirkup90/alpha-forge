from __future__ import annotations

from typing import Dict
import math


def _ema(prev: float | None, x: float, alpha: float) -> float:
    if prev is None:
        return x
    return alpha * x + (1 - alpha) * prev


def compute_ic_ema_series(
    ic_series_by_factor: Dict[str, Dict[str, float]],
    alpha: float = 0.2,
) -> Dict[str, Dict[str, float]]:
    """Return {date:{factor: ic_ema}} with dates sorted ascending."""

    dates = sorted({d for f in ic_series_by_factor.values() for d in f.keys()})
    out: Dict[str, Dict[str, float]] = {d: {} for d in dates}
    state: Dict[str, float | None] = {fname: None for fname in ic_series_by_factor.keys()}
    for d in dates:
        for fname, series in ic_series_by_factor.items():
            val = series.get(d)
            if val is None or not isinstance(val, (int, float)) or not math.isfinite(val):
                out[d][fname] = float(state[fname]) if state[fname] is not None else float("nan")
                continue
            state[fname] = _ema(state[fname], float(val), alpha)
            out[d][fname] = float(state[fname])
    return out


def clamp_and_normalize_weights(scores: Dict[str, float]) -> Dict[str, float]:
    """Clamp negatives to 0, normalize to sum=1 if positive mass; else all zeros."""

    nonneg = {
        k: (v if (isinstance(v, (int, float)) and v > 0 and math.isfinite(v)) else 0.0)
        for k, v in scores.items()
    }
    s = sum(nonneg.values())
    if s > 0:
        return {k: v / s for k, v in nonneg.items()}
    return {k: 0.0 for k in scores.keys()}


def apply_gates(weights: Dict[str, float], gates: Dict[str, int]) -> Dict[str, float]:
    """Zero out weights where gate == 0, keep others; does not renormalize."""

    return {k: (0.0 if int(gates.get(k, 1)) == 0 else float(v)) for k, v in weights.items()}
