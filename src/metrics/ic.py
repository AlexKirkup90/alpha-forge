from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


def _safe_number(x: float) -> float | str:
    try:
        xf = float(x)
        if math.isfinite(xf):
            return xf
        return "Infinity" if math.isinf(xf) and xf > 0 else "-Infinity"
    except Exception:
        return "NaN"


def next_period_returns_from_prices(px: pd.DataFrame) -> pd.Series | pd.DataFrame:
    """Compute next-period return per date per ticker (align to t: ret_{t+1})."""
    rets = px.pct_change().shift(-1)
    return rets


def ic_series(scores: pd.DataFrame, next_returns: pd.DataFrame) -> pd.Series:
    """Cross-sectional Spearman IC per date (index intersection)."""
    idx = scores.index.intersection(next_returns.index)
    cols = scores.columns.intersection(next_returns.columns)
    if len(idx) == 0 or len(cols) == 0:
        return pd.Series(dtype=float)
    S = scores.reindex(index=idx, columns=cols)
    R = next_returns.reindex(index=idx, columns=cols)
    vals = []
    for d in idx:
        s = S.loc[d]
        r = R.loc[d]
        m = s.notna() & r.notna()
        if m.sum() < 2:
            vals.append(np.nan)
            continue
        rho, _ = spearmanr(s[m], r[m])
        vals.append(rho)
    return pd.Series(vals, index=idx, dtype=float)


def ic_summary(series: pd.Series) -> dict[str, float | str]:
    s = series.dropna()
    n = int(s.shape[0])
    if n == 0:
        return {"n": 0, "ic_mean": "NaN", "ic_std": "NaN", "ir": "NaN", "tstat": "NaN"}
    mu = float(s.mean())
    sd = float(s.std(ddof=1)) if n > 1 else float("nan")
    ir = float(mu / sd) if (sd and math.isfinite(sd) and sd != 0.0) else float("nan")
    t = float(mu / (sd / (n ** 0.5))) if (sd and math.isfinite(sd) and sd != 0.0) else float("nan")
    return {
        "n": n,
        "ic_mean": _safe_number(mu),
        "ic_std": _safe_number(sd),
        "ir": _safe_number(ir),
        "tstat": _safe_number(t),
    }


__all__ = ["next_period_returns_from_prices", "ic_series", "ic_summary"]
