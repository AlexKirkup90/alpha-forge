"""Feature-level marginal PnL computations."""
from __future__ import annotations

from typing import Dict, Iterable, List

import numpy as np
import pandas as pd


def _to_returns_df(next_period_returns: pd.Series | pd.DataFrame) -> pd.DataFrame:
    if isinstance(next_period_returns, pd.DataFrame):
        return next_period_returns
    if next_period_returns.name is None:
        raise ValueError("next_period_returns Series must have a date index or name")
    return next_period_returns.to_frame().T


def compute_feature_marginals(
    weights_by_feature: Dict[str, pd.DataFrame],
    next_period_returns: pd.Series | pd.DataFrame,
) -> pd.DataFrame:
    """Compute marginal PnL contributions for each feature per date."""
    if not weights_by_feature:
        return pd.DataFrame(columns=["date", "feature", "delta_weight", "next_ret", "marginal_pnl"])

    returns_df = _to_returns_df(next_period_returns)

    common_index = returns_df.index
    common_columns = returns_df.columns
    for df in weights_by_feature.values():
        common_index = common_index.intersection(df.index)
        common_columns = common_columns.intersection(df.columns)

    if common_index.empty or len(common_columns) == 0:
        return pd.DataFrame(columns=["date", "feature", "delta_weight", "next_ret", "marginal_pnl"])

    rows: List[dict[str, object]] = []
    for feature, weights in weights_by_feature.items():
        aligned_weights = weights.reindex(index=common_index, columns=common_columns).fillna(0.0)
        for date in common_index:
            delta = aligned_weights.loc[date]
            rets = returns_df.loc[date, common_columns]
            pnl = float((delta * rets).sum())
            gross_exposure = float(delta.abs().sum())
            next_ret = float(pnl / gross_exposure) if gross_exposure > 0 else 0.0
            rows.append(
                {
                    "date": date,
                    "feature": feature,
                    "delta_weight": float(delta.sum()),
                    "next_ret": next_ret,
                    "marginal_pnl": pnl,
                }
            )

    result = pd.DataFrame(rows)
    if not result.empty:
        result.sort_values(["date", "feature"], inplace=True)
        result.reset_index(drop=True, inplace=True)
    return result
