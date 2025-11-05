from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd


def rolling_vol(series: pd.Series, window: int = 13) -> pd.Series:
    return series.rolling(window).std(ddof=1)


def trend_signal(series: pd.Series, window: int = 26) -> pd.Series:
    ma = series.rolling(window).mean()
    return (series > ma).astype(int)


def make_regime_gates(
    benchmark_weekly_returns: Dict[str, float] | None,
    factor_names: List[str],
    high_vol_threshold: float = 0.03,
    vol_window: int = 13,
    trend_window: int = 26,
    gate_map: Dict[str, Dict[str, int]] | None = None,
) -> Dict[str, Dict[str, int]]:
    """Return {date:{factor:0/1}} with simple defensive rules."""

    if not benchmark_weekly_returns:
        return {}

    idx = pd.Index(sorted(benchmark_weekly_returns.keys()))
    r = pd.Series([float(benchmark_weekly_returns[d]) for d in idx], index=idx)
    eq = (1 + r).cumprod()
    vol = rolling_vol(r, window=vol_window).reindex(idx)
    up = trend_signal(eq, window=trend_window).reindex(idx)

    out: Dict[str, Dict[str, int]] = {}
    for d in idx:
        is_high_vol = bool(vol.get(d, np.nan) > high_vol_threshold)
        is_up = bool(up.get(d, 1) == 1)

        row: Dict[str, int] = {}
        for f in factor_names:
            base = 1
            if is_high_vol and f not in ("low_vol_26w", "quality_q"):
                base = 0
            if not is_up and f.startswith("mom"):
                base = 0
            row[f] = base

        if gate_map and d in gate_map:
            for k, v in gate_map[d].items():
                row[k] = int(v)
        out[str(d)] = row
    return out
