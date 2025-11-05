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

try:
    import pandas as pd  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    pd = None  # type: ignore

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

st.sidebar.header("Live Data (Phase 4)")
tickers_text = st.sidebar.text_input("Tickers (comma-separated)", "AAPL,MSFT,GOOGL")
provider_choice = st.sidebar.selectbox("Provider", ["yfinance (no key)", "Polygon (API key)"])

# Build Snapshot
if st.sidebar.button("Build Snapshot"):
    T = [t.strip().upper() for t in tickers_text.split(",") if t.strip()]
    try:
        if provider_choice.startswith("yfinance"):
            from src.data.providers.yf_provider import YFinanceProvider

            prov = YFinanceProvider()
        else:
            from src.data.providers.polygon_provider import PolygonProvider

            prov = PolygonProvider()

        prices_by_date = prov.fetch_prices_weekly(T, lookback_weeks=156)
        eps_by_date = prov.fetch_eps_weekly(T, lookback_weeks=156)
        fundamentals_latest = prov.fetch_fundamentals_latest(T)
        sector_map = prov.fetch_sector_map(T)

        from src.data.snapshot import write_snapshot

        snap_path = write_snapshot(
            prices_by_date, eps_by_date, fundamentals_latest, sector_map
        )
        st.success(f"Snapshot written: {snap_path}")
    except ImportError as e:
        st.error(f"Provider not available: {e}")
    except NotImplementedError as e:
        st.warning(f"Provider feature not implemented: {e}")
    except Exception as e:
        st.error(f"Snapshot build failed: {e.__class__.__name__}: {e}")

# Run Snapshot Backtest
from src.data.snapshot import list_snapshots, load_snapshot

snaps = list_snapshots()
snap_sel = st.sidebar.selectbox("Use Snapshot", snaps if snaps else ["(none)"])
if st.sidebar.button("Run Snapshot Backtest") and snaps:
    try:
        from src.engine.backtest_pd import run_backtest_pd

        pb, eb, fb, sm = load_snapshot(snap_sel)
        out_path = run_backtest_pd(
            pb,
            eb,
            fb,
            sm,
            weeks=52,
            data_snapshot_id=snapshot or "SNAPSHOT_LIVE",
        )
        st.success(f"Snapshot backtest created at: {out_path}")
    except ImportError:
        st.error("pandas not available on this runtime.")
    except Exception as e:
        st.error(f"Snapshot backtest failed: {e.__class__.__name__}: {e}")

st.sidebar.header("📊 Factor Telemetry")
tele_disabled = pd is None
if tele_disabled:
    st.sidebar.warning("pandas not available; factor telemetry disabled.")
tele_snapshot = st.sidebar.selectbox(
    "Snapshot for telemetry",
    list_snapshots() or ["(none)"],
    disabled=tele_disabled,
)
available_factors = [
    "mom_12_1",
    "mom_velocity",
    "eps_rev_4_12",
    "quality_q",
    "low_vol_26w",
]
selected_factors = st.sidebar.multiselect(
    "Select factors",
    available_factors,
    default=["mom_12_1", "eps_rev_4_12"],
    disabled=tele_disabled,
)

if st.sidebar.button("Run Factor IC", disabled=tele_disabled):
    try:
        from src.engine.factor_telemetry import run_factor_ic_telemetry

        if tele_snapshot == "(none)":
            st.warning("No snapshots available. Build or load a snapshot first.")
        else:
            pb, eb, fb, sm = load_snapshot(tele_snapshot)
            out_path = run_factor_ic_telemetry(
                pb,
                eb,
                fb,
                selected_factors,
                data_snapshot_id=tele_snapshot.split("/")[-1],
            )
            st.success(f"Factor telemetry created at: {out_path}")
    except ImportError:
        st.error("pandas/scipy not available for factor telemetry.")
    except Exception as e:
        st.error(f"Factor telemetry failed: {e.__class__.__name__}: {e}")

with st.expander("📈 Factor IC (latest run)"):
    try:
        import json
        import pathlib

        import pandas as pd  # type: ignore

        runs_dir = pathlib.Path("runs")
        candidates = sorted((p for p in runs_dir.glob("*/*/factors") if p.is_dir()))
        if not candidates:
            st.info("No factor runs yet.")
        else:
            froot = candidates[-1]
            st.caption(f"Latest factor artifacts: {froot}")
            fdirs = sorted([d for d in froot.iterdir() if d.is_dir()])
            tabs = st.tabs([d.name for d in fdirs] or ["(none)"])
            for tab, d in zip(tabs, fdirs):
                with tab:
                    ic_file = d / "ic_series.json"
                    sum_file = d / "ic_summary.json"
                    if ic_file.exists():
                        ser = json.loads(ic_file.read_text(encoding="utf-8"))
                        series = pd.Series(
                            {
                                k: (float(v) if v not in ("NaN", "Infinity", "-Infinity") else float("nan"))
                                for k, v in ser.items()
                            }
                        )
                        st.line_chart(series)
                    if sum_file.exists():
                        summary = json.loads(sum_file.read_text(encoding="utf-8"))
                        st.json(summary)
    except Exception as e:
        st.warning(f"Could not render factor IC preview: {e}")

st.sidebar.header("🧮 Adaptive Weights")
alpha_ic = st.sidebar.slider(
    "IC-EMA alpha (0.05–0.5)", min_value=0.05, max_value=0.5, value=0.2, step=0.05
)
factors_for_weights = st.sidebar.multiselect(
    "Factors to weight",
    ["mom_12_1", "mom_velocity", "eps_rev_4_12", "quality_q", "low_vol_26w"],
    default=["mom_12_1", "mom_velocity", "quality_q", "low_vol_26w"],
)

if st.sidebar.button("Compute Adaptive Weights"):
    try:
        from src.engine.load_ic_artifacts import load_latest_ic_series
        from src.engine.weights_and_attr import run_factor_weighting_and_attr

        ic_by_factor = load_latest_ic_series(factor_names=factors_for_weights)
        if not ic_by_factor:
            st.warning("No factor IC artifacts found. Run Factor IC first.")
        else:
            bench = {}
            out_dir = run_factor_weighting_and_attr(
                ic_series_by_factor=ic_by_factor,
                bench_weekly_returns=bench,
                factor_names=factors_for_weights,
                data_snapshot_id=snapshot or "SNAPSHOT",
                alpha=alpha_ic,
            )
            st.success(f"Adaptive weights created at: {out_dir}")
    except Exception as e:
        st.error(f"Adaptive weighting failed: {e.__class__.__name__}: {e}")

with st.expander("📑 Factor Tear-Sheet (latest weights)"):
    import pathlib, json
    runs_dir = pathlib.Path("runs")
    candidates = sorted((p for p in runs_dir.glob("*/*/factors/weights") if p.is_dir()))
    if not candidates:
        st.info("No adaptive weights runs yet.")
    else:
        wdir = candidates[-1]
        st.caption(f"Artifacts: {wdir}")
        files = {
            name: wdir / name
            for name in ["weights.json", "ic_ema.json", "gates.json", "contrib.json", "summary.json"]
        }

        # Summary
        try:
            summary = json.loads(files["summary.json"].read_text(encoding="utf-8"))
            st.subheader("Summary")
            st.json(summary)
        except Exception as e:
            st.warning(f"Could not read summary: {e}")

        # Latest snapshot table
        try:
            import pandas as pd  # type: ignore

            weights = json.loads(files["weights.json"].read_text(encoding="utf-8"))
            ic_ema  = json.loads(files["ic_ema.json"].read_text(encoding="utf-8"))
            gates   = json.loads(files["gates.json"].read_text(encoding="utf-8"))
            contrib = json.loads(files["contrib.json"].read_text(encoding="utf-8"))

            last_date = sorted(weights.keys())[-1]

            # Default missing gates to 1 for display
            _g = gates.get(last_date, {}) if isinstance(gates, dict) else {}
            g_last = {}
            for k in weights[last_date].keys():
                v = _g.get(k, 1)
                try:
                    g_last[k] = int(v)
                except Exception:
                    g_last[k] = 1

            df = pd.DataFrame(
                {
                    "weight": weights[last_date],
                    "ic_ema": ic_ema.get(last_date, {}),
                    "gate": g_last,
                    "weighted_ic": contrib.get(last_date, {}),
                }
            ).T.T

            st.subheader(f"Latest snapshot — {last_date}")
            st.table(df)
        except Exception as e:
            st.warning(f"Could not render latest snapshot: {e}")

        # Downloads
        st.subheader("Downloads")
        for k, p in files.items():
            if p.exists():
                st.download_button(label=f"Download {k}", data=p.read_bytes(), file_name=k)

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

with st.expander("🧪 Run details (latest)"):
    runs_dir = pathlib.Path("runs")
    candidates = sorted((p for p in runs_dir.glob("*/*") if p.is_dir()))
    if not candidates:
        st.info("No runs available.")
    else:
        latest = candidates[-1]
        st.write(f"Latest run: **{latest.name}** — {latest.parent.name}")

        metrics_data = None
        mfile = latest / "metrics.json"
        if mfile.exists():
            try:
                metrics_data = json.loads(mfile.read_text(encoding="utf-8"))
                st.subheader("Metrics")
                st.json(metrics_data)
            except Exception as e:
                st.warning(f"Could not parse metrics.json: {e}")

        def _as_float(x):
            try:
                return float(x)
            except Exception:
                return float("nan")

        if metrics_data:
            sortino_val = _as_float(metrics_data.get("Sortino", "NaN"))
            maxdd = _as_float(metrics_data.get("MaxDD", "NaN"))
            tmean = _as_float(metrics_data.get("Turnover_mean", "NaN"))
            flags = []
            if maxdd == 0.0:
                flags.append("MaxDD is 0 (toy/synthetic data often produces this).")
            if not math.isfinite(sortino_val):
                flags.append("Sortino is non-finite (no downside returns).")
            if tmean == 0.0:
                flags.append("Turnover is 0 (weights likely unchanged).")
            if flags:
                st.warning(" • ".join(flags))

        eq_file = latest / "equity.json"
        if eq_file.exists():
            try:
                eq = json.loads(eq_file.read_text(encoding="utf-8"))
                st.subheader("Equity")
                st.line_chart(eq)
            except Exception as e:
                st.warning(f"Could not parse equity.json: {e}")

        wfile = latest / "weights.csv"
        if wfile.exists():
            if pd is None:
                st.info("Install pandas to view turnover diagnostics.")
            else:
                try:
                    wdf = pd.read_csv(wfile, index_col=0)
                    if len(wdf) > 1:
                        t_series = (wdf.diff().abs().sum(axis=1) / 2.0).fillna(0.0)
                        st.subheader("Turnover per period")
                        st.line_chart(t_series.values.tolist())
                except Exception as e:
                    st.warning(f"Could not compute turnover from weights.csv: {e}")

        hfile = latest / "holdings_last.json"
        if hfile.exists():
            try:
                hold = json.loads(hfile.read_text(encoding="utf-8"))
                st.subheader("Final holdings")
                if hold:
                    if pd is not None:
                        holdings_df = pd.DataFrame(
                            list(hold.items()), columns=["Ticker", "weight"]
                        ).set_index("Ticker")
                        st.table(holdings_df)
                    else:
                        st.json(hold)
                else:
                    st.caption("Empty holdings.")
            except Exception as e:
                st.warning(f"Could not parse holdings_last.json: {e}")

        st.subheader("Downloads")
        for fname in ("metrics.json", "returns.json", "equity.json", "weights.csv", "holdings_last.json"):
            fp = latest / fname
            if fp.exists():
                st.download_button(
                    label=f"Download {fname}",
                    data=fp.read_bytes(),
                    file_name=fname,
                )
