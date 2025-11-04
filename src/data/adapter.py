from __future__ import annotations
from typing import Dict, Tuple
import csv

# ---- CSV Schemas ----
# prices.csv: date,ticker,close
# eps.csv:    date,ticker,eps_estimate
# funda.csv:  date,ticker,gpm,accruals,leverage
#
# Constraints: weekly data or daily that you will pre-aggregate to weekly outside.


def load_prices_csv(path: str) -> Dict[str, Dict[str, float]]:
    """Return: {date: {ticker: close}} (wide-by-date mapping for fast alignment)."""
    out: Dict[str, Dict[str, float]] = {}
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            d = row["date"]
            t = row["ticker"]
            c = float(row["close"])
            out.setdefault(d, {})[t] = c
    return out


def pivot_prices_to_ticker_series(prices_by_date: Dict[str, Dict[str, float]]) -> Dict[str, list[float]]:
    """Convert {date:{t:c}} → {ticker:[…]} ordered by sorted date ascending."""
    dates = sorted(prices_by_date.keys())
    tickers = set()
    for d in dates:
        tickers |= set(prices_by_date[d].keys())
    result: Dict[str, list[float]] = {t: [] for t in tickers}
    for t in tickers:
        for d in dates:
            result[t].append(float(prices_by_date[d].get(t, 0.0)))
    return result


def load_eps_csv(path: str) -> Dict[str, Dict[str, float]]:
    """Return: {date:{ticker: eps_estimate}}."""
    out: Dict[str, Dict[str, float]] = {}
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            d = row["date"]
            t = row["ticker"]
            v = float(row["eps_estimate"])
            out.setdefault(d, {})[t] = v
    return out


def pivot_eps_to_ticker_series(eps_by_date: Dict[str, Dict[str, float]]) -> Dict[str, list[float]]:
    dates = sorted(eps_by_date.keys())
    tickers = set()
    for d in dates:
        tickers |= set(eps_by_date[d].keys())
    result: Dict[str, list[float]] = {t: [] for t in tickers}
    for t in tickers:
        for d in dates:
            result[t].append(float(eps_by_date[d].get(t, 0.0)))
    return result


def load_fundamentals_csv(path: str) -> Dict[str, Dict[str, float]]:
    """Return FINAL ROW PER TICKER (latest) → {ticker:{gpm,accruals,leverage}}."""
    latest: Dict[str, Tuple[str, Dict[str, float]]] = {}
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            d = row["date"]
            t = row["ticker"]
            vals = {
                "gpm": float(row.get("gpm", 0.0)),
                "accruals": float(row.get("accruals", 0.0)),
                "leverage": float(row.get("leverage", 0.0)),
            }
            if t not in latest or d > latest[t][0]:
                latest[t] = (d, vals)
    return {t: v for t, (_, v) in latest.items()}


def load_sector_map_csv(path: str) -> Dict[str, str]:
    """Optional helper: CSV schema: ticker,sector"""
    out: Dict[str, str] = {}
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            out[row["ticker"]] = row["sector"]
    return out
