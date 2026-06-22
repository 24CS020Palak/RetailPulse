"""
RetailPulse Dashboard - Customer Dashboard Page
==================================================
Surfaces customer segmentation (Day 3) and churn risk (Day 9) insights.
Per the project plan, the FULL churn risk dashboard with detailed SHAP
visuals is a Day 17 task ("Customer segmentation and churn risk
dashboard") - this Day 15 skeleton lays out the PAGE STRUCTURE and
basic charts, to be expanded later.
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utils.data_loader import (
    safe_load, load_rfm_clustered, load_churn_features,
    load_churn_test_predictions, load_json_metrics
)

st.title("👥 Customer Dashboard")
st.caption("RFM segmentation and churn risk overview")

rfm = safe_load(load_rfm_clustered)

if rfm is None:
    st.stop()

# ============================================================
# SEGMENT OVERVIEW
# ============================================================
st.subheader("Customer Segments (RFM-based)")

segment_col1, segment_col2 = st.columns([1, 2])

with segment_col1:
    segment_counts = rfm["KMeans_Label"].value_counts() if "KMeans_Label" in rfm.columns else None
    if segment_counts is not None:
        for segment, count in segment_counts.items():
            pct = 100 * count / len(rfm)
            st.metric(f"Segment {segment}",f"{count:,}",f"{pct:.1f}% of customers")
    else:
        st.info("Segment labels not found - run Day 3 notebook first.")

with segment_col2:
    if "KMeans_Label" in rfm.columns:
        st.bar_chart(rfm["KMeans_Label"].value_counts())

st.divider()

# ============================================================
# RFM SCATTER VIEW (Recency vs Monetary, colored by segment)
# ============================================================
st.subheader("Recency vs Monetary by Segment")

if {"Recency", "Monetary", "KMeans_Label"}.issubset(rfm.columns):
    # st.scatter_chart is Streamlit's native scatter plot widget -
    # no need for matplotlib here, keeps the page lightweight and
    # automatically interactive (zoom/pan/tooltip) out of the box
    st.scatter_chart(
        rfm,
        x="Recency",
        y="Monetary",
        color="KMeans_Label",
        size=None,
    )
else:
    st.info("RFM columns not found - run Day 3 notebook first.")

st.divider()

# ============================================================
# CHURN RISK OVERVIEW
# ============================================================
st.subheader("Churn Risk Overview")

churn_metrics = load_json_metrics("churn_metrics.json")
churn_test_preds = safe_load(load_churn_test_predictions)

if churn_metrics is not None:
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.metric("Model AUC-ROC", f"{churn_metrics['auc_roc']:.4f}")
    with m_col2:
        st.metric("Precision @ Top 20%", f"{churn_metrics['precision_at_top20']:.4f}")
    with m_col3:
        st.metric("Observed Churn Rate", f"{churn_metrics['churn_rate']*100:.1f}%")

    if churn_test_preds is not None:
        st.markdown("**Highest Churn-Risk Customers (Test Set)**")
        top_risk = churn_test_preds.sort_values("pred_proba", ascending=False).head(10)
        st.dataframe(top_risk, width='stretch')
else:
    st.info("Churn model metrics not found - run Day 9 notebook first.")

st.divider()

with st.expander("View full RFM table"):
    st.dataframe(rfm, width='stretch')
