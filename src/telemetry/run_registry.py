"""Run registry utilities."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict


@dataclass
class RunRecord:
    """Record describing a single backtest run."""
    run_id: str
    code_sha: str
    data_snapshot_id: str
    config_hash: str
    started_at: str
    ended_at: str
    metrics: Dict[str, float]
    paths: Dict[str, str]


def save_run(record: RunRecord, base_dir: str = "runs") -> str:
    """Persist a run record and associated metadata to disk."""
    base_path = Path(base_dir)
    day_dir = base_path / record.started_at[:10]
    run_path = day_dir / record.run_id
    run_path.mkdir(parents=True, exist_ok=True)

    run_json = run_path / "run.json"
    metrics_json = run_path / "metrics.json"
    hashes_json = run_path / "hashes.json"

    with run_json.open("w", encoding="utf-8") as f:
        json.dump(asdict(record), f, indent=2, sort_keys=True)

    with metrics_json.open("w", encoding="utf-8") as f:
        json.dump(record.metrics, f, indent=2, sort_keys=True)

    hashes_payload = {
        "code_sha": record.code_sha,
        "config_hash": record.config_hash,
        "data_snapshot_id": record.data_snapshot_id,
    }
    with hashes_json.open("w", encoding="utf-8") as f:
        json.dump(hashes_payload, f, indent=2, sort_keys=True)

    return str(run_path)
