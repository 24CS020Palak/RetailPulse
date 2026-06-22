"""
RetailPulse Dashboard - Inventory Dashboard Page
===================================================
Surfaces the Day 10 ABC classification and reorder recommendation
outputs. Per the project plan, the full "Inventory optimization
recommendations UI" with deeper interactivity is a Day 18 deliverable -
this Day 15 skeleton lays out the page structure with the core tables
and charts already wired up.
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utils.data_loader import (
    safe_load, load_inventory_recommendations,
    load_inventory_parameters, load_abc_classification
)

st.title("📦 Inventory Dashboard")
st.caption("ABC classification and reorder recommendations")

recommendations = safe_load(load_inventory_recommendations)
parameters = safe_load(load_inventory_parameters)
abc_data = safe_load(load_abc_classification)

if recommendations is None:
    st.stop()

# ============================================================
# ABC CLASSIFICATION SUMMARY
# ============================================================
st.subheader("ABC Product Classification")

if abc_data is not None:
    abc_summary = abc_data.groupby("ABC_Class").agg(
        NumProducts=("StockCode", "count"),
        TotalRevenue=("TotalRevenue", "sum")
    ).reset_index()
    abc_summary["PctOfRevenue"] = 100 * abc_summary["TotalRevenue"] / abc_summary["TotalRevenue"].sum()

    col1, col2, col3 = st.columns(3)
    for col, (_, row) in zip([col1, col2, col3], abc_summary.iterrows()):
        with col:
            st.metric(
                f"Class {row['ABC_Class']}",
                f"{int(row['NumProducts']):,} products",
                f"{row['PctOfRevenue']:.1f}% of revenue"
            )
else:
    st.info("ABC classification data not found - run Day 10 notebook first.")

st.divider()

# ============================================================
# REORDER RECOMMENDATIONS TABLE
# ============================================================
st.subheader("Reorder Recommendations (Top Class A Products)")

st.dataframe(
    recommendations[[
        "StockCode", "Description", "HistoricalAvgDailyDemand",
        "ForecastedDailyDemand", "RecommendedSafetyStock",
        "RecommendedReorderPoint", "RecommendedOrderQty"
    ]],
    width='stretch'
)

st.divider()

# ============================================================
# DEMAND VS SAFETY STOCK CHART
# ============================================================
if parameters is not None:
    st.subheader("Safety Stock by Product")
    chart_data = parameters.set_index("StockCode")[["SafetyStock_opt", "ReorderPoint_opt"]]
    chart_data.columns = ["Safety Stock", "Reorder Point"]
    st.bar_chart(chart_data)

st.divider()

# ============================================================
# PRODUCT-LEVEL DRILL-DOWN
# ============================================================
st.subheader("Product Drill-Down")

product_options = recommendations["StockCode"].tolist()
selected_product = st.selectbox("Select a product", product_options)

product_row = recommendations[recommendations["StockCode"] == selected_product].iloc[0]

d_col1, d_col2, d_col3 = st.columns(3)
with d_col1:
    st.metric("Historical Daily Demand", f"{product_row['HistoricalAvgDailyDemand']:.1f} units")
with d_col2:
    st.metric("Forecasted Daily Demand", f"{product_row['ForecastedDailyDemand']:.1f} units")
with d_col3:
    st.metric("Recommended Order Qty", f"{product_row['RecommendedOrderQty']:.0f} units")

st.info(f"**Action:** {product_row['Action']}")
