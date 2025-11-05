from __future__ import annotations

from typing import Dict, List
from pathlib import Path
from datetime import datetime, timezone
import json


def write_snapshot(
    prices_by_date: Dict[str, Dict[str, float]],
    eps_by_date: Dict[str, Dict[str, float]],
    fundamentals_latest: Dict[str, Dict[str, float]],
    sector_map: Dict[str, str],
    base_dir: str = "data/snapshots",
    snap_id: str | None = None,
) -> str:
    snap = snap_id or datetime.now(timezone.utc).strftime("SNAP_%Y%m%d_%H%M%S")
    out = Path(base_dir) / snap
    out.mkdir(parents=True, exist_ok=True)
    (out / "prices_by_date.json").write_text(
        json.dumps(prices_by_date), encoding="utf-8"
    )
    (out / "eps_by_date.json").write_text(json.dumps(eps_by_date), encoding="utf-8")
    (out / "fundamentals_latest.json").write_text(
        json.dumps(fundamentals_latest), encoding="utf-8"
    )
    (out / "sector_map.json").write_text(json.dumps(sector_map), encoding="utf-8")
    (out / "manifest.json").write_text(
        json.dumps({"snapshot_id": snap}), encoding="utf-8"
    )
    return str(out)


def load_snapshot(snap_dir: str) -> tuple[dict, dict, dict, dict]:
    p = Path(snap_dir)
    prices_by_date = json.loads((p / "prices_by_date.json").read_text(encoding="utf-8"))
    eps_by_date = json.loads((p / "eps_by_date.json").read_text(encoding="utf-8"))
    fundamentals_latest = json.loads(
        (p / "fundamentals_latest.json").read_text(encoding="utf-8")
    )
    sector_map = json.loads((p / "sector_map.json").read_text(encoding="utf-8"))
    return prices_by_date, eps_by_date, fundamentals_latest, sector_map


def list_snapshots(base_dir: str = "data/snapshots") -> List[str]:
    p = Path(base_dir)
    if not p.exists():
        return []
    return [str(d) for d in sorted(p.iterdir()) if d.is_dir()]
