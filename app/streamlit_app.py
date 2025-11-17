import streamlit as st
import pandas as pd
import time

# --- ensure 'src' is importable when not installed in editable mode ---
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
# ---------------------------------------------------------------------

from src.app_logic.assessment import assess_market_conditions
from src.app_logic.portfolio import generate_portfolio


# --- Streamlit App UI ---

st.set_page_config(page_title="alpha-forge", layout="wide")
st.title("alpha-forge Portfolio Generator")

# Initialize session state to hold results
if "market_assessment" not in st.session_state:
    st.session_state.market_assessment = None
if "generated_portfolio" not in st.session_state:
    st.session_state.generated_portfolio = None

# --- Step 1: Market Assessment ---

st.header("Step 1: Assess Market Conditions")
st.markdown(
    "Click this button to analyze recent market data. The system will identify the "
    "most effective investment factors (like Momentum, Quality, etc.) to use for "
    "portfolio construction."
)

if st.button("Assess Market", type="primary"):
    with st.spinner("Running market analysis... This may take a moment."):
        try:
            st.session_state.market_assessment = assess_market_conditions()
        except Exception as e:
            st.error(f"Market assessment failed: {e}")
            st.session_state.market_assessment = None

    st.session_state.generated_portfolio = None  # Reset portfolio if assessment is re-run

# Display assessment results if available
if st.session_state.market_assessment:
    st.success("Market Assessment Complete!")
    st.info(st.session_state.market_assessment["summary"])

    # --- Step 2: Portfolio Generation ---

    st.header("Step 2: Generate Portfolio")
    st.markdown(
        "Based on the assessment, click below to generate a diversified portfolio "
        "designed to maximize alpha and minimize drawdown."
    )

    if st.button("Generate Portfolio", type="primary"):
        with st.spinner("Constructing portfolio... This may take a few moments."):
            try:
                st.session_state.generated_portfolio = generate_portfolio(
                    st.session_state.market_assessment["best_factors"]
                )
            except Exception as e:
                st.error(f"Portfolio generation failed: {e}")
                st.session_state.generated_portfolio = None

# Display portfolio if available
if st.session_state.generated_portfolio is not None:
    st.success("Portfolio Generation Complete!")
    st.dataframe(st.session_state.generated_portfolio, use_container_width=True)

    st.download_button(
        label="Download Portfolio as CSV",
        data=st.session_state.generated_portfolio.to_csv(index=False).encode('utf-8'),
        file_name="alpha_forge_portfolio.csv",
        mime="text/csv",
    )

st.sidebar.info("alpha-forge v1.0")
