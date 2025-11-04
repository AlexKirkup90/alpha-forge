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

st.set_page_config(page_title="alpha-forge", layout="wide")
st.title("alpha-forge — Backtest Console (Step 1)")

st.sidebar.header("Run Config (placeholder)")
snapshot = st.sidebar.text_input("Data snapshot ID", "SNAPSHOT_DEMO")
run_id = st.sidebar.text_input("Run ID", datetime.utcnow().strftime("%Y%m%d-%H%M%S"))
gross = st.sidebar.checkbox("Show Gross", value=True)
net = st.sidebar.checkbox("Show Net", value=True)

st.subheader("Run Registry")
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
