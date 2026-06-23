"""
RetailPulse Dashboard - Inventory Dashboard Page (Day 18 Expansion)
========================================================================
Day 15 built a SKELETON version of this page. Day 18's job, per the
project plan, is:
  "Inventory optimization recommendations UI"

This page now has FOUR tabs:
  1. ABC Overview          - Pareto-style product classification view
  2. Reorder Recommendations - filterable, sortable, urgency-colored table
  3. Product Drill-Down     - single-product deep dive with simulated
                              stock-level timeline
  4. Policy Simulator       - interactive what-if: drag lead time /
                              service level sliders, see stockout and
                              inventory impact change LIVE

WHY A LIVE POLICY SIMULATOR HERE (NOT JUST STATIC NUMBERS FROM DAY 10)?
Day 10's notebook computed ONE fixed simulation with ONE set of
parameters (7-day lead time, 95% service level) and saved the result.
A dashboard's whole VALUE is letting a buyer/ops manager ask "what if
our supplier's lead time grows to 14 days?" and see the answer
immediately - that requires re-running the simulation logic live,
which is exactly what utils/inventory_utils.py was built to support.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sys
import os
from streamlit_extras.metric_cards import style_metric_cards

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utils.data_loader import (
    safe_load, load_inventory_recommendations, load_inventory_parameters,
    load_abc_classification, load_json_metrics
)
from utils.inventory_utils import (
    calculate_z_score, calculate_safety_stock, calculate_reorder_point,
    calculate_eoq, simulate_inventory_policy, generate_demand_sequence,
    compare_policies, classify_urgency
)

st.title("📦 Inventory Dashboard")
st.caption("ABC classification, reorder recommendations, and policy simulation")

# ============================================================
# LOAD DATA (shared across all tabs)
# ============================================================
recommendations = safe_load(load_inventory_recommendations)
parameters = safe_load(load_inventory_parameters)
abc_data = safe_load(load_abc_classification)
inventory_config = load_json_metrics("inventory_config.json")

if recommendations is None:
    st.stop()

# ============================================================
# TOP-LEVEL KPI ROW
# ============================================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Products Tracked (Class A)", f"{len(recommendations):,}")

with col2:
    if abc_data is not None:
        st.metric("Total Products (All Classes)", f"{len(abc_data):,}")
    else:
        st.metric("Total Products (All Classes)", "N/A")

with col3:
    if inventory_config:
        st.metric("Stockout Reduction", f"{inventory_config['total_stockout_reduction_pct']:.1f}%",
                   help="Target range: 25-40%")
    else:
        st.metric("Stockout Reduction", "N/A")

with col4:
    if inventory_config:
        st.metric("Avg Inventory Reduction", f"{inventory_config['avg_inventory_reduction_pct']:.1f}%",
                   help="Target range: 25-40%")
    else:
        st.metric("Avg Inventory Reduction", "N/A")

st.divider()
style_metric_cards()
# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 ABC Overview", "🔁 Reorder Recommendations",
    "🔎 Product Drill-Down", "🎛️ Policy Simulator"
])

# ============================================================
# TAB 1: ABC OVERVIEW
# ============================================================
with tab1:
    st.subheader("ABC Product Classification")
    st.markdown(
        "Products are classified by their share of total revenue "
        "(Pareto principle): **Class A** products drive the majority "
        "of revenue and get the most inventory attention; **Class C** "
        "products contribute little individually and need only loose "
        "monitoring."
    )

    if abc_data is not None:
        abc_summary = abc_data.groupby("ABC_Class").agg(
            NumProducts=("StockCode", "count"),
            TotalRevenue=("TotalRevenue", "sum")
        ).reset_index()
        abc_summary["PctOfRevenue"] = 100 * abc_summary["TotalRevenue"] / abc_summary["TotalRevenue"].sum()
        abc_summary["PctOfProducts"] = 100 * abc_summary["NumProducts"] / abc_summary["NumProducts"].sum()
        abc_summary = abc_summary.sort_values("ABC_Class")

        kpi_cols = st.columns(3)
        class_colors = {"A": "🔴", "B": "🟡", "C": "⚪"}
        for col, (_, row) in zip(kpi_cols, abc_summary.iterrows()):
            with col:
                st.metric(
                    f"{class_colors.get(row['ABC_Class'], '')} Class {row['ABC_Class']}",
                    f"{int(row['NumProducts']):,} products",
                    f"{row['PctOfRevenue']:.1f}% of revenue"
                )

        st.divider()

        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
        
            fig = px.pie(
                abc_summary,
                names="ABC_Class",
                values="NumProducts",
                title="Products Distribution"
            )
        
            st.plotly_chart(
                fig,
                use_container_width=True
            )
        
        with chart_col2:
        
            fig = px.pie(
                abc_summary,
                names="ABC_Class",
                values="PctOfRevenue",
                title="Revenue Share"
            )
        
            st.plotly_chart(
                fig,
                use_container_width=True
            )

        st.divider()

        st.subheader("Pareto Curve")
        st.markdown(
            "Products sorted by revenue (highest first), showing "
            "cumulative revenue percentage. The steep initial rise "
            "followed by a flattening tail is the visual signature of "
            "the Pareto principle in action."
        )
        sorted_abc = abc_data.sort_values("TotalRevenue", ascending=False).reset_index(drop=True)
        sorted_abc["Rank"] = sorted_abc.index + 1
        fig = px.line(
            sorted_abc,
            x="Rank",
            y="CumPct",
            title="ABC Pareto Curve"
        )
        
        fig.update_layout(
            height=500
        )
        
        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.divider()
        with st.expander("View full product classification table"):
            st.dataframe(abc_data, width="stretch")


        st.divider()
        
        st.subheader("Top 20 Revenue Products")
        
        top_products = (
            abc_data
            .sort_values(
                "TotalRevenue",
                ascending=False
            )
            .head(20)
        )
        
        fig = px.bar(
            top_products,
            x="Description",
            y="TotalRevenue",
            color="ABC_Class",
            title="Top Products by Revenue"
        )
        
        st.plotly_chart(
            fig,
            use_container_width=True
        )
    else:
        st.info("ABC classification data not found - run Day 10 notebook first.")

# ============================================================
# TAB 2: REORDER RECOMMENDATIONS
# ============================================================
with tab2:
    st.subheader("Reorder Recommendations")
    st.markdown(
        "Recommended reorder points and order quantities for top "
        "Class A products, derived from historical demand, forecasted "
        "demand growth (Day 8), and Safety Stock / EOQ formulas (Day 10)."
    )

    # Add an urgency classification column for visual triage.
    # We don't have LIVE current stock levels in this dataset, so we
    # SIMULATE a plausible "current stock" per product for demo purposes -
    # in a real production system this would come from a live inventory
    # database query instead.
    display_recs = recommendations.copy()
    rng = np.random.default_rng(123)
    display_recs["SimulatedCurrentStock"] = [
        int(rng.uniform(0.3, 1.8) * row["RecommendedReorderPoint"])
        for _, row in display_recs.iterrows()
    ]
    display_recs["Urgency"] = display_recs.apply(
        lambda r: classify_urgency(
            r["SimulatedCurrentStock"], r["RecommendedReorderPoint"], r["RecommendedSafetyStock"]
        ), axis=1
    )

    filter_col1, filter_col2 = st.columns([1, 2])
    with filter_col1:
        urgency_filter = st.selectbox("Filter by urgency", ["All", "Critical", "Reorder Now", "Healthy"])
    with filter_col2:
        search_term = st.text_input("Search by product description", "")

    filtered_recs = display_recs.copy()
    if urgency_filter != "All":
        filtered_recs = filtered_recs[filtered_recs["Urgency"] == urgency_filter]
    if search_term:
        filtered_recs = filtered_recs[
            filtered_recs["Description"].str.contains(search_term, case=False, na=False)
        ]

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Products Shown", f"{len(filtered_recs):,}")
    with m2:
        n_critical = (filtered_recs["Urgency"] == "Critical").sum()
        st.metric("Critical (need order today)", f"{n_critical:,}")
    with m3:
        n_reorder = (filtered_recs["Urgency"] == "Reorder Now").sum()
        st.metric("Reorder Now", f"{n_reorder:,}")

    st.subheader("Urgency Distribution")
        
    urgency_counts = (
        filtered_recs["Urgency"]
        .value_counts()
    )
        
    fig = px.pie(
        values=urgency_counts.values,
        names=urgency_counts.index,
        title="Inventory Status"
    )
        
    st.plotly_chart(
        fig,
        use_container_width=True
    )
    
    def highlight_urgency(row):
        color_map = {"Critical": "#f8d7da", "Reorder Now": "#fff3cd", "Healthy": "#d4edda"}
        color = color_map.get(row["Urgency"], "")
        return [f"background-color: {color}"] * len(row)

    st.dataframe(
        filtered_recs[[
            "StockCode", "Description", "SimulatedCurrentStock", "Urgency",
            "HistoricalAvgDailyDemand", "ForecastedDailyDemand",
            "RecommendedSafetyStock", "RecommendedReorderPoint", "RecommendedOrderQty"
        ]].style.apply(highlight_urgency, axis=1).format({
            "HistoricalAvgDailyDemand": "{:.1f}", "ForecastedDailyDemand": "{:.1f}"
        }),
        width="stretch"
    )
    st.caption(
        "Note: 'Simulated Current Stock' is illustrative for this demo "
        "(no live inventory feed connected). In production this column "
        "would be populated from a real-time stock database."
    )

# ============================================================
# TAB 3: PRODUCT DRILL-DOWN
# ============================================================
with tab3:
    st.subheader("Product Drill-Down")
    st.markdown(
        "Select a product to see a simulated stock-level timeline "
        "under its recommended reorder policy, and the exact action "
        "to take."
    )

    product_options = recommendations["StockCode"].tolist()
    selected_product = st.selectbox(
        "Select a product", product_options,
        format_func=lambda code: f"{code} - {recommendations[recommendations['StockCode']==code]['Description'].iloc[0][:40]}"
    )

    product_row = recommendations[recommendations["StockCode"] == selected_product].iloc[0]

    d_col1, d_col2, d_col3, d_col4 = st.columns(4)
    with d_col1:
        st.metric("Historical Daily Demand", f"{product_row['HistoricalAvgDailyDemand']:.1f} units")
    with d_col2:
        st.metric("Forecasted Daily Demand", f"{product_row['ForecastedDailyDemand']:.1f} units")
    with d_col3:
        st.metric("Reorder Point", f"{product_row['RecommendedReorderPoint']:.0f} units")
    with d_col4:
        st.metric("Order Quantity (EOQ)", f"{product_row['RecommendedOrderQty']:.0f} units")

    st.info(f"**Recommended action:** {product_row['Action']}")

    st.divider()

    st.subheader("Simulated Stock-Level Timeline")
    sim_days = st.slider("Simulation horizon (days)", min_value=30, max_value=365, value=120, step=10)

    # Estimate std demand from the parameters table if available, else
    # approximate it as 30% of mean demand (a reasonable default for
    # retail demand variability when the precise figure isn't on hand).
    if parameters is not None and selected_product in parameters["StockCode"].values:
        param_row = parameters[parameters["StockCode"] == selected_product].iloc[0]
        std_demand = param_row.get("ProjectedStdDemand", product_row["ForecastedDailyDemand"] * 0.3)
    else:
        std_demand = product_row["ForecastedDailyDemand"] * 0.3

    demand_seq = generate_demand_sequence(
        product_row["ForecastedDailyDemand"], std_demand, sim_days, seed=hash(selected_product) % 1000
    )
    initial_stock = int(round(product_row["ForecastedDailyDemand"] * 30))
    stockouts, avg_inv, daily_levels = simulate_inventory_policy(
        demand_seq, reorder_point=int(product_row["RecommendedReorderPoint"]),
        order_qty=int(product_row["RecommendedOrderQty"]), lead_time=7,
        initial_stock=initial_stock
    )

    sim_m1, sim_m2, sim_m3 = st.columns(3)
    with sim_m1:
        st.metric("Simulated Stockout Days", f"{stockouts}")
    with sim_m2:
        st.metric("Average Inventory Level", f"{avg_inv:.0f} units")
    with sim_m3:
        st.metric("Days Simulated", f"{sim_days}")

    timeline_df = pd.DataFrame({
        "Day": range(sim_days),
        "Stock Level": daily_levels,
    }).set_index("Day")
    timeline_df["Reorder Point"] = product_row["RecommendedReorderPoint"]
    timeline_df["Safety Stock"] = product_row["RecommendedSafetyStock"]

    fig = px.line(
        timeline_df.reset_index(),
        x="Day",
        y=[
            "Stock Level",
            "Reorder Point",
            "Safety Stock"
        ],
        title="Inventory Timeline"
    )
    
    st.plotly_chart(
        fig,
        use_container_width=True
    )
    st.caption(
        "When the orange Reorder Point line is crossed, a new order is "
        "triggered (arriving after a 7-day lead time). The simulation "
        "uses a fixed random seed per product for reproducibility."
    )

# ============================================================
# TAB 4: POLICY SIMULATOR (live what-if)
# ============================================================
with tab4:
    st.subheader("Interactive Policy Simulator")
    st.markdown(
        "Adjust the lead time and service level assumptions and see "
        "the simulated impact on stockouts and inventory levels "
        "**live** - useful for answering questions like *'what if our "
        "supplier's lead time doubles?'* without re-running a notebook."
    )

    sim_product = st.selectbox(
        "Select a product to simulate", recommendations["StockCode"].tolist(),
        key="policy_sim_product",
        format_func=lambda code: f"{code} - {recommendations[recommendations['StockCode']==code]['Description'].iloc[0][:40]}"
    )
    sim_product_row = recommendations[recommendations["StockCode"] == sim_product].iloc[0]

    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns(3)
    with ctrl_col1:
        lead_time = st.slider("Lead time (days)", min_value=1, max_value=30, value=7)
    with ctrl_col2:
        service_level = st.slider("Service level (%)", min_value=80, max_value=99, value=95)
    with ctrl_col3:
        sim_horizon = st.slider("Simulation horizon (days)", min_value=60, max_value=365, value=180, key="policy_sim_horizon")

    avg_demand = sim_product_row["ForecastedDailyDemand"]
    std_demand = avg_demand * 0.3  # approximate, see Tab 3 note

    # Recompute Safety Stock / Reorder Point LIVE using the slider values
    live_safety_stock = calculate_safety_stock(std_demand, lead_time, service_level)
    live_reorder_point = calculate_reorder_point(avg_demand, lead_time, live_safety_stock)
    live_eoq = calculate_eoq(avg_demand * 365, order_cost=20, holding_cost_per_unit=2.0)

    st.divider()

    live_col1, live_col2, live_col3 = st.columns(3)
    with live_col1:
        st.metric("Live Safety Stock", f"{live_safety_stock:.0f} units")
    with live_col2:
        st.metric("Live Reorder Point", f"{live_reorder_point:.0f} units")
    with live_col3:
        st.metric("Live EOQ", f"{live_eoq:.0f} units")

    st.divider()

    st.subheader("Naive vs Optimized Policy Comparison")
    naive_order_qty = int(round(avg_demand * 30))

    comparison = compare_policies(
        avg_daily_demand=avg_demand, std_daily_demand=std_demand,
        naive_order_qty=naive_order_qty,
        optimized_reorder_point=int(round(live_reorder_point)),
        optimized_order_qty=int(round(live_eoq)),
        lead_time_days=lead_time, sim_days=sim_horizon, seed=42
    )

    comp_col1, comp_col2 = st.columns(2)
    with comp_col1:
        st.metric(
            "Stockout Days: Naive -> Optimized",
            f"{comparison['naive_stockout_days']} -> {comparison['optimized_stockout_days']}",
            delta=f"{comparison['stockout_reduction_pct']:.1f}% reduction"
        )
    with comp_col2:
        st.metric(
            "Avg Inventory: Naive -> Optimized",
            f"{comparison['naive_avg_inventory']:.0f} -> {comparison['optimized_avg_inventory']:.0f}",
            delta=f"{comparison['inventory_reduction_pct']:.1f}% reduction"
        )

    timeline_compare_df = pd.DataFrame({
        "Day": range(sim_horizon),
        "Naive Policy": comparison["naive_daily_levels"],
        "Optimized Policy": comparison["optimized_daily_levels"],
    }).set_index("Day")
    fig = px.line(
        timeline_compare_df.reset_index(),
        x="Day",
        y=[
            "Naive Policy",
            "Optimized Policy"
        ],
        title="Policy Comparison"
    )
    
    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.caption(
        f"Simulated over {sim_horizon} days using the SAME randomly "
        "generated demand sequence for both policies, ensuring a fair "
        "comparison (any performance difference comes from the policy "
        "itself, not lucky/unlucky demand)."
    )
