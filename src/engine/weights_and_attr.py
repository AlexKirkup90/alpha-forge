from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from src.regime.filters import make_regime_gates
from src.signals.weighting import (
    apply_gates,
    clamp_and_normalize_weights,
    compute_ic_ema_series,
)


def _safe(x: float) -> float | str:
    try:
        xf = float(x)
        if math.isfinite(xf):
            return xf
        return "Infinity" if math.isinf(xf) and xf > 0 else "-Infinity"
    except Exception:
        return "NaN"


def run_factor_weighting_and_attr(
    ic_series_by_factor: Dict[str, Dict[str, float]],
    bench_weekly_returns: Dict[str, float] | None,
    factor_names: List[str],
    runs_dir: str = "runs",
    data_snapshot_id: str = "SNAPSHOT",
    alpha: float = 0.2,
    gate_cfg: dict | None = None,
) -> str:
    """Run adaptive weighting, gates, attribution, and persist artifacts."""

    ic_ema = compute_ic_ema_series(ic_series_by_factor, alpha=alpha)
    gates = make_regime_gates(bench_weekly_returns or {}, factor_names)

    dates = sorted(ic_ema.keys())
    weights_by_date: Dict[str, Dict[str, float]] = {}
    contrib_by_date: Dict[str, Dict[str, float]] = {}

    for d in dates:
        scores = {f: ic_ema[d].get(f, float("nan")) for f in factor_names}
        w = clamp_and_normalize_weights(scores)
        w = apply_gates(w, gates.get(d, {}))
        w = clamp_and_normalize_weights(w)
        weights_by_date[d] = w
        contrib_by_date[d] = {
            f: float(w[f]) * float(scores.get(f, 0.0))
            if math.isfinite(float(scores.get(f, float("nan"))))
            else 0.0
            for f in factor_names
        }

    summary: Dict[str, dict] = {}
    for f in factor_names:
        ic_vals = [
            ic_ema[d].get(f)
            for d in dates
            if ic_ema[d].get(f) is not None and isinstance(ic_ema[d].get(f), (int, float))
        ]
        w_vals = [weights_by_date[d].get(f, 0.0) for d in dates]
        g_vals = [gates.get(d, {}).get(f, 1) for d in dates]
        c_vals = [contrib_by_date[d].get(f, 0.0) for d in dates]
        ic_mean = sum(ic_vals) / len(ic_vals) if ic_vals else float("nan")
        summary[f] = {
            "ic_ema_mean": _safe(ic_mean),
            "avg_weight": _safe(sum(w_vals) / len(w_vals) if w_vals else float("nan")),
            "avg_gate": _safe(sum(g_vals) / len(g_vals) if g_vals else float("nan")),
            "avg_contrib": _safe(sum(c_vals) / len(c_vals) if c_vals else float("nan")),
        }

    started = datetime.now(timezone.utc).isoformat()
    outdir = Path(runs_dir) / started[:10] / ("weights_" + started.replace(":", "").replace("-", "")[:15])
    outdir.mkdir(parents=True, exist_ok=True)
    weights_dir = outdir / "factors" / "weights"
    weights_dir.mkdir(parents=True, exist_ok=True)

    (weights_dir / "ic_ema.json").write_text(json.dumps(ic_ema, indent=2), encoding="utf-8")
    (weights_dir / "gates.json").write_text(json.dumps(gates, indent=2), encoding="utf-8")
    (weights_dir / "weights.json").write_text(json.dumps(weights_by_date, indent=2), encoding="utf-8")
    (weights_dir / "contrib.json").write_text(json.dumps(contrib_by_date, indent=2), encoding="utf-8")
    (weights_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    meta = {
        "run_id": outdir.name,
        "started_at": started,
        "ended_at": started,
        "paths": {"root": str(outdir)},
        "data_snapshot_id": data_snapshot_id,
        "factors": factor_names,
        "alpha_ic_ema": alpha,
    }
    (outdir / "run.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return str(outdir)
