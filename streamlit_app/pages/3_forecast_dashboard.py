"""
RetailPulse Dashboard - Forecast Dashboard Page
==================================================
Visualizes the Day 8 hybrid Prophet+LSTM forecast. The full "what-if
analysis" tool is officially a Day 16 deliverable per the project plan
("Demand forecasting visualizations and what-if analysis") - this Day 15
skeleton includes a BASIC interactive alpha slider as a starting point,
which Day 16 can build on top of.
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utils.data_loader import safe_load, load_hybrid_forecast_results, load_json_metrics

st.title("📈 Forecast Dashboard")
st.caption("Hybrid Prophet + LSTM demand forecasting")

results = safe_load(load_hybrid_forecast_results)
hybrid_config = load_json_metrics("hybrid_config.json")

if results is None:
    st.stop()

# ============================================================
# MODEL PERFORMANCE METRICS
# ============================================================
st.subheader("Model Performance")

if hybrid_config is not None:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Prophet MAPE", f"{hybrid_config['prophet_mape']:.2f}%")
    with col2:
        st.metric("LSTM MAPE", f"{hybrid_config['lstm_mape']:.2f}%")
    with col3:
        st.metric("Hybrid MAPE", f"{hybrid_config['hybrid_mape']:.2f}%",
                   help="Target: <= 12%")

st.divider()

# ============================================================
# WHAT-IF: INTERACTIVE BLENDING WEIGHT SLIDER
# ============================================================
# This is the simplest possible "what-if" interaction: let the user
# drag the Prophet/LSTM blend weight (alpha) and see the resulting
# hybrid forecast and MAPE update LIVE. Streamlit re-runs this script
# top-to-bottom every time the slider moves, recomputing everything
# below this point - this is the core mental model for how ALL
# Streamlit interactivity works, not just this slider.

st.subheader("What-If: Adjust the Forecast Blend")

default_alpha = hybrid_config["alpha"] if hybrid_config else 0.5

alpha = st.slider(
    "Blend weight (alpha): 1.0 = pure Prophet, 0.0 = pure LSTM",
    min_value=0.0, max_value=1.0, value=float(default_alpha), step=0.05
)

results["whatif_pred"] = alpha * results["prophet_pred"] + (1 - alpha) * results["lstm_pred"]


def mape(actual, predicted):
    import numpy as np
    actual = actual.to_numpy()
    predicted = predicted.to_numpy()
    mask = actual != 0
    return (abs((actual[mask] - predicted[mask]) / actual[mask])).mean() * 100


whatif_mape = mape(results["actual"], results["whatif_pred"])
st.metric("Resulting MAPE at this blend", f"{whatif_mape:.2f}%")

st.divider()

# ============================================================
# FORECAST CHART
# ============================================================
st.subheader("Forecast vs Actual (Test Period)")

chart_data = results.set_index("ds")[["actual", "prophet_pred", "lstm_pred", "whatif_pred"]]
chart_data.columns = ["Actual", "Prophet", "LSTM", "Your Blend"]
st.line_chart(chart_data)

st.divider()

with st.expander("View full forecast results table"):
    st.dataframe(results, width='stretch')
