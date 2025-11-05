import json
import os

import pytest

from src.engine.backtest_pd import run_backtest_pd, try_import_pandas


@pytest.mark.skipif(try_import_pandas() is None, reason="pandas not available")
def test_artifacts_and_serialization(tmp_path):
    dates = [f"2024-01-{d:02d}" for d in range(7, 35, 7)]
    prices = {d: {"AAA": 100 + i, "BBB": 80 - 0.2 * i, "CCC": 50 + 0.5 * i} for i, d in enumerate(dates)}
    eps = {d: {"AAA": 1.0 + 0.01 * i, "BBB": 0.9 - 0.002 * i, "CCC": 0.55 + 0.003 * i} for i, d in enumerate(dates)}
    funda = {
        "AAA": {"gpm": 0.6, "accruals": 0.1, "leverage": 0.2},
        "BBB": {"gpm": 0.4, "accruals": 0.2, "leverage": 0.35},
        "CCC": {"gpm": 0.55, "accruals": 0.12, "leverage": 0.25},
    }
    sector = {"AAA": "Tech", "BBB": "Finance", "CCC": "Tech"}
    out = run_backtest_pd(prices, eps, funda, sector, weeks=10, runs_dir=str(tmp_path))
    assert os.path.isdir(out)
    for fname in ("metrics.json", "returns.json", "equity.json", "weights.csv", "holdings_last.json"):
        assert os.path.isfile(os.path.join(out, fname))
    with open(os.path.join(out, "metrics.json"), "r", encoding="utf-8") as fh:
        metrics = json.load(fh)
    for key in ("Sharpe", "Sortino", "CAGR", "MaxDD", "Turnover_mean", "TerminalEquity"):
        assert key in metrics
