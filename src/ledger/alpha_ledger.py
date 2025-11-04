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
        Mapping from feature name -> date -> ticker -> delta weight attributable to that feature.
        Example:
            {
              "momentum": { "2024-01-05": {"AAPL": 0.01, "MSFT": -0.005}, ... },
              "revisions": { "2024-01-05": {"AAPL": 0.002, "MSFT": 0.001}, ... }
            }
    next_period_returns:
        Mapping from date -> ticker -> realized return for the subsequent period.
        Example:
            { "2024-01-05": {"AAPL": 0.012, "MSFT": -0.004}, ... }

    Returns
    -------
    list of dict:
        Rows of the form:
        {
          "date": <str>,
          "feature": <str>,
          "delta_weight": <float>,   # sum of feature-attributed delta weights (across common tickers)
          "next_ret": <float>,       # marginal return (pnl / gross_exposure) for this feature on that date
          "marginal_pnl": <float>    # sum_ticker( delta_weight[t] * next_ret[t] )
        }
    """

    # Fast exits
    if not weights_by_feature or not next_period_returns:
        return []

    # Dates common to returns and to every feature's weights
    common_dates = set(next_period_returns.keys())
    for feature_weights in weights_by_feature.values():
        common_dates &= set(feature_weights.keys())
    if not common_dates:
        return []

    sorted_dates = sorted(common_dates)

    # Determine tickers common across all features for the overlapping dates
    common_tickers: set[str] | None = None
    for feature_weights in weights_by_feature.values():
        for date in sorted_dates:
            tickers = set(feature_weights.get(date, {}).keys())
            if common_tickers is None:
                common_tickers = set(tickers)
            else:
                common_tickers &= tickers

    if not common_tickers:
        return []

    rows: list[dict[str, object]] = []
    for date in sorted_dates:
        date_returns = next_period_returns.get(date, {})
        for feature_name in sorted(weights_by_feature.keys()):
            weights_for_date = weights_by_feature[feature_name].get(date, {})
            pnl = 0.0
            gross_exposure = 0.0

            # Compute marginal pnl and gross exposure over common tickers
            for ticker in common_tickers:
                w = float(weights_for_date.get(ticker, 0.0))
                r = float(date_returns.get(ticker, 0.0))
                pnl += w * r
                gross_exposure += abs(w)

            next_ret = pnl / gross_exposure if gross_exposure > 0.0 else 0.0
            delta_weight_sum = float(sum(weights_for_date.get(t, 0.0) for t in common_tickers))

            rows.append(
                {
                    "date": date,
                    "feature": feature_name,
                    "delta_weight": delta_weight_sum,
                    "next_ret": next_ret,
                    "marginal_pnl": pnl,
                }
            )

    rows.sort(key=lambda row: (row["date"], row["feature"]))
    return rows