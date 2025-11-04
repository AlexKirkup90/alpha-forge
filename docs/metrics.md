# Metrics Specification

**Periodicity**: weekly unless stated. Annualization uses √52. (Daily uses √252.)

- Excess return r_e = r - r_f. If r_f omitted, assume 0.
- Mean/Std are computed on aligned weekly series.

**Sharpe (weekly)**  
Sharpe = mean(r_e) / std(r_e) × √52

**Sortino (weekly)**  
Downside series d = min(r_e, 0).  
Downside deviation σ_down = std(d).  
Sortino = mean(r_e) / σ_down × √52  
(Note: if σ_down = 0 and mean(r_e) > 0, return +∞; if mean ≤ 0, return 0.)

**Alpha & Beta (weekly)**  
OLS on aligned weekly returns: r_strat = α + β · r_bench + ε  
Report α (per week) and β. If annualizing α, multiply by 52; keep units explicit.

**Deflated Sharpe Ratio (DSR)**  
Use López de Prado formulation. Inputs: observed Sharpe, sample size N, number of tried strategies M (model-selection correction), and return autocorrelation ρ (optional).

**Conventions**  
- Align observations by intersecting shared keys/index values (no forward-fill).  
- Plain Python sequences or mappings are acceptable inputs so long as ordering is deterministic.  
- Report units clearly (per-week vs annualized).
