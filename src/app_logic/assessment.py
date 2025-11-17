from __future__ import annotations

import pandas as pd
from src.data.snapshot import load_snapshot, list_snapshots
from src.engine.factor_telemetry import run_factor_ic_telemetry
from src.engine.load_ic_artifacts import load_latest_ic_series


def assess_market_conditions() -> dict:
    """
    Analyzes the most recent data snapshot to determine the best-performing
    alpha factors based on their Information Coefficient (IC) over the last 90 days.

    Returns
    -------
    dict
        A dictionary containing the best-performing factors and a summary.
    """
    # 1. Load the most recent data snapshot
    snapshots = list_snapshots()
    if not snapshots:
        raise FileNotFoundError("No data snapshots found. Please build a snapshot first.")
    latest_snapshot = snapshots[0]
    prices_by_date, eps_by_date, fundamentals_latest, _ = load_snapshot(latest_snapshot)

    # 2. Run factor IC telemetry
    available_factors = [
        "mom_12_1",
        "mom_velocity",
        "eps_rev_4_12",
        "quality_q",
        "low_vol_26w",
    ]
    run_factor_ic_telemetry(
        prices_by_date=prices_by_date,
        eps_by_date=eps_by_date,
        fundamentals_latest=fundamentals_latest,
        factor_names=available_factors,
        data_snapshot_id=latest_snapshot.split("/")[-1],
    )

    # 3. Load the results and identify the best factors
    ic_by_factor = load_latest_ic_series(factor_names=available_factors)
    if not ic_by_factor:
        raise RuntimeError("Could not load IC series from the telemetry run.")

    ic_means = {
        factor: pd.Series(ic_data).mean()
        for factor, ic_data in ic_by_factor.items()
    }

    # Select factors with positive IC, sorted by performance
    best_factors = sorted(
        [factor for factor, mean_ic in ic_means.items() if mean_ic > 0],
        key=lambda factor: ic_means[factor],
        reverse=True,
    )

    # 4. Formulate the summary
    summary = (
        f"Based on market performance over the last 90 days, the following factors "
        f"are showing the strongest predictive power: {', '.join(best_factors)}. "
        f"The portfolio will be tilted towards these factors."
    )

    return {
        "best_factors": best_factors,
        "summary": summary,
    }
