from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


def load_latest_ic_series(
    runs_dir: str = "runs", factor_names: List[str] | None = None
) -> Dict[str, Dict[str, float]]:
    """Load IC series from the latest telemetry run."""

    root = Path(runs_dir)
    cand = sorted((p for p in root.glob("*/*/factors") if p.is_dir()))
    if not cand:
        return {}
    latest = cand[-1]
    out: Dict[str, Dict[str, float]] = {}
    for d in latest.iterdir():
        if not d.is_dir():
            continue
        name = d.name
        if factor_names and name not in factor_names:
            continue
        f = d / "ic_series.json"
        if f.exists():
            ser = json.loads(f.read_text(encoding="utf-8"))
            out[name] = {
                k: (float(v) if isinstance(v, (int, float)) else float("nan"))
                for k, v in ser.items()
            }
    return out
