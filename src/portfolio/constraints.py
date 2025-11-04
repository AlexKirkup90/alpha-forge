from __future__ import annotations

from typing import Mapping


def cap_by_name(weights: Mapping[str, float], cap: float = 0.05) -> dict[str, float]:
    """Clip absolute weight by per-name cap and renormalize to sum(abs)=1 (if possible)."""
    clipped: dict[str, float] = {
        t: max(min(float(w), cap), -cap) for t, w in weights.items()
    }
    total = sum(abs(v) for v in clipped.values())
    if total == 0.0:
        return {t: 0.0 for t in clipped}
    if total >= 1.0:
        return {t: v / total for t, v in clipped.items()}

    capacities: dict[str, float] = {
        t: max(cap - abs(v), 0.0) for t, v in clipped.items()
    }
    signs: dict[str, float] = {}
    for t, v in clipped.items():
        if v > 0:
            signs[t] = 1.0
        elif v < 0:
            signs[t] = -1.0
        else:
            orig = float(weights.get(t, 0.0))
            if orig > 0:
                signs[t] = 1.0
            elif orig < 0:
                signs[t] = -1.0
            else:
                signs[t] = 0.0

    leftover = 1.0 - total
    while leftover > 1e-12:
        available = [t for t, cap_left in capacities.items() if cap_left > 1e-12 and signs[t] != 0.0]
        if not available:
            break
        share = leftover / len(available)
        progressed = False
        for t in available:
            delta = min(capacities[t], share)
            if delta <= 0.0:
                continue
            clipped[t] += signs[t] * delta
            capacities[t] -= delta
            leftover -= delta
            progressed = True
        if not progressed:
            break

    total = sum(abs(v) for v in clipped.values())
    if total == 0.0:
        return {t: 0.0 for t in clipped}
    if total >= 1.0:
        return {t: v / total for t, v in clipped.items()}
    return clipped


def cap_by_sector(
    weights: Mapping[str, float],
    sector_map: Mapping[str, str],
    cap: float = 0.20,
) -> dict[str, float]:
    """If sector abs-sum exceeds cap, scale that sector down proportionally, then renormalize."""
    sec_sum: dict[str, float] = {}
    for t, w in weights.items():
        sec = sector_map.get(t, "UNK")
        sec_sum[sec] = sec_sum.get(sec, 0.0) + abs(float(w))

    scaled = dict(weights)
    for t, w in weights.items():
        sec = sector_map.get(t, "UNK")
        s = sec_sum[sec]
        if s > cap and s > 0:
            scaled[t] = float(w) * (cap / s)

    total = sum(abs(v) for v in scaled.values())
    if total == 0.0:
        return {t: 0.0 for t in scaled}
    if total > 1.0:
        return {t: v / total for t, v in scaled.items()}
    return {t: float(v) for t, v in scaled.items()}
