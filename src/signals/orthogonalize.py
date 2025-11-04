from __future__ import annotations

from typing import Mapping


def sector_zscore(scores: Mapping[str, float], sector_map: Mapping[str, str]) -> dict[str, float]:
    """
    Z-score within each sector group: (x - mean_sector)/std_sector (ddof=1).
    If a sector has <2 names or std=0, return 0 for that sector.
    """
    groups: dict[str, list[float]] = {}
    for t, score in scores.items():
        sec = sector_map.get(t, "UNK")
        groups.setdefault(sec, []).append(float(score))

    stats: dict[str, tuple[float, float]] = {}
    for sec, vals in groups.items():
        if len(vals) < 2:
            stats[sec] = (0.0, 0.0)
            continue
        mean = sum(vals) / len(vals)
        var = sum((v - mean) ** 2 for v in vals) / (len(vals) - 1)
        stats[sec] = (mean, var ** 0.5)

    out: dict[str, float] = {}
    for t, score in scores.items():
        sec = sector_map.get(t, "UNK")
        mean, std = stats[sec]
        out[t] = 0.0 if std == 0.0 else (float(score) - mean) / std
    return out
