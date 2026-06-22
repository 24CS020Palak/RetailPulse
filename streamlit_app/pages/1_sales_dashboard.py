"""
RetailPulse Dashboard - Sales Dashboard Page
===============================================
Surfaces the core sales/revenue insights from the cleaned transaction
data (Day 2 output). This is intentionally a SKELETON for Day 15 - full
interactivity (filters, drill-downs) gets layered on in later Week 3
days per the project plan (Day 16: demand forecasting visuals and
what-if analysis is a SEPARATE page's job; this page focuses on
historical sales, not forecasts).
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utils.data_loader import safe_load, load_clean_retail, load_daily_revenue

st.title("💰 Sales Dashboard")
st.caption("Historical revenue trends, product performance, and seasonality")

df = safe_load(load_clean_retail)
daily = safe_load(load_daily_revenue)

if df is None:
    st.stop()   # st.stop() halts execution of the REST of this page only,
                # the rest of the app (sidebar, other pages) is unaffected

# ============================================================
# SIDEBAR FILTERS (page-specific - only appears on this page,
# since it's defined inside this page's own script)
# ============================================================
st.sidebar.subheader("Sales Filters")

min_date = df["InvoiceDate"].min().date()
max_date = df["InvoiceDate"].max().date()

date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

countries = ["All"] + sorted(df["Country"].unique().tolist())
selected_country = st.sidebar.selectbox("Country", countries)

# Apply filters
filtered_df = df.copy()
if len(date_range) == 2:
    start, end = date_range
    filtered_df = filtered_df[
        (filtered_df["InvoiceDate"].dt.date >= start) &
        (filtered_df["InvoiceDate"].dt.date <= end)
    ]
if selected_country != "All":
    filtered_df = filtered_df[filtered_df["Country"] == selected_country]

# ============================================================
# KPI ROW
# ============================================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Revenue", f"£{filtered_df['TotalRevenue'].sum():,.0f}")
with col2:
    st.metric("Transactions", f"{filtered_df['Invoice'].nunique():,}")
with col3:
    st.metric("Avg Order Value",
              f"£{filtered_df.groupby('Invoice')['TotalRevenue'].sum().mean():,.2f}")
with col4:
    st.metric("Unique Customers", f"{filtered_df['Customer ID'].nunique():,}")

st.divider()

# ============================================================
# REVENUE TREND CHART
# ============================================================
st.subheader("Revenue Trend")

trend_data = filtered_df.groupby(filtered_df["InvoiceDate"].dt.date)["TotalRevenue"].sum()
trend_data.index.name = "Date"
st.line_chart(trend_data)

st.divider()

# ============================================================
# TOP PRODUCTS AND COUNTRY BREAKDOWN (side by side)
# ============================================================
left_col, right_col = st.columns(2)

with left_col:
    st.subheader("Top 10 Products by Revenue")
    top_products = (
        filtered_df.groupby("Description")["TotalRevenue"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )
    st.bar_chart(top_products)

with right_col:
    st.subheader("Revenue by Country")
    country_revenue = (
        filtered_df.groupby("Country")["TotalRevenue"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )
    st.bar_chart(country_revenue)

st.divider()

# ============================================================
# RAW DATA EXPANDER (for transparency / debugging during demos)
# ============================================================
with st.expander("View filtered raw data"):
    st.dataframe(
        filtered_df[["InvoiceDate", "Invoice", "Description", "Quantity",
                      "Price", "TotalRevenue", "Country"]].head(500),
        width='stretch'
    )
    st.caption(f"Showing first 500 of {len(filtered_df):,} filtered rows")
