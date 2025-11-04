"""Transaction cost estimation utilities without external dependencies."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping


@dataclass
class CostRow:
    """Per-date summary of transaction costs."""

    date: str
    C_spread: float
    C_impact: float
    C_fees: float

    @property
    def C_total(self) -> float:
        return self.C_spread + self.C_impact + self.C_fees


def estimate_costs(
    trades: Mapping[str, Mapping[str, float]],
    adv: Mapping[str, float],
    spreads_bps: Mapping[str, float],
    sigma_daily: Mapping[str, float],
    params: Mapping[str, float] | None = None,
) -> tuple[list[CostRow], dict[str, dict[str, float]]]:
    """Estimate per-date trading costs with spread, impact, and fees.

    Returns a tuple of (cost_rows, diagnostics) where diagnostics contains
    participation levels and violation counts keyed by date.
    """

    if not trades:
        return [], {"participation": {}, "violations": {}}

    defaults = {"p_max": 0.10, "k": 0.7, "fee_bps": 0.0}
    cfg = {**defaults, **(params or {})}
    fee_rate = cfg.get("fee_bps", 0.0) / 1e4

    cost_rows: list[CostRow] = []
    participation_summary: dict[str, dict[str, float]] = {}
    violations_summary: dict[str, int] = {}

    for date, trade_row in trades.items():
        c_spread_total = 0.0
        c_impact_total = 0.0
        c_fees_total = 0.0
        participation_row: dict[str, float] = {}
        violations = 0

        for ticker, shares in trade_row.items():
            adv_value = float(adv.get(ticker, 0.0))
            participation_raw = abs(shares)
            if adv_value > 0:
                participation_raw = abs(shares) / adv_value
            else:
                participation_raw = 0.0
            if participation_raw > cfg["p_max"] + 1e-12:
                violations += 1
            participation_capped = min(participation_raw, cfg["p_max"])
            participation_row[ticker] = participation_capped

            spread_bps = float(spreads_bps.get(ticker, 0.0))
            sigma = float(sigma_daily.get(ticker, 0.0))
            c_spread_total += participation_capped * (spread_bps / 1e4)
            c_impact_total += sigma * cfg["k"] * math.sqrt(participation_capped)
            c_fees_total += participation_capped * fee_rate

        cost_rows.append(
            CostRow(
                date=date,
                C_spread=c_spread_total,
                C_impact=c_impact_total,
                C_fees=c_fees_total,
            )
        )
        participation_summary[date] = participation_row
        violations_summary[date] = violations

    diagnostics = {"participation": participation_summary, "violations": violations_summary}
    return cost_rows, diagnostics
