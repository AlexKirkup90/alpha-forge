from __future__ import annotations

from typing import Dict, List
import os

from .base import DataProvider

def _get_key() -> str | None:
    return os.getenv("POLYGON_API_KEY") or None


class PolygonProvider(DataProvider):
    """Stub for Polygon provider (HTTP disabled in restricted environments)."""

    def __init__(self):
        self.key = _get_key()
        if not self.key:
            raise RuntimeError("POLYGON_API_KEY not set in environment")

    def fetch_prices_weekly(
        self, tickers: List[str], lookback_weeks: int = 156
    ) -> Dict[str, Dict[str, float]]:
        raise NotImplementedError(
            "Polygon HTTP calls are disabled in this environment."
        )

    def fetch_eps_weekly(
        self, tickers: List[str], lookback_weeks: int = 156
    ) -> Dict[str, Dict[str, float]]:
        raise NotImplementedError(
            "Polygon EPS endpoint not implemented in this environment."
        )

    def fetch_fundamentals_latest(
        self, tickers: List[str]
    ) -> Dict[str, Dict[str, float]]:
        raise NotImplementedError(
            "Polygon fundamentals endpoint not implemented in this environment."
        )

    def fetch_sector_map(self, tickers: List[str]) -> Dict[str, str]:
        raise NotImplementedError("Polygon reference/sector endpoint not implemented.")
