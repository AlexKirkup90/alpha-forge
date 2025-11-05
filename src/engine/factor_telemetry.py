from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.factors import FACTOR_REGISTRY, factor_quality_q
from src.metrics.ic import ic_series, ic_summary, next_period_returns_from_prices


def _to_df(wide_by_date: dict[str, dict[str, float]]) -> pd.DataFrame:
    if not wide_by_date:
        return pd.DataFrame()
    df = pd.DataFrame.from_dict(wide_by_date, orient="index").sort_index().astype(float)
    return df


def run_factor_ic_telemetry(
    prices_by_date: dict[str, dict[str, float]],
    eps_by_date: dict[str, dict[str, float]] | None,
    fundamentals_latest: dict[str, dict[str, float]] | None,
    factor_names: list[str],
    runs_dir: str = "runs",
    data_snapshot_id: str = "SNAPSHOT",
) -> str:
    """Compute factor IC series for selected factors and persist artifacts."""
    px = _to_df(prices_by_date)
    eps = _to_df(eps_by_date or {})
    next_ret = next_period_returns_from_prices(px)

    started = datetime.now(timezone.utc).isoformat()
    rid = uuid.uuid4().hex[:12]
    outdir = Path(runs_dir) / started[:10] / rid / "factors"
    outdir.mkdir(parents=True, exist_ok=True)

    run_meta = {
        "run_id": rid,
        "started_at": started,
        "ended_at": started,
        "paths": {"root": str(outdir.parent)},
        "data_snapshot_id": data_snapshot_id,
    }
    (outdir.parent / "run.json").write_text(json.dumps(run_meta, indent=2), encoding="utf-8")

    for name in factor_names:
        if name not in FACTOR_REGISTRY and name != "quality_q":
            continue

        if name == "quality_q":
            scores = factor_quality_q(fundamentals_latest or {}, px.index, list(px.columns))
        else:
            func = FACTOR_REGISTRY[name]
            if name.startswith("eps"):
                scores = func(eps)
            else:
                scores = func(px)

        ic_ser = ic_series(scores, next_ret)
        summary = ic_summary(ic_ser)

        fdir = outdir / name
        fdir.mkdir(parents=True, exist_ok=True)
        ic_payload = {
            str(k): float(v) if pd.notna(v) else "NaN"
            for k, v in ic_ser.items()
        }
        (fdir / "ic_series.json").write_text(json.dumps(ic_payload, indent=2), encoding="utf-8")
        (fdir / "ic_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return str(outdir.parent)


__all__ = ["run_factor_ic_telemetry"]
