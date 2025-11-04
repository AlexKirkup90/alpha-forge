# alpha-forge
An autonomous alpha research lab: fetch → features → signals → portfolio → walk-forward → telemetry → explain.

## Why
Maximize real (net) alpha, minimize drawdown, and prove where returns come from.

## What’s inside
- Truth layer: correct Sharpe/Sortino/alpha, realistic cost model.
- Alpha Ledger: marginal PnL by feature with decay & IC.
- Orthogonalization: sector z + optional PCA.
- Construction: linear ranks + ERC/HRP overlays, vol targeting, constraints.
- Governance: purging/embargo, anchored OOS, DSR, PBO.
- Streamlit app: Gross vs Net, Run Registry, Sources of Return.

## Quickstart
```bash
pip install -e .
streamlit run app/streamlit_app.py
