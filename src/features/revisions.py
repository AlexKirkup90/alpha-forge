from __future__ import annotations

from typing import Mapping, Sequence


def revision_velocity(
    eps_estimates: Mapping[str, Sequence[float]],
    short: int = 4,
    long: int = 12,
) -> dict[str, float]:
    """
    eps_estimates: ticker -> sequence of weekly EPS estimates (oldest...newest).
    Returns: ticker -> (rolling short change - rolling long change) at the end.
    """
    out: dict[str, float] = {}
    window = max(short, long) + 1
    for tkr, seq in eps_estimates.items():
        if len(seq) < window:
            out[tkr] = 0.0
            continue
        s = float(seq[-1]) - float(seq[-1 - short])
        l = float(seq[-1]) - float(seq[-1 - long])
        out[tkr] = s - l
    return out
