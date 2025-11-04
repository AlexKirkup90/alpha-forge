from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path


def write_demo_run(
    base_dir: str = "runs",
    data_snapshot_id: str = "SNAPSHOT_DEMO",
    run_id: str | None = None,
) -> str:
    rid = run_id or uuid.uuid4().hex[:12]
    started = datetime.now(timezone.utc).isoformat()
    day = started[:10]
    outdir = Path(base_dir) / day / rid
    outdir.mkdir(parents=True, exist_ok=True)

    # minimal, deterministic “metrics”
    metrics = {
        "Sharpe": 1.23,
        "Sortino": 1.80,
        "MaxDD": 0.18,
        "Alpha_weekly": 0.0009,
        "CAGR_gross": 0.265,
        "CAGR_net": 0.251,
        "Turnover": 0.34,
        "Costs_bps_week": 2.4,
    }

    run = {
        "run_id": rid,
        "started_at": started,
        "ended_at": started,
        "code_sha": "unknown",
        "data_snapshot_id": data_snapshot_id,
        "config_hash": "demo",
        "metrics": metrics,
        "paths": {"root": str(outdir)},
    }

    (outdir / "run.json").write_text(json.dumps(run, indent=2), encoding="utf-8")
    (outdir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    # create an empty ledger so the UI has all files it expects later
    (outdir / "ledger.parquet").write_bytes(b"")  # placeholder
    return str(outdir)
