"""Feature-level marginal PnL computations using plain Python structures."""
from __future__ import annotations

from typing import Mapping


def compute_feature_marginals(
    weights_by_feature: Mapping[str, Mapping[str, Mapping[str, float]]],
    next_period_returns: Mapping[str, Mapping[str, float]],
) -> list[dict[str, object]]:
    """Compute marginal PnL contributions for each feature per date.

    Parameters
    ----------
    weights_by_feature:
        Mapping from feature name to date->ticker weight adjustments.
    next_period_returns:
        Mapping from date to ticker returns for the subsequent period.
    """

    if not weights_by_feature or not next_period_returns:
        return []

    common_dates = set(next_period_returns.keys())
    for weights in weights_by_feature.values():
        common_dates &= set(weights.keys())
    if not common_dates:
        return []

    sorted_dates = sorted(common_dates)

    # Determine common tickers across all features for the overlapping dates.
    common_tickers: set[str] | None = None
    for feature in weights_by_feature.values():
        for date in sorted_dates:
            tickers = set(feature.get(date, {}).keys())
            if common_tickers is None:
                common_tickers = set(tickers)
            else:
                common_tickers &= tickers
    if not common_tickers:
        return []

    results: list[dict[str, object]] = []
    for date in sorted_dates:
        date_returns = next_period_returns.get(date, {})
        for feature_name, feature_weights in sorted(weights_by_feature.items()):
            weights_for_date = feature_weights.get(date, {})
            pnl = 0.0
            gross = 0.0
            for ticker in common_tickers:
                weight = float(weights_for_date.get(ticker, 0.0))
                ret = float(date_returns.get(ticker, 0.0))
                pnl += weight * ret
                gross += abs(weight)
            next_ret = pnl / gross if gross > 0 else 0.0
            results.append(
                {
                    "date": date,
                    "feature": feature_name,
                    "delta_weight": sum(weights_for_date.get(t, 0.0) for t in common_tickers),
                    "next_ret": next_ret,
                    "marginal_pnl": pnl,
                }
            )

    results.sort(key=lambda row: (row["date"], row["feature"]))
    return results
