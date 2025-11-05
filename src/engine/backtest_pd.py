from __future__ import annotations
import json
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path


def try_import_pandas():
    try:
        import pandas as pd  # type: ignore
        return pd
    except Exception:
        return None


def run_backtest_pd(
    prices_by_date: dict[str, dict[str, float]],
    eps_by_date: dict[str, dict[str, float]],
    fundamentals_latest: dict[str, dict[str, float]],
    sector_map: dict[str, str],
    weeks: int = 52,
    runs_dir: str = "runs",
    data_snapshot_id: str = "CSV_SNAPSHOT",
) -> str:
    """
    Vectorized pandas backtest (if pandas available). Returns run directory path.
    If pandas is not available, raises ImportError with a clear message.
    """
    pd = try_import_pandas()
    if pd is None:
        raise ImportError("pandas not available: install extras or run dependency-free engine.")

    # Build DataFrames (dates ascending)
    dates = sorted(prices_by_date.keys())
    px = pd.DataFrame.from_dict(prices_by_date, orient="index").sort_index().astype(float)
    # shift one step for returns
    rets = px.pct_change().shift(-1).iloc[:-1]  # next-period return

    # Simple factor: 26w momentum based on price ratio
    mom = (px / px.shift(26) - 1.0)
    # Revisions (short-long diff, using eps_by_date)
    eps_df = pd.DataFrame.from_dict(eps_by_date, orient="index").sort_index().astype(float)
    rev_short = eps_df - eps_df.shift(4)
    rev_long = eps_df - eps_df.shift(12)
    rev = rev_short - rev_long
    # Quality (latest snapshot mapped across all dates)
    qual = pd.DataFrame(
        {
            k: v.get("gpm", 0.0)
            - 0.5 * v.get("accruals", 0.0)
            - 0.5 * v.get("leverage", 0.0)
            for k, v in fundamentals_latest.items()
        },
        index=[0],
    )
    qual = pd.concat([qual] * len(px), ignore_index=True)
    qual.index = px.index

    # Sector z-score (by group each date)
    sector = pd.Series(sector_map)

    def sector_z(df: "pd.DataFrame") -> "pd.DataFrame":
        # z by sector per row (date)
        if sector.empty:
            return df.fillna(0.0)
        out = []
        for idx, row in df.iterrows():
            s = pd.DataFrame({"v": row}).join(sector.rename("sec"), how="left")
            g = s.groupby("sec")["v"]
            z = (s["v"] - g.transform("mean")) / g.transform("std", ddof=1)
            out.append(z.fillna(0.0).to_frame().T.set_index(pd.Index([idx])))
        return pd.concat(out).reindex(df.index)

    mom_z = sector_z(mom)
    rev_z = sector_z(rev)
    qual_z = sector_z(qual)
    comp = 0.5 * mom_z + 0.3 * rev_z + 0.2 * qual_z

    # Rank each row; take top-K equal-weight
    top_k = 20
    ranks = comp.rank(axis=1, method="average", pct=True)
    total_names = max(1, ranks.shape[1])
    quantile_level = 1 - top_k / total_names
    quantile_level = max(0.0, min(1.0, quantile_level))
    thresh = ranks.quantile(quantile_level, axis=1)
    weights = (ranks >= thresh.values[:, None]).astype(float)
    # equal weight among selected names
    weights = weights.div(weights.sum(axis=1).replace(0, 1.0), axis=0)

    # Realized next-period returns (align to rets index)
    weights = weights.reindex(index=rets.index, columns=rets.columns).fillna(0.0)
    port_ret_gross = (weights * rets).sum(axis=1)
    cost_bps_week = 2.4
    port_ret_net = port_ret_gross - (cost_bps_week / 1e4)
    equity = (1.0 + port_ret_net).cumprod()

    # Metrics
    def _ann_scale(sr: float, n: int) -> float:
        return sr * (n ** 0.5) if n > 0 else float("nan")

    sr = port_ret_net.mean() / (port_ret_net.std(ddof=1) or float("nan"))
    sharpe = _ann_scale(sr, 52)
    downside = port_ret_net.clip(upper=0.0)
    down_std = float(downside.std(ddof=1)) if len(downside) > 1 else 0.0
    if down_std == 0.0:
        sortino = float("inf") if float(port_ret_net.mean()) > 0 else 0.0
    else:
        sortino = float(port_ret_net.mean() / down_std * (52 ** 0.5))
    # Alpha/Beta via OLS vs equal-weight benchmark of available names each week (simplistic)
    bench = rets.mean(axis=1)
    cov = port_ret_net.cov(bench)
    var = bench.var()
    beta = float("nan") if var == 0 else cov / var
    alpha = port_ret_net.mean() - beta * bench.mean() if var != 0 else float("nan")
    # Max drawdown
    roll_max = equity.cummax()
    dd = (roll_max - equity) / roll_max
    max_dd = float(dd.max()) if not dd.empty else 0.0
    cagr = float(equity.iloc[-1] ** (52 / max(1, len(equity))) - 1.0)
    # Turnover per period
    w_diff = weights.diff().abs().sum(axis=1) / 2.0
    turnover_mean = float(w_diff.mean()) if len(w_diff) else 0.0
    turnover_median = float(w_diff.median()) if len(w_diff) else 0.0

    # Persist
    started = datetime.now(timezone.utc).isoformat()
    rid = uuid.uuid4().hex[:12]
    outdir = Path(runs_dir) / started[:10] / rid
    outdir.mkdir(parents=True, exist_ok=True)
    
    def _safe_num(x: float) -> float | str:
        try:
            if x is None:
                return "NaN"
            value = float(x)
            if math.isfinite(value):
                return value
            if math.isinf(value):
                return "Infinity" if value > 0 else "-Infinity"
            return "NaN"
        except Exception:
            return "NaN"

    metrics = {
        "Sharpe": _safe_num(sharpe),
        "Sortino": _safe_num(sortino),
        "Alpha": _safe_num(alpha),
        "Beta": _safe_num(beta),
        "CAGR": _safe_num(cagr),
        "MaxDD": _safe_num(max_dd),
        "Turnover_mean": _safe_num(turnover_mean),
        "Turnover_median": _safe_num(turnover_median),
        "TerminalEquity": _safe_num(float(equity.iloc[-1]) if len(equity) else float("nan")),
        "TotalWeeks": int(len(equity)),
        "bench_method": "equal_weight_universe",
    }
    (outdir / "metrics.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8"
    )
    (outdir / "returns.json").write_text(
        json.dumps(list(map(float, port_ret_net.values)), indent=2), encoding="utf-8"
    )
    (outdir / "equity.json").write_text(
        json.dumps(list(map(float, equity.values)), indent=2), encoding="utf-8"
    )
    weights.to_csv(outdir / "weights.csv", index=True)
    last = weights.iloc[-1].dropna().to_dict() if len(weights) else {}
    (outdir / "holdings_last.json").write_text(
        json.dumps(last, indent=2), encoding="utf-8"
    )
    # minimal run.json
    run_meta = {
        "run_id": rid,
        "started_at": started,
        "ended_at": started,
        "paths": {"root": str(outdir)},
        "data_snapshot_id": data_snapshot_id,
    }
    (outdir / "run.json").write_text(json.dumps(run_meta, indent=2), encoding="utf-8")
    return str(outdir)
