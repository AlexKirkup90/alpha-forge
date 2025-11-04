from __future__ import annotations

import json
import math
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence

from src.engine.weekly import WeeklyParams, _rank, _select_top_k
from src.features.momentum import price_momentum
from src.features.quality import quality_composite
from src.features.revisions import revision_velocity
from src.metrics.perf import alpha_beta, sharpe, sortino
from src.portfolio.constraints import cap_by_name, cap_by_sector
from src.portfolio.governor import compute_drawdown
from src.signals.orthogonalize import sector_zscore
from src.telemetry.hashing import code_sha, hash_config
from src.telemetry.run_registry import RunRecord, save_run


@dataclass(frozen=True)
class WeeklyBatch:
    """Container with all data needed for a single weekly rebalance step."""

    prices: Mapping[str, Sequence[float]]
    eps: Mapping[str, Sequence[float]]
    fundamentals: Mapping[str, Mapping[str, float]]
    next_returns: Mapping[str, float]
    benchmark: Mapping[str, float] | None = None


def _composite_scores(
    batch: WeeklyBatch,
    sector_map: Mapping[str, str],
    params: WeeklyParams,
) -> Mapping[str, float]:
    mom_raw = price_momentum(batch.prices, [13, 26, 52])
    mom = {
        ticker: (sum(values.values()) / max(len(values), 1)) if values else 0.0
        for ticker, values in mom_raw.items()
    }
    rev = revision_velocity(batch.eps, short=4, long=12)
    qual = quality_composite(
        gross_profit_margin={
            ticker: batch.fundamentals.get(ticker, {}).get("gpm", 0.0)
            for ticker in batch.prices
        },
        accruals={
            ticker: batch.fundamentals.get(ticker, {}).get("accruals", 0.0)
            for ticker in batch.prices
        },
        leverage={
            ticker: batch.fundamentals.get(ticker, {}).get("leverage", 0.0)
            for ticker in batch.prices
        },
    )

    mom_z = sector_zscore(mom, sector_map)
    rev_z = sector_zscore(rev, sector_map)
    qual_z = sector_zscore(qual, sector_map)

    composite = {
        ticker: params.w_mom * mom_z.get(ticker, 0.0)
        + params.w_rev * rev_z.get(ticker, 0.0)
        + params.w_qual * qual_z.get(ticker, 0.0)
        for ticker in batch.prices
    }
    return composite


def _portfolio_weights(
    scores: Mapping[str, float],
    sector_map: Mapping[str, str],
    params: WeeklyParams,
) -> dict[str, float]:
    ranked = _rank(scores)
    preliminary = _select_top_k(ranked, params.top_k)
    capped = cap_by_name(preliminary, params.name_cap)
    weights = cap_by_sector(capped, sector_map, params.sector_cap)
    return {ticker: float(weight) for ticker, weight in weights.items()}


def _turnover(prev_weights: Mapping[str, float], curr_weights: Mapping[str, float]) -> float:
    tickers: set[str] = set(prev_weights) | set(curr_weights)
    change = 0.0
    for ticker in tickers:
        change += abs(float(curr_weights.get(ticker, 0.0)) - float(prev_weights.get(ticker, 0.0)))
    return 0.5 * change


def _avg_benchmark_return(benchmark: Mapping[str, float] | None) -> float:
    if not benchmark:
        return 0.0
    values = [float(v) for v in benchmark.values()]
    if not values:
        return 0.0
    return sum(values) / len(values)


def _cagr(equity: Sequence[float], periods_per_year: int = 52) -> float:
    if len(equity) < 2:
        return math.nan
    total_return = float(equity[-1]) / float(equity[0])
    if total_return <= 0:
        return math.nan
    periods = len(equity) - 1
    years = periods / periods_per_year
    if years <= 0:
        return math.nan
    return total_return ** (1.0 / years) - 1.0


def run_walkforward(
    batches: Sequence[WeeklyBatch],
    sector_map: Mapping[str, str],
    data_snapshot_id: str,
    params: WeeklyParams | None = None,
    runs_dir: str = "runs",
) -> tuple[str, dict[str, float]]:
    """Simulate a multi-week walk-forward using the dependency-free weekly engine."""

    if not batches:
        raise ValueError("batches must contain at least one WeeklyBatch entry")

    param = params or WeeklyParams()
    net_returns: list[float] = []
    gross_returns: list[float] = []
    bench_returns: list[float] = []
    equity_curve: list[float] = [1.0]
    total_turnover = 0.0
    prev_weights: dict[str, float] = {}
    weights_history: list[dict[str, float]] = []

    for batch in batches:
        composite = _composite_scores(batch, sector_map, param)
        weights = _portfolio_weights(composite, sector_map, param)
        weights_history.append(weights)

        gross = 0.0
        for ticker, weight in weights.items():
            gross += weight * float(batch.next_returns.get(ticker, 0.0))
        net = gross - (param.cost_bps_week / 1e4)

        gross_returns.append(gross)
        net_returns.append(net)
        bench_returns.append(_avg_benchmark_return(batch.benchmark))

        total_turnover += _turnover(prev_weights, weights)
        prev_weights = weights

        equity_curve.append(equity_curve[-1] * (1.0 + net))

    sharpe_ratio = sharpe(net_returns)
    sortino_ratio = sortino(net_returns)
    alpha_weekly, beta = alpha_beta(net_returns, bench_returns)
    drawdown = compute_drawdown(equity_curve)
    max_drawdown = max(drawdown) if drawdown else math.nan
    cagr_value = _cagr(equity_curve)
    avg_turnover = total_turnover / len(net_returns) if net_returns else math.nan

    started = datetime.now(timezone.utc)
    run_id = uuid.uuid4().hex[:12]
    outdir = Path(runs_dir) / started.strftime("%Y-%m-%d") / run_id
    outdir.mkdir(parents=True, exist_ok=True)

    metrics = {
        "Sharpe": sharpe_ratio,
        "Sortino": sortino_ratio,
        "Alpha": alpha_weekly,
        "Beta": beta,
        "CAGR": cagr_value,
        "MaxDD": max_drawdown,
        "Turnover": avg_turnover,
        "TerminalEquity": equity_curve[-1],
        "TotalWeeks": len(net_returns),
    }

    returns_payload = {
        "gross": gross_returns,
        "net": net_returns,
        "equity": equity_curve,
        "benchmark": bench_returns,
        "weights": weights_history,
    }

    config = {
        "params": asdict(param),
        "data_snapshot_id": data_snapshot_id,
        "weeks": len(batches),
    }

    metrics_path = outdir / "metrics.json"
    config_path = outdir / "config.json"
    returns_path = outdir / "returns.json"

    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    returns_path.write_text(json.dumps(returns_payload, indent=2), encoding="utf-8")

    record = RunRecord(
        run_id=run_id,
        code_sha=code_sha(),
        data_snapshot_id=data_snapshot_id,
        config_hash=hash_config(config),
        started_at=started.isoformat(),
        ended_at=datetime.now(timezone.utc).isoformat(),
        metrics=metrics,
        paths={"root": str(outdir)},
    )
    save_run(record, base_dir=runs_dir)

    return str(outdir), metrics
