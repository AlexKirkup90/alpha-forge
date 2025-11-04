from __future__ import annotations

import json
import math
from pathlib import Path

from src.engine.backtest import WeeklyBatch, run_walkforward
from src.engine.weekly import WeeklyParams


def _make_synthetic_batches(weeks: int = 12):
    tickers = ["AAA", "BBB", "CCC"]
    sector_map = {"AAA": "Tech", "BBB": "Finance", "CCC": "Health"}
    base_prices = {"AAA": 50.0, "BBB": 40.0, "CCC": 30.0}
    growth = {"AAA": 0.012, "BBB": 0.008, "CCC": 0.01}
    base_eps = {"AAA": 2.0, "BBB": 1.5, "CCC": 1.2}
    eps_trend = {"AAA": 0.02, "BBB": 0.015, "CCC": 0.018}

    price_history = {t: [] for t in tickers}
    eps_history = {t: [] for t in tickers}

    warmup = 13
    total_points = warmup + weeks + 1

    for step in range(total_points):
        for t in tickers:
            drift = base_prices[t] * (1 + growth[t]) ** step
            seasonal = 1 + 0.01 * math.sin(step / 3.0 + len(t))
            price_history[t].append(drift * seasonal)

            eps_level = base_eps[t] + eps_trend[t] * step
            eps_cycle = 0.05 * math.cos(step / 4.0 + len(t))
            eps_history[t].append(eps_level + eps_cycle)

    batches: list[WeeklyBatch] = []
    for week in range(warmup, warmup + weeks):
        prices = {t: price_history[t][: week + 1] for t in tickers}
        eps = {t: eps_history[t][: week + 1] for t in tickers}
        fundamentals = {
            t: {
                "gpm": 0.4 + 0.01 * (idx + 1) + 0.001 * week,
                "accruals": 0.1 + 0.002 * idx,
                "leverage": 0.2 + 0.001 * (weeks - idx),
            }
            for idx, t in enumerate(tickers)
        }
        next_returns = {
            t: price_history[t][week + 1] / price_history[t][week] - 1.0 for t in tickers
        }
        bench_ret = sum(next_returns.values()) / len(next_returns)
        batches.append(
            WeeklyBatch(
                prices=prices,
                eps=eps,
                fundamentals=fundamentals,
                next_returns=next_returns,
                benchmark={"SPY": bench_ret},
            )
        )

    return batches, sector_map


def test_walkforward_produces_artifacts(tmp_path: Path):
    batches, sector_map = _make_synthetic_batches(weeks=13)
    out_path, metrics = run_walkforward(
        batches=batches,
        sector_map=sector_map,
        data_snapshot_id="SYNTH-DEMO",
        params=WeeklyParams(top_k=2, name_cap=0.6, sector_cap=0.7),
        runs_dir=str(tmp_path),
    )

    run_dir = Path(out_path)
    assert run_dir.exists(), "run directory should be created"

    metrics_file = run_dir / "metrics.json"
    returns_file = run_dir / "returns.json"
    run_file = run_dir / "run.json"
    config_file = run_dir / "config.json"

    for artifact in (metrics_file, returns_file, run_file, config_file):
        assert artifact.exists(), f"missing artifact: {artifact.name}"

    metrics_payload = json.loads(metrics_file.read_text(encoding="utf-8"))
    assert metrics_payload == metrics
    for key in ["Sharpe", "Sortino", "Alpha", "Beta", "CAGR", "MaxDD", "Turnover"]:
        assert key in metrics_payload
    assert metrics_payload["TotalWeeks"] == len(batches)
    assert math.isfinite(metrics_payload["TerminalEquity"]) and metrics_payload["TerminalEquity"] > 0

    returns_payload = json.loads(returns_file.read_text(encoding="utf-8"))
    assert len(returns_payload["net"]) == len(batches)
    assert len(returns_payload["gross"]) == len(batches)
    assert len(returns_payload["equity"]) == len(batches) + 1
    assert len(returns_payload["benchmark"]) == len(batches)
    assert returns_payload["weights"], "weights history should not be empty"

    registry_payload = json.loads(run_file.read_text(encoding="utf-8"))
    assert registry_payload["metrics"]["Sharpe"] == metrics_payload["Sharpe"]
    assert registry_payload["paths"]["root"] == str(run_dir)

    config_payload = json.loads(config_file.read_text(encoding="utf-8"))
    assert config_payload["data_snapshot_id"] == "SYNTH-DEMO"
    assert config_payload["weeks"] == len(batches)
    assert config_payload["params"]["top_k"] == 2
