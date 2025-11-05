# alpha-forge

**alpha-forge** is an autonomous alpha-research lab — a modular system for feature engineering, signal generation, backtesting, and explainable portfolio analytics.

## Features
- Modular data → features → signals → portfolio → backtest → telemetry flow.
- Streamlit UI with gross vs. net returns and explainability dashboard.
- Full CI with unit tests.

## Quickstart
```bash
SETUPTOOLS_ENABLE_FEATURES=legacy-editable pip install -e .[providers] --no-build-isolation --no-deps
streamlit run app/streamlit_app.py
```
