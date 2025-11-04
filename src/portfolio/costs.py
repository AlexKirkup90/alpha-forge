"""Transaction cost estimation utilities."""
from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd


def _safe_divide(numerator: pd.DataFrame, denominator: pd.Series) -> pd.DataFrame:
    denom = denominator.replace(0, np.nan)
    result = numerator.divide(denom, axis=1)
    return result.fillna(0.0)


def estimate_costs(
    trades_df: pd.DataFrame,
    adv: pd.Series,
    spreads_bps: pd.Series,
    sigma_daily: pd.Series,
    params: Dict[str, float],
) -> pd.DataFrame:
    """Estimate per-date trading costs with spread, impact, and fees."""
    if trades_df.empty:
        result = pd.DataFrame(columns=["C_spread", "C_impact", "C_fees", "C_total"])
        result.attrs["violations"] = pd.Series(dtype=int)
        result.attrs["participation"] = trades_df
        return result

    defaults = {"p_max": 0.10, "k": 0.7, "fee_bps": 0.0}
    cfg = {**defaults, **(params or {})}

    cols = trades_df.columns
    adv_aligned = adv.reindex(cols)
    spreads_aligned = spreads_bps.reindex(cols).fillna(0.0)
    sigma_aligned = sigma_daily.reindex(cols).fillna(0.0)

    participation_raw = _safe_divide(trades_df.abs(), adv_aligned)
    violations = participation_raw > cfg["p_max"]
    participation = participation_raw.clip(upper=cfg["p_max"])

    c_spread = participation * (spreads_aligned / 1e4)
    c_impact = np.sqrt(participation) * (sigma_aligned * cfg["k"])
    fee_rate = cfg.get("fee_bps", 0.0) / 1e4
    c_fees = participation * fee_rate

    costs = pd.DataFrame(
        {
            "C_spread": c_spread.sum(axis=1),
            "C_impact": c_impact.sum(axis=1),
            "C_fees": c_fees.sum(axis=1),
        }
    )
    costs["C_total"] = costs.sum(axis=1)

    costs.attrs["violations"] = violations.sum(axis=1)
    costs.attrs["participation"] = participation

    return costs
