from __future__ import annotations

import pandas as pd
from src.data.snapshot import load_snapshot, list_snapshots
from src.factors.library import (
    factor_mom_12_1,
    factor_mom_velocity,
    factor_eps_revision_4_12,
    factor_quality_q,
    factor_low_vol_26w,
)
from src.portfolio.constraints import cap_by_name, cap_by_sector
from src.signals.orthogonalize import sector_zscore


def _rank(scores: dict[str, float]) -> dict[str, float]:
    items = [(ticker, float(value)) for ticker, value in scores.items()]
    if not items:
        return {}
    items.sort(key=lambda kv: kv[1])  # ascending
    n = len(items)
    return {ticker: (idx + 1) / n for idx, (ticker, _) in enumerate(items)}


def _select_top_k(scores: dict[str, float], k: int) -> dict[str, float]:
    k = max(1, int(k))
    items = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:k]
    if not items:
        return {}
    weight = 1.0 / len(items)
    return {ticker: weight for ticker, _ in items}


def generate_portfolio(
    best_factors: list[str],
    top_k: int = 20,
    name_cap: float = 0.07,
    sector_cap: float = 0.30,
) -> pd.DataFrame:
    """
    Generates a diversified portfolio based on a list of best-performing factors.

    Parameters
    ----------
    best_factors
        A list of factor names to use for portfolio construction.
    top_k
        The number of assets to include in the portfolio.
    name_cap
        The maximum weight for any single asset.
    sector_cap
        The maximum weight for any single sector.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the portfolio holdings, weights, and rationale.
    """
    # 1. Load the most recent data snapshot
    snapshots = list_snapshots()
    if not snapshots:
        raise FileNotFoundError("No data snapshots found. Please build a snapshot first.")
    latest_snapshot = snapshots[0]
    prices_by_date, eps_by_date, fundamentals_latest, sector_map = load_snapshot(
        latest_snapshot
    )
    px = pd.DataFrame.from_dict(prices_by_date, orient="index").sort_index()
    eps = pd.DataFrame.from_dict(eps_by_date, orient="index").sort_index()

    # 2. Calculate all available factor scores
    factor_data = {
        "mom_12_1": factor_mom_12_1(px),
        "mom_velocity": factor_mom_velocity(px),
        "eps_rev_4_12": factor_eps_revision_4_12(eps),
        "quality_q": factor_quality_q(
            fundamentals_latest, px.index, list(px.columns)
        ),
        "low_vol_26w": factor_low_vol_26w(px),
    }

    # 3. Combine the scores of the best-performing factors
    latest_scores = pd.DataFrame(
        {
            factor: data.iloc[-1]
            for factor, data in factor_data.items()
            if factor in best_factors
        }
    )
    composite_score = latest_scores.mean(axis=1)

    # 4. Construct the portfolio
    score_dict = composite_score.to_dict()
    neutral_score = sector_zscore(score_dict, sector_map)
    ranked_score = _rank(neutral_score)
    preliminary_weights = _select_top_k(ranked_score, top_k)
    capped_weights = cap_by_name(preliminary_weights, name_cap)
    final_weights = cap_by_sector(capped_weights, sector_map, sector_cap)

    # 5. Format the output
    rationale = f"Selected based on high scores from factors: {', '.join(best_factors)}"
    portfolio_df = pd.DataFrame.from_dict(final_weights, orient="index", columns=["Weight"])
    portfolio_df["Rationale"] = rationale
    portfolio_df = portfolio_df.reset_index().rename(columns={"index": "Ticker"})

    return portfolio_df
