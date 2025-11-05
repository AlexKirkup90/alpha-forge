import json
import pathlib
import sys
from datetime import datetime

# --- ensure 'src' is importable when not installed in editable mode ---
ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
# ---------------------------------------------------------------------

import math

import streamlit as st

from src.engine.backtest import WeeklyBatch, run_walkforward
from src.engine.weekly import WeeklyParams, run_weekly
from src.metrics.diagnostics import (
    breadth,
    cross_sectional_ic,
    hit_rate,
    hhi,
    quintile_spread,
)
from src.telemetry.demo_run import write_demo_run

st.set_page_config(page_title="alpha-forge", layout="wide")
st.title("alpha-forge — Backtest Console (Step 1)")

st.sidebar.header("Run Config (placeholder)")
snapshot = st.sidebar.text_input("Data snapshot ID", "SNAPSHOT_DEMO")
run_id = st.sidebar.text_input("Run ID", datetime.utcnow().strftime("%Y%m%d-%H%M%S"))
gross = st.sidebar.checkbox("Show Gross", value=True)
net = st.sidebar.checkbox("Show Net", value=True)


if st.sidebar.button("Create demo run"):
    out_path = write_demo_run(data_snapshot_id=snapshot, run_id=run_id or None)
    st.success(f"Demo run created at: {out_path}")

def _multiweek_demo_batches(weeks: int = 12):
    tickers = ["AAA", "BBB", "CCC"]
    sector_map = {"AAA": "Tech", "BBB": "Finance", "CCC": "Health"}
    base_prices = {"AAA": 50.0, "BBB": 38.0, "CCC": 28.0}
    growth = {"AAA": 0.011, "BBB": 0.007, "CCC": 0.009}
    base_eps = {"AAA": 2.0, "BBB": 1.4, "CCC": 1.1}
    eps_trend = {"AAA": 0.02, "BBB": 0.015, "CCC": 0.017}

    price_history = {t: [] for t in tickers}
    eps_history = {t: [] for t in tickers}
    warmup = 13
    total_points = warmup + weeks + 1

    for step in range(total_points):
        for t in tickers:
            drift = base_prices[t] * (1 + growth[t]) ** step
            seasonal = 1 + 0.01 * math.sin(step / 3.0 + len(t))
            price_history[t].append(drift * seasonal)

            eps_level = base_eps[t] + eps_trend[t] * step
            eps_cycle = 0.04 * math.cos(step / 4.0 + len(t))
            eps_history[t].append(eps_level + eps_cycle)

    batches: list[WeeklyBatch] = []
    for week in range(warmup, warmup + weeks):
        prices = {t: price_history[t][: week + 1] for t in tickers}
        eps = {t: eps_history[t][: week + 1] for t in tickers}
        fundamentals = {
            t: {
                "gpm": 0.45 + 0.01 * (idx + 1) + 0.001 * week,
                "accruals": 0.12 + 0.002 * idx,
                "leverage": 0.25 + 0.001 * (weeks - idx),
            }
            for idx, t in enumerate(tickers)
        }
        next_returns = {
            t: price_history[t][week + 1] / price_history[t][week] - 1.0 for t in tickers
        }
        bench_ret = sum(next_returns.values()) / len(next_returns)
        batches.append(
            WeeklyBatch(
                prices=prices,
                eps=eps,
                fundamentals=fundamentals,
                next_returns=next_returns,
                benchmark={"SPY": bench_ret},
            )
        )

    return batches, sector_map


if st.sidebar.button("Run demo weekly"):
    prices = {
        "AAA": [10, 11, 12, 13, 14, 15],
        "BBB": [10, 9, 9.5, 9.7, 9.9, 10.2],
        "CCC": [5, 5.1, 5.2, 5.3, 5.4, 5.5],
    }
    eps = {
        "AAA": [1, 1, 1, 1.1, 1.2, 1.25],
        "BBB": [1, 1, 0.98, 0.97, 0.96, 0.95],
        "CCC": [0.5, 0.5, 0.51, 0.52, 0.53, 0.54],
    }
    fundamentals = {
        "AAA": {"gpm": 0.6, "accruals": 0.1, "leverage": 0.2},
        "BBB": {"gpm": 0.3, "accruals": 0.2, "leverage": 0.4},
        "CCC": {"gpm": 0.55, "accruals": 0.12, "leverage": 0.25},
    }
    sector = {"AAA": "Tech", "BBB": "Finance", "CCC": "Tech"}
    next_ret = {"AAA": 0.02, "BBB": -0.01, "CCC": 0.015}
    bench = {"SPY": 0.008}

    out_path = run_weekly(
        prices,
        eps,
        fundamentals,
        sector,
        next_ret,
        bench,
        data_snapshot_id=snapshot or "SNAPSHOT_DEMO",
        params=WeeklyParams(top_k=2),
    )
    st.success(f"Weekly demo run created at: {out_path}")

if st.sidebar.button("Run Multi-Week Demo"):
    batches, sector_map = _multiweek_demo_batches(weeks=12)
    out_path, metrics = run_walkforward(
        batches=batches,
        sector_map=sector_map,
        data_snapshot_id=snapshot or "SNAPSHOT_DEMO",
        params=WeeklyParams(top_k=2),
    )
    st.success(f"Multi-week demo run created at: {out_path}")
    st.json(metrics)

import importlib


def _pandas_available():
    try:
        importlib.import_module("pandas")
        return True
    except Exception:
        return False


st.sidebar.subheader("Backtest Mode")
mode = st.sidebar.selectbox("Engine", ["Synthetic (Pure-Python)", "CSV (Pandas)"])

if mode == "CSV (Pandas)":
    st.sidebar.caption("Upload CSVs (prices/eps/funda) — schemas documented in code.")
    prices_file = st.sidebar.file_uploader("prices.csv", type=["csv"])
    eps_file = st.sidebar.file_uploader("eps.csv", type=["csv"])
    funda_file = st.sidebar.file_uploader("funda.csv", type=["csv"])
    sector_text = st.sidebar.text_area("Sector map (ticker,sector) CSV content (optional)")

    if st.sidebar.button("Run CSV backtest"):
        if not _pandas_available():
            st.error("pandas not available on this runtime. Install locally or use Synthetic mode.")
        elif not (prices_file and eps_file and funda_file):
            st.warning("Please upload all three CSVs.")
        else:
            import tempfile

            def _write_temp(data: bytes, suffix: str) -> str:
                tmp = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, encoding="utf-8")
                try:
                    tmp.write(data.decode("utf-8"))
                    return tmp.name
                finally:
                    tmp.close()

            from src.data.adapter import (
                load_eps_csv,
                load_fundamentals_csv,
                load_prices_csv,
                load_sector_map_csv,
            )

            prices_path = _write_temp(prices_file.getvalue(), "_prices.csv")
            eps_path = _write_temp(eps_file.getvalue(), "_eps.csv")
            funda_path = _write_temp(funda_file.getvalue(), "_funda.csv")
            sector_path = None
            out_path = None
            try:
                prices_by_date = load_prices_csv(prices_path)
                eps_by_date = load_eps_csv(eps_path)
                funda_latest = load_fundamentals_csv(funda_path)

                sector_map = {}
                if sector_text.strip():
                    sector_path = _write_temp(sector_text.encode("utf-8"), "_sector.csv")
                    sector_map = load_sector_map_csv(sector_path)

                from src.engine.backtest_pd import run_backtest_pd

                out_path = run_backtest_pd(
                    prices_by_date,
                    eps_by_date,
                    funda_latest,
                    sector_map,
                    weeks=52,
                    data_snapshot_id=snapshot or "CSV_SNAPSHOT",
                )
            except ValueError as e:
                st.error(f"CSV schema problem: {e}")
            except Exception as e:
                st.error(f"CSV backtest failed: {e.__class__.__name__}")
            else:
                st.success(f"CSV backtest created at: {out_path}")
            finally:
                import os

                for p in (prices_path, eps_path, funda_path, sector_path):
                    if not p:
                        continue
                    try:
                        os.unlink(p)
                    except OSError:
                        pass

st.subheader("Run Registry")

with st.expander("🔎 Diagnostics (demo calculation)"):
    demo_factor = {"AAA": 1.0, "BBB": 0.5, "CCC": -0.2, "DDD": 0.8}
    demo_next = {"AAA": 0.02, "BBB": 0.01, "CCC": -0.01, "DDD": 0.015}
    demo_weights = {"AAA": 0.4, "BBB": 0.3, "CCC": 0.2, "DDD": 0.1}
    st.write(
        {
            "IC": cross_sectional_ic(demo_factor, demo_next),
            "HitRate": hit_rate(demo_factor, demo_next),
            "Q5-Q1": quintile_spread(demo_factor, demo_next, 4),
            "Breadth": breadth(demo_weights),
            "HHI": hhi(demo_weights),
        }
    )
runs_dir = pathlib.Path("runs")
if runs_dir.exists():
    for day_dir in sorted(runs_dir.glob("*")):
        for rdir in sorted(day_dir.glob("*")):
            meta = rdir / "run.json"
            metrics = rdir / "metrics.json"
            if meta.exists():
                st.markdown(f"**{rdir.name}** — {day_dir.name}")
                with open(meta, encoding="utf-8") as f:
                    st.code(f.read(), language="json")
                if metrics.exists():
                    with open(metrics, encoding="utf-8") as f:
                        st.json(json.load(f))
                st.divider()
else:
    st.info("No runs yet. Once backtests write artifacts, they will appear here.")

with st.expander("📈 Equity preview (latest run)"):
    try:
        runs_dir = pathlib.Path("runs")
        candidates = sorted((p for p in runs_dir.glob("*/*") if p.is_dir()))
        if candidates:
            latest = candidates[-1]
            eq_file = latest / "equity.json"
            if eq_file.exists():
                series = json.loads(eq_file.read_text(encoding="utf-8"))
                st.line_chart(series)
            else:
                st.info("No equity.json found in latest run.")
        else:
            st.info("No runs found.")
    except Exception as e:
        st.warning(f"Preview unavailable: {e}")
