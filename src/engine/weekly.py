from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping
import json
import uuid

from src.features.momentum import price_momentum
from src.features.revisions import revision_velocity
from src.features.quality import quality_composite
from src.metrics.perf import alpha_beta, sharpe, sortino
from src.portfolio.constraints import cap_by_name, cap_by_sector
from src.portfolio.governor import compute_drawdown
from src.signals.orthogonalize import sector_zscore
from src.telemetry.hashing import code_sha, hash_config
from src.telemetry.run_registry import RunRecord, save_run


@dataclass
class WeeklyParams:
    top_k: int = 20
    name_cap: float = 0.07
    sector_cap: float = 0.30
    w_mom: float = 0.5
    w_rev: float = 0.3
    w_qual: float = 0.2
    cost_bps_week: float = 2.4  # rough netting placeholder


def _rank(scores: Mapping[str, float]) -> dict[str, float]:
    items = [(ticker, float(value)) for ticker, value in scores.items()]
    if not items:
        return {}
    items.sort(key=lambda kv: kv[1])  # ascending
    n = len(items)
    return {ticker: (idx + 1) / n for idx, (ticker, _) in enumerate(items)}


def _select_top_k(scores: Mapping[str, float], k: int) -> dict[str, float]:
    k = max(1, int(k))
    items = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:k]
    if not items:
        return {}
    weight = 1.0 / len(items)
    return {ticker: weight for ticker, _ in items}


def run_weekly(
    prices_weekly: Mapping[str, list[float]],
    eps_weekly: Mapping[str, list[float]],
    fundamentals: Mapping[str, dict[str, float]],
    sector_map: Mapping[str, str],
    next_period_returns: Mapping[str, float],
    benchmark_returns: Mapping[str, float] | None,
    data_snapshot_id: str,
    params: WeeklyParams | None = None,
    runs_dir: str = "runs",
) -> str:
    """One-step weekly run: build signals, construct portfolio, compute realized metrics, persist artifacts."""
    param = params or WeeklyParams()

    mom_raw = price_momentum(prices_weekly, [13, 26, 52])
    mom = {
        ticker: sum(values.values()) / max(len(values), 1)
        for ticker, values in mom_raw.items()
    }
    rev = revision_velocity(eps_weekly, short=4, long=12)
    qual = quality_composite(
        gross_profit_margin={
            ticker: fundamentals.get(ticker, {}).get("gpm", 0.0)
            for ticker in prices_weekly
        },
        accruals={
            ticker: fundamentals.get(ticker, {}).get("accruals", 0.0)
            for ticker in prices_weekly
        },
        leverage={
            ticker: fundamentals.get(ticker, {}).get("leverage", 0.0)
            for ticker in prices_weekly
        },
    )

    mom_z = sector_zscore(mom, sector_map)
    rev_z = sector_zscore(rev, sector_map)
    qual_z = sector_zscore(qual, sector_map)

    composite = {
        ticker: param.w_mom * mom_z.get(ticker, 0.0)
        + param.w_rev * rev_z.get(ticker, 0.0)
        + param.w_qual * qual_z.get(ticker, 0.0)
        for ticker in prices_weekly
    }

    comp_rank = _rank(composite)
    preliminary = _select_top_k(comp_rank, param.top_k)
    capped = cap_by_name(preliminary, param.name_cap)
    weights = cap_by_sector(capped, sector_map, param.sector_cap)

    gross_ret = 0.0
    for ticker, weight in weights.items():
        gross_ret += weight * float(next_period_returns.get(ticker, 0.0))
    net_ret = gross_ret - (param.cost_bps_week / 1e4)

    weekly_series = [net_ret]
    if benchmark_returns:
        values = list(benchmark_returns.values())
        average_bench = sum(values) / max(len(values), 1)
        benchmark_series = [float(average_bench)]
    else:
        benchmark_series = [0.0]
    sharpe_ratio = sharpe(weekly_series)
    sortino_ratio = sortino(weekly_series)
    alpha_weekly, beta = alpha_beta(weekly_series, benchmark_series)
    equity = [1.0, 1.0 * (1.0 + net_ret)]
    drawdown = compute_drawdown(equity)
    max_drawdown = max(drawdown) if drawdown else 0.0

    started = datetime.now(timezone.utc).isoformat()
    run_id = uuid.uuid4().hex[:12]
    outdir = Path(runs_dir) / started[:10] / run_id
    outdir.mkdir(parents=True, exist_ok=True)

    metrics = {
        "Sharpe": sharpe_ratio,
        "Sortino": sortino_ratio,
        "MaxDD": max_drawdown,
        "Alpha_weekly": alpha_weekly,
        "Beta": beta,
        "Gross_weekly": gross_ret,
        "Net_weekly": net_ret,
        "Breadth": float(len(weights)),
    }
    cfg = {
        "top_k": param.top_k,
        "name_cap": param.name_cap,
        "sector_cap": param.sector_cap,
        "weights": {
            "mom": param.w_mom,
            "rev": param.w_rev,
            "qual": param.w_qual,
        },
        "cost_bps_week": param.cost_bps_week,
        "data_snapshot_id": data_snapshot_id,
    }

    record = RunRecord(
        run_id=run_id,
        code_sha=code_sha(),
        data_snapshot_id=data_snapshot_id,
        config_hash=hash_config(cfg),
        started_at=started,
        ended_at=started,
        metrics=metrics,
        paths={"root": str(outdir)},
    )

    (outdir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (outdir / "config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    save_run(record, base_dir=runs_dir)
    return str(outdir)
