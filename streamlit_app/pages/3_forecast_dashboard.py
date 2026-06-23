"""
RetailPulse Dashboard - Forecast Dashboard Page (Day 16 Expansion)
======================================================================
Day 15 built a SKELETON version of this page (model metrics + a single
basic alpha slider). Day 16's job, per the project plan, is:
  "Demand forecasting visualizations and what-if analysis"

This page now has FOUR tabs:
  1. Forecast Overview   - historical context + test-period forecast
  2. Model Comparison     - Prophet vs LSTM vs Hybrid, side by side
  3. What-If Analysis     - THREE interactive scenario tools
  4. Export                - download the forecast results as CSV

WHY TABS INSTEAD OF ONE LONG SCROLLING PAGE?
With this much content, a single page becomes a wall of charts that's
hard to navigate. st.tabs() keeps each concern visually separated while
staying on ONE page (as opposed to making each tab its OWN separate
page in the sidebar, which would fragment what is conceptually a
single "Forecast Dashboard" feature per the project's page list).
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utils.data_loader import (
    safe_load, load_hybrid_forecast_results, load_prophet_ready,
    load_json_metrics
)
from utils.forecast_utils import (
    calculate_mape, calculate_mae, calculate_rmse, blend_forecast,
    apply_growth_scenario, apply_seasonal_shock, build_confidence_band,
    summarize_scenario_impact
)

st.title("📈 Forecast Dashboard")
st.caption("Hybrid Prophet + LSTM demand forecasting, with interactive what-if analysis")

# ============================================================
# LOAD DATA (shared across all tabs)
# ============================================================
results = safe_load(load_hybrid_forecast_results)
historical = safe_load(load_prophet_ready)
hybrid_config = load_json_metrics("hybrid_config.json")

if results is None:
    st.stop()

# ============================================================
# TOP-LEVEL KPI ROW (visible above all tabs)
# ============================================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    if hybrid_config:
        st.metric("Prophet MAPE", f"{hybrid_config['prophet_mape']:.2f}%")
    else:
        st.metric("Prophet MAPE", f"{calculate_mape(results['actual'], results['prophet_pred']):.2f}%")

with col2:
    if hybrid_config:
        st.metric("LSTM MAPE", f"{hybrid_config['lstm_mape']:.2f}%")
    else:
        st.metric("LSTM MAPE", f"{calculate_mape(results['actual'], results['lstm_pred']):.2f}%")

with col3:
    hybrid_mape_value = (hybrid_config['hybrid_mape'] if hybrid_config
                          else calculate_mape(results['actual'], results['hybrid_pred']))
    st.metric("Hybrid MAPE", f"{hybrid_mape_value:.2f}%",
              help="Target from project spec: <= 12%")

with col4:
    target_met = hybrid_mape_value <= 12.0
    st.metric("Target Status", "PASS" if target_met else "REVIEW",
              delta=f"{12.0 - hybrid_mape_value:+.2f} pts vs target",
              delta_color="normal" if target_met else "inverse")

st.divider()

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Forecast Overview", "🔬 Model Comparison", "🎛️ What-If Analysis", "⬇️ Export"
])

# ============================================================
# TAB 1: FORECAST OVERVIEW
# ============================================================
with tab1:
    st.subheader("Historical Revenue + Forecast Period")
    st.markdown(
        "This chart shows the full historical revenue series leading "
        "into the forecast test period, so you can see the forecast "
        "in context rather than in isolation."
    )

    if historical is not None:
        hist_renamed = historical.rename(columns={"ds": "Date", "y": "Revenue"})
        hist_renamed["Source"] = "Historical (Actual)"

        forecast_renamed = results[["ds", "hybrid_pred"]].rename(
            columns={"ds": "Date", "hybrid_pred": "Revenue"}
        )
        forecast_renamed["Source"] = "Forecast (Hybrid)"

        combined = pd.concat([
            hist_renamed[["Date", "Revenue", "Source"]],
            forecast_renamed
        ], ignore_index=True)

        chart_pivot = combined.pivot_table(
            index="Date", columns="Source", values="Revenue", aggfunc="first"
        )
        st.line_chart(chart_pivot)
    else:
        # Fall back to just the test-period forecast if historical data isn't available
        st.info("Historical series not found - showing test period only.")
        st.line_chart(results.set_index("ds")[["actual", "hybrid_pred"]])

    st.divider()

    st.subheader("Forecast with Confidence Interval")
    st.markdown(
        "Since the hybrid ensemble doesn't have a native uncertainty "
        "estimate (unlike Prophet alone, which provides `yhat_lower`/"
        "`yhat_upper`), we approximate a confidence band using the "
        "model's own historical MAPE as a proxy for typical error size."
    )

    confidence_pct = st.slider(
        "Confidence level", min_value=80, max_value=99, value=95, step=1,
        help="Higher confidence = wider band (more cautious about uncertainty)"
    )
    # Convert confidence % to an approximate z-score multiplier.
    # 95% -> 1.96, 90% -> 1.645, 99% -> 2.576 (standard normal critical values)
    z_lookup = {80: 1.28, 85: 1.44, 90: 1.645, 95: 1.96, 99: 2.576}
    nearest_key = min(z_lookup.keys(), key=lambda k: abs(k - confidence_pct))
    z_score = z_lookup[nearest_key]

    lower_band, upper_band = build_confidence_band(
        results["hybrid_pred"], mape_pct=hybrid_mape_value, z_score=z_score
    )

    band_df = pd.DataFrame({
        "Date": results["ds"],
        "Actual": results["actual"],
        "Forecast": results["hybrid_pred"],
        "Lower Bound": lower_band,
        "Upper Bound": upper_band,
    }).set_index("Date")

    st.line_chart(band_df[["Actual", "Forecast", "Lower Bound", "Upper Bound"]])
    st.caption(
        f"Approximate {confidence_pct}% confidence band, built from "
        f"the hybrid model's {hybrid_mape_value:.2f}% historical MAPE."
    )

# ============================================================
# TAB 2: MODEL COMPARISON
# ============================================================
with tab2:
    st.subheader("Side-by-Side: Prophet vs LSTM vs Hybrid")

    comparison_chart_data = results.set_index("ds")[
        ["actual", "prophet_pred", "lstm_pred", "hybrid_pred"]
    ]
    comparison_chart_data.columns = ["Actual", "Prophet", "LSTM", "Hybrid"]
    st.line_chart(comparison_chart_data)

    st.divider()

    st.subheader("Error Metrics Comparison")

    metrics_rows = []
    for model_name, pred_col in [("Prophet", "prophet_pred"),
                                   ("LSTM", "lstm_pred"),
                                   ("Hybrid", "hybrid_pred")]:
        metrics_rows.append({
            "Model": model_name,
            "MAPE (%)": calculate_mape(results["actual"], results[pred_col]),
            "MAE (£)": calculate_mae(results["actual"], results[pred_col]),
            "RMSE (£)": calculate_rmse(results["actual"], results[pred_col]),
        })
    metrics_df = pd.DataFrame(metrics_rows)

    st.dataframe(
        metrics_df.style.format({
            "MAPE (%)": "{:.2f}", "MAE (£)": "{:,.2f}", "RMSE (£)": "{:,.2f}"
        }).highlight_min(subset=["MAPE (%)", "MAE (£)", "RMSE (£)"], color="#d4edda"),
        width="stretch"
    )
    st.caption("Highlighted cells show the best (lowest error) model per metric.")

    st.divider()

    st.subheader("Residual Comparison")
    st.markdown(
        "Residual = Actual − Predicted. Points scattered evenly around "
        "zero indicate unbiased predictions; a consistent pattern above "
        "or below zero indicates systematic over- or under-prediction."
    )

    residual_df = pd.DataFrame({
        "Date": results["ds"],
        "Prophet Residual": results["actual"] - results["prophet_pred"],
        "LSTM Residual": results["actual"] - results["lstm_pred"],
        "Hybrid Residual": results["actual"] - results["hybrid_pred"],
    }).set_index("Date")
    st.line_chart(residual_df)

# ============================================================
# TAB 3: WHAT-IF ANALYSIS
# ============================================================
with tab3:
    st.subheader("Scenario Tools")
    st.markdown(
        "Explore how changes to the forecast assumptions would affect "
        "projected revenue. All three tools below recompute LIVE as "
        "you adjust the controls - this is the core mental model for "
        "Streamlit interactivity: every widget change re-runs this "
        "page's script from top to bottom."
    )

    whatif_tool = st.radio(
        "Choose a what-if tool:",
        ["Blend Weight (Prophet vs LSTM)", "Growth/Decline Shock", "Targeted Date-Range Shock"],
        horizontal=True
    )

    st.divider()

    baseline_total = results["hybrid_pred"].sum()

    # ---------- TOOL 1: Blend weight ----------
    if whatif_tool == "Blend Weight (Prophet vs LSTM)":
        st.markdown("**Adjust how much weight Prophet vs LSTM contributes to the forecast.**")

        default_alpha = hybrid_config["alpha"] if hybrid_config else 0.5
        alpha = st.slider(
            "Blend weight (alpha): 1.0 = pure Prophet, 0.0 = pure LSTM",
            min_value=0.0, max_value=1.0, value=float(default_alpha), step=0.05
        )

        scenario_pred = blend_forecast(results["prophet_pred"], results["lstm_pred"], alpha)
        scenario_mape = calculate_mape(results["actual"], scenario_pred)
        scenario_total = scenario_pred.sum()

        impact = summarize_scenario_impact(baseline_total, scenario_total)

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Resulting MAPE", f"{scenario_mape:.2f}%")
        with m2:
            st.metric("Total Forecasted Revenue", f"£{scenario_total:,.0f}")
        with m3:
            st.metric("vs Saved Hybrid Total", f"{impact['percent_difference']:+.1f}%")

        chart_data = pd.DataFrame({
            "Date": results["ds"], "Actual": results["actual"],
            "Saved Hybrid": results["hybrid_pred"], "Your Blend": scenario_pred
        }).set_index("Date")
        st.line_chart(chart_data)

    # ---------- TOOL 2: Growth/decline shock ----------
    elif whatif_tool == "Growth/Decline Shock":
        st.markdown(
            "**Simulate a uniform demand shock across the whole forecast "
            "period** - e.g., a market-wide downturn, a successful "
            "national ad campaign, or inflation-driven price increases."
        )

        growth_pct = st.slider(
            "Demand change (%)", min_value=-50, max_value=50, value=0, step=5,
            help="Positive = demand increase, Negative = demand decrease"
        )

        scenario_pred = apply_growth_scenario(results["hybrid_pred"], growth_pct)
        scenario_total = scenario_pred.sum()
        impact = summarize_scenario_impact(baseline_total, scenario_total)

        m1, m2 = st.columns(2)
        with m1:
            st.metric("Scenario Total Revenue", f"£{scenario_total:,.0f}",
                      delta=f"£{impact['absolute_difference']:,.0f}")
        with m2:
            st.metric("Percent Change", f"{impact['percent_difference']:+.1f}%")

        chart_data = pd.DataFrame({
            "Date": results["ds"], "Baseline Forecast": results["hybrid_pred"],
            f"Scenario ({growth_pct:+d}%)": scenario_pred
        }).set_index("Date")
        st.line_chart(chart_data)

    # ---------- TOOL 3: Targeted date-range shock ----------
    else:
        st.markdown(
            "**Simulate a targeted event** - e.g., a flash sale, a "
            "stockout period, or a short marketing campaign that only "
            "affects demand within a specific date window."
        )

        min_d = results["ds"].min().date()
        max_d = results["ds"].max().date()

        shock_range = st.date_input(
            "Shock date range", value=(min_d, max_d), min_value=min_d, max_value=max_d
        )
        shock_pct = st.slider(
            "Shock intensity (%)", min_value=-50, max_value=100, value=20, step=5
        )

        if len(shock_range) == 2:
            shock_start, shock_end = shock_range
            scenario_pred = apply_seasonal_shock(
                results["ds"], results["hybrid_pred"], shock_start, shock_end, shock_pct
            )
            scenario_total = scenario_pred.sum()
            impact = summarize_scenario_impact(baseline_total, scenario_total)

            m1, m2 = st.columns(2)
            with m1:
                st.metric("Scenario Total Revenue", f"£{scenario_total:,.0f}",
                          delta=f"£{impact['absolute_difference']:,.0f}")
            with m2:
                st.metric("Percent Change", f"{impact['percent_difference']:+.1f}%")

            chart_data = pd.DataFrame({
                "Date": results["ds"], "Baseline Forecast": results["hybrid_pred"],
                f"With Shock ({shock_pct:+d}%)": scenario_pred
            }).set_index("Date")
            st.line_chart(chart_data)
        else:
            st.info("Select both a start and end date for the shock window.")

# ============================================================
# TAB 4: EXPORT
# ============================================================
with tab4:
    st.subheader("Export Forecast Results")
    st.markdown(
        "Download the full forecast comparison table as a CSV - useful "
        "for sharing with stakeholders who don't use this dashboard "
        "directly, or for further analysis in Excel/Power BI."
    )

    export_df = results.copy()
    export_df["prophet_residual"] = export_df["actual"] - export_df["prophet_pred"]
    export_df["lstm_residual"] = export_df["actual"] - export_df["lstm_pred"]
    export_df["hybrid_residual"] = export_df["actual"] - export_df["hybrid_pred"]

    csv_bytes = export_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download forecast_results.csv",
        data=csv_bytes,
        file_name="retailpulse_forecast_results.csv",
        mime="text/csv",
    )

    st.divider()
    st.dataframe(export_df, width="stretch")
