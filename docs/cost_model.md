# Cost Model v2

**Goal**: realistic netting of spread + impact under participation caps.

Definitions (per trade):
- Participation p = |shares_traded| / ADV
- Cap p at p_max (default 0.10 = 10%)
- Spread cost C_spread (in return units) = (spread_bps / 1e4) * p
- Impact C_imp = k * σ * sqrt(p)
  - σ = recent daily volatility (e.g., 20d std of daily returns)
  - k in [0.5, 1.0] configurable
- Fees/taxes optional: C_fees = fee_bps/1e4 * p

Total cost C = C_spread + C_imp + C_fees  
Apply per-name per-rebalance, convert to portfolio return impact by weight/turnover attribution.

**Execution guards**
- Flag if p > p_max (violation).
- Enforce min trade size threshold to avoid dust churn.
- Log per-trade cost components for diagnostics.
