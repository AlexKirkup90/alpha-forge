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

import streamlit as st

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
