import pytest

from src.engine.backtest_pd import run_backtest_pd, try_import_pandas


@pytest.mark.skipif(try_import_pandas() is None, reason="pandas not available")
def test_backtest_pd_runs(tmp_path, monkeypatch):
    # small synthetic dataset
    dates = [f"2024-01-{d:02d}" for d in range(1, 30, 2)]
    prices = {d: {"A": 100 + i, "B": 50 + 0.5 * i, "C": 30 + 0.2 * i} for i, d in enumerate(dates)}
    eps = {d: {"A": 1.0 + 0.01 * i, "B": 0.8 - 0.005 * i, "C": 0.5 + 0.002 * i} for i, d in enumerate(dates)}
    funda = {
        "A": {"gpm": 0.6, "accruals": 0.1, "leverage": 0.2},
        "B": {"gpm": 0.4, "accruals": 0.2, "leverage": 0.3},
        "C": {"gpm": 0.55, "accruals": 0.12, "leverage": 0.25},
    }
    sector = {"A": "Tech", "B": "Finance", "C": "Tech"}
    out = run_backtest_pd(prices, eps, funda, sector, weeks=20, runs_dir=str(tmp_path))
    import json
    import os

    assert os.path.isdir(out)
    assert os.path.isfile(os.path.join(out, "metrics.json"))
    metrics = json.load(open(os.path.join(out, "metrics.json")))
    assert "Sharpe" in metrics and "CAGR" in metrics and "TerminalEquity" in metrics
