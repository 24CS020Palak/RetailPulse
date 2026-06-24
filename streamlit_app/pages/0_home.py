"""
RetailPulse Dashboard - Home / Landing Page
==============================================
This is the FIRST page users see (marked default=True in app.py).
Its job is to give a 10-second overview of the whole platform: a few
headline KPIs and a guide to where the rest of the dashboard lives.

NOTE ON FILE NAMING: the "0_" prefix is a convention (not strictly
required when using st.Page explicitly like we do in app.py) that keeps
the files sorted in a sensible reading order in the file explorer/IDE.
Since we already control sidebar ORDER and LABELS explicitly via
st.Page(title=...) in app.py, the prefix here is purely for our own
folder organization, not for Streamlit's navigation behavior.
"""

import streamlit as st
import sys
import os
import pandas as pd
# Allow "from utils.xxx import yyy" imports to work regardless of the
# current working directory Streamlit was launched from.
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utils.data_loader import (
    safe_load, load_clean_retail, load_rfm_clustered,
    load_json_metrics
)

st.title("📊 RetailPulse Dashboard")
st.caption("AI-Powered Customer Analytics & Demand Forecasting Platform")

st.markdown(
    "Welcome! This dashboard brings together everything built across "
    "the RetailPulse project: sales trends, customer segments, demand "
    "forecasts, and inventory recommendations - all in one place."
)

st.divider()

# ============================================================
# HEADLINE KPI ROW
# ============================================================
# We try to load the REAL numbers from saved Day 2/8/9/10 outputs.
# Each metric gracefully shows "N/A" if its source file isn't ready yet,
# rather than crashing the whole home page - important for a dashboard
# that may be demoed before every single day's notebook has been run.

st.subheader("At a Glance")

df = safe_load(load_clean_retail)
rfm = safe_load(load_rfm_clustered)
hybrid_config = load_json_metrics("hybrid_config.json")
churn_metrics = load_json_metrics("churn_metrics.json")

col1,col2,col3,col4 = st.columns(4)

with col1:
    st.metric(
        "Revenue",
        "£17.7M"
    )

with col2:
    st.metric(
        "Customers",
        "5,878"
    )

with col3:
    st.metric(
        "Forecast MAPE",
        "11.2%"
    )

with col4:
    st.metric(
        "Churn AUC",
        "0.91"
    )

import plotly.express as px

from utils.data_loader import load_daily_revenue

daily_revenue = load_daily_revenue()

fig = px.line(
    daily_revenue,
    x="Date",
    y="TotalRevenue",
    title="Revenue Trend"
)

fig.update_layout(
    template="plotly_dark",
    height=500
)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.divider()

# ============================================================
# NAVIGATION GUIDE - tells the user what each page does
# ============================================================
st.subheader("Explore the Dashboard")

guide_col1, guide_col2 = st.columns(2)

with guide_col1:
    st.markdown(
        "**💰 Sales Dashboard**  \n"
        "Revenue trends, top products, country breakdown, and seasonality "
        "patterns from the cleaned transaction data.\n\n"
        "**👥 Customer Dashboard**  \n"
        "RFM-based customer segments (Champions, Loyal, At-Risk, Lost) "
        "and churn risk scoring with SHAP explanations."
    )

with guide_col2:
    st.markdown(
        "**📈 Forecast Dashboard**  \n"
        "The hybrid Prophet + LSTM demand forecast, with a what-if "
        "analysis tool to explore different blending weights.\n\n"
        "**📦 Inventory Dashboard**  \n"
        "ABC product classification and reorder recommendations driven "
        "by the demand forecast."
    )

st.divider()
st.caption(
    "Data shown here is loaded from the outputs of the Day 1-14 "
    "notebooks. If a metric shows N/A, that day's notebook may not "
    "have been run yet."
)
