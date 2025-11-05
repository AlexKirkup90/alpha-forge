from __future__ import annotations

import csv
import re
from typing import Dict, Tuple

# ---- CSV Schemas ----
# prices.csv: date,ticker,close
# eps.csv:    date,ticker,eps_estimate
# funda.csv:  date,ticker,gpm,accruals,leverage
#
# Constraints: weekly data or daily that you will pre-aggregate to weekly outside.

# Canonical headers with known aliases that we normalise into the canonical key.
# NOTE: aliases are listed in addition to the canonical key.
_CANONICAL_ALIASES: Dict[str, tuple[str, ...]] = {
    "date": ("date", "as_of", "timestamp", "datetime"),
    "ticker": ("ticker", "symbol", "ticker_symbol"),
    "close": (
        "close",
        "closing_price",
        "close_price",
        "price",
        "adj_close",
        "adjusted_close",
        "adjclose",
    ),
    "eps_estimate": ("eps_estimate", "eps", "estimate", "eps_est"),
    "gpm": ("gpm", "gross_profit_margin"),
    "accruals": ("accruals", "accrual"),
    "leverage": ("leverage", "debt_to_assets", "debt_to_equity"),
    "sector": ("sector", "industry"),
}


def _norm(s: str) -> str:
    if s is None:
        return ""
    # strip BOM on first field and collapse whitespace/punctuation into underscores
    cleaned = s.replace("\ufeff", "").strip().lower()
    cleaned = re.sub(r"[\s\-/]+", "_", cleaned)
    cleaned = re.sub(r"__+", "_", cleaned).strip("_")
    return cleaned


# Build alias lookups after _norm is defined.
_ALIAS_LOOKUP = {
    _norm(alias): canonical
    for canonical, aliases in _CANONICAL_ALIASES.items()
    for alias in aliases
    if alias != canonical
}


def _normalize_row(row: dict) -> dict:
    normalized = {}
    for key, value in row.items():
        nk = _norm(key)
        if not nk:
            continue
        normalized[nk] = value
    # Inject canonical keys for aliases if available.
    for alias_norm, canonical in _ALIAS_LOOKUP.items():
        if alias_norm in normalized and canonical not in normalized:
            normalized[canonical] = normalized[alias_norm]
    return normalized


def _lookup(row: dict, *keys: str, raw: dict | None = None, rownum: int | None = None) -> str:
    for key in keys:
        nk = _norm(key)
        if nk in row:
            return row[nk]
    attempted = ", ".join(keys)
    normalized_attempts = ", ".join(_norm(k) for k in keys)
    available_raw = ", ".join(str(k) for k in (raw or {}).keys()) or "<none>"
    available_normalized = ", ".join(sorted(row.keys())) or "<none>"
    location = f" on row {rownum}" if rownum is not None else ""
    raise KeyError(
        "missing column(s) "
        f"{attempted}{location} (normalized: {normalized_attempts}). "
        f"Available columns: {available_raw} (normalized: {available_normalized})"
    )


def load_prices_csv(path: str) -> Dict[str, Dict[str, float]]:
    """Return: {date: {ticker: close}} (wide-by-date mapping for fast alignment)."""
    out: Dict[str, Dict[str, float]] = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, raw in enumerate(reader, start=2):  # include header line in count
            nrow = _normalize_row(raw)
            try:
                d = _lookup(nrow, "date", raw=raw, rownum=idx)
                t = _lookup(nrow, "ticker", raw=raw, rownum=idx)
                c = float(_lookup(nrow, "close", raw=raw, rownum=idx))
            except KeyError as exc:
                raise ValueError(f"prices.csv schema error: {exc}") from None
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
        reader = csv.DictReader(f)
        for idx, raw in enumerate(reader, start=2):
            nrow = _normalize_row(raw)
            try:
                d = _lookup(nrow, "date", raw=raw, rownum=idx)
                t = _lookup(nrow, "ticker", raw=raw, rownum=idx)
                v = float(_lookup(nrow, "eps_estimate", raw=raw, rownum=idx))
            except KeyError as exc:
                raise ValueError(f"eps.csv schema error: {exc}") from None
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
        reader = csv.DictReader(f)
        for idx, raw in enumerate(reader, start=2):
            nrow = _normalize_row(raw)
            try:
                d = _lookup(nrow, "date", raw=raw, rownum=idx)
                t = _lookup(nrow, "ticker", raw=raw, rownum=idx)
                g = float(_lookup(nrow, "gpm", raw=raw, rownum=idx))
                a = float(_lookup(nrow, "accruals", raw=raw, rownum=idx))
                lv = float(_lookup(nrow, "leverage", raw=raw, rownum=idx))
            except KeyError as exc:
                raise ValueError(f"funda.csv schema error: {exc}") from None
            vals = {"gpm": g, "accruals": a, "leverage": lv}
            if t not in latest or d > latest[t][0]:
                latest[t] = (d, vals)
    return {t: v for t, (_, v) in latest.items()}


def load_sector_map_csv(path: str) -> Dict[str, str]:
    """Optional helper: CSV schema: ticker,sector"""
    out: Dict[str, str] = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            nrow = _normalize_row(raw)
            t = nrow.get("ticker")
            s = nrow.get("sector") or "UNK"
            if t:
                out[t] = s
    return out
