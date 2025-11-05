from __future__ import annotations

from typing import Dict, List
from datetime import datetime, timedelta

from .base import DataProvider


def _try_import_yf():
    try:
        import yfinance as yf  # type: ignore

        return yf
    except Exception:
        return None


def _iso(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")


class YFinanceProvider(DataProvider):
    """Best-effort weekly data via yfinance (no key)."""

    def __init__(self):
        self.yf = _try_import_yf()

    def _guard(self):
        if self.yf is None:
            raise ImportError(
                "yfinance not installed. Install extras: `pip install -e .[providers]`"
            )

    def fetch_prices_weekly(
        self, tickers: List[str], lookback_weeks: int = 156
    ) -> Dict[str, Dict[str, float]]:
        self._guard()
        end = datetime.utcnow()
        start = end - timedelta(weeks=lookback_weeks + 4)
        dl = self.yf.download(
            tickers=tickers,
            start=_iso(start),
            end=_iso(end),
            interval="1wk",
            auto_adjust=True,
            threads=False,
        )
        data: Dict[str, Dict[str, float]] = {}
        if hasattr(dl, "empty") and not dl.empty:
            closes = dl["Close"] if "Close" in dl else dl
            if not hasattr(closes, "columns"):
                try:
                    closes = closes.to_frame(name=tickers[0] if tickers else "value")
                except Exception:
                    closes = closes.to_frame()
            closes = closes.fillna(method="ffill").fillna(0.0)
            idx = closes.index
            cols = list(closes.columns) if hasattr(closes, "columns") else tickers
            for i in range(len(idx)):
                date = _iso(idx[i].to_pydatetime())
                row: Dict[str, float] = {}
                for t in cols:
                    try:
                        row[str(t)] = float(closes.loc[idx[i], t])
                    except Exception:
                        row[str(t)] = 0.0
                data[date] = row
        return data

    def fetch_eps_weekly(
        self, tickers: List[str], lookback_weeks: int = 156
    ) -> Dict[str, Dict[str, float]]:
        """Placeholder EPS series when real estimates aren’t available."""
        prices = self.fetch_prices_weekly(tickers, lookback_weeks)
        dates = sorted(prices.keys())
        out: Dict[str, Dict[str, float]] = {}
        for i, d in enumerate(dates):
            row = {t: 1.0 + 0.001 * i for t in tickers}  # mild drift
            out[d] = row
        return out

    def fetch_fundamentals_latest(self, tickers: List[str]) -> Dict[str, Dict[str, float]]:
        """Conservative placeholders (replace when keyed provider available)."""
        return {t: {"gpm": 0.5, "accruals": 0.1, "leverage": 0.3} for t in tickers}

    def fetch_sector_map(self, tickers: List[str]) -> Dict[str, str]:
        self._guard()
        out: Dict[str, str] = {}
        for t in tickers:
            try:
                info = self.yf.Ticker(t).info or {}
                out[t] = info.get("sector") or "UNK"
            except Exception:
                out[t] = "UNK"
        return out
