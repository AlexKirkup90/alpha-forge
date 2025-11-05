from __future__ import annotations

from typing import Dict, List
from abc import ABC, abstractmethod


class DataProvider(ABC):
    """Abstract provider for weekly data (ISO date strings)."""

    @abstractmethod
    def fetch_prices_weekly(
        self, tickers: List[str], lookback_weeks: int = 156
    ) -> Dict[str, Dict[str, float]]:
        """Return {date: {ticker: close}}."""

    @abstractmethod
    def fetch_eps_weekly(
        self, tickers: List[str], lookback_weeks: int = 156
    ) -> Dict[str, Dict[str, float]]:
        """Return {date: {ticker: eps_estimate}} (best-effort if unavailable)."""

    @abstractmethod
    def fetch_fundamentals_latest(self, tickers: List[str]) -> Dict[str, Dict[str, float]]:
        """Return {ticker: {gpm, accruals, leverage}}."""

    @abstractmethod
    def fetch_sector_map(self, tickers: List[str]) -> Dict[str, str]:
        """Return {ticker: sector}."""
