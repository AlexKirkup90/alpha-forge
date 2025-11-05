from __future__ import annotations

import numpy as np
import pandas as pd


def _z(x: pd.Series) -> pd.Series:
    mu = x.mean()
    sd = x.std(ddof=1)
    if not np.isfinite(sd) or sd == 0:
        return pd.Series(0.0, index=x.index)
    return (x - mu) / sd


def standardize_by_date(df: pd.DataFrame) -> pd.DataFrame:
    """Apply cross-sectional z-score per row (date)."""
    if df.empty:
        return df
    return df.apply(_z, axis=1)


# --- Factors ---


def factor_mom_12_1(px: pd.DataFrame) -> pd.DataFrame:
    """12-1 momentum (skip last week): px(t-1) / px(t-52) - 1 at each t."""
    r_12 = px.shift(1) / px.shift(52) - 1.0
    return standardize_by_date(r_12)


def factor_mom_velocity(px: pd.DataFrame) -> pd.DataFrame:
    """Slope of 12w normalized price window (OLS beta vs time index)."""
    w = 12

    def _slope(s: pd.Series) -> float:
        idx = np.arange(len(s))
        if len(s.dropna()) < 3:
            return np.nan
        x = idx - idx.mean()
        y = (s - s.mean()) / (s.std(ddof=1) or 1.0)
        denom = (x**2).sum()
        if denom == 0:
            return 0.0
        return float((x * y).sum() / denom)

    out = px.rolling(w).apply(lambda col: _slope(pd.Series(col)), raw=False)
    return standardize_by_date(out)


def factor_eps_revision_4_12(eps: pd.DataFrame) -> pd.DataFrame:
    """EPS revisions: (eps - eps.shift(4)) - (eps - eps.shift(12)) = eps.shift(12) - eps.shift(4)."""
    rev_short = eps - eps.shift(4)
    rev_long = eps - eps.shift(12)
    rev = rev_short - rev_long
    return standardize_by_date(rev)


def factor_quality_q(
    funda_latest: dict[str, dict[str, float]],
    px_index: pd.Index,
    columns: list[str],
) -> pd.DataFrame:
    """
    Cross-sectional quality score broadcast across time:
    q = gpm - 0.5*accruals - 0.5*leverage
    """

    base = {
        t: (
            vals.get("gpm", 0.0)
            - 0.5 * vals.get("accruals", 0.0)
            - 0.5 * vals.get("leverage", 0.0)
        )
        for t, vals in funda_latest.items()
    }
    row = pd.Series({c: float(base.get(c, 0.0)) for c in columns})
    df = pd.DataFrame([row] * len(px_index), index=px_index)
    return standardize_by_date(df)


def factor_low_vol_26w(px: pd.DataFrame) -> pd.DataFrame:
    """Low volatility over ~26 weeks (std of returns). Lower vol → higher score (negate std)."""
    r = px.pct_change()
    vol = r.rolling(26).std(ddof=1)
    score = -vol
    return standardize_by_date(score)


__all__ = [
    "factor_mom_12_1",
    "factor_mom_velocity",
    "factor_eps_revision_4_12",
    "factor_quality_q",
    "factor_low_vol_26w",
    "standardize_by_date",
]
