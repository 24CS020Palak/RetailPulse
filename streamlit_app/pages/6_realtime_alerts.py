"""
RetailPulse Dashboard - Real-Time Metrics & Alerts Page (Day 19)
=====================================================================
Project plan, Day 19: "Real-time metrics and alerts"

IMPORTANT HONESTY NOTE (also explained on-page to the user):
This project's underlying dataset (UCI Online Retail II) is HISTORICAL
- it ends in December 2011, so there is no genuinely live transaction
feed to connect to. This page therefore SIMULATES a live data stream
(see utils/realtime_utils.py's docstring for the full rationale), but
the AUTO-REFRESH MECHANICS and ALERTING LOGIC built here are fully
real and would work IDENTICALLY against a genuine live data source -
only the data generator function would need to be swapped out.

THREE Streamlit mechanisms work together on this page:
  1. st.session_state  - persists the simulated metric values BETWEEN
     reruns/refreshes (without this, every refresh would reset to the
     baseline instead of evolving over time).
  2. st.fragment(run_every=...) - reruns ONLY the live metrics section
     on a timer, WITHOUT reloading the entire page (sidebar, other
     tabs, etc.) - this is the key to making a "real-time" feel
     without a jarring full-page flash every few seconds.
  3. A manual refresh button - lets the user force an immediate update
     outside the automatic timer, useful right after changing a
     threshold setting.
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime
from streamlit_extras.metric_cards import style_metric_cards

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utils.data_loader import (
    safe_load, load_daily_revenue, load_inventory_recommendations,
    load_json_metrics
)
from utils.realtime_utils import (
    generate_live_snapshot, check_revenue_alert, check_stockout_alert,
    check_churn_spike_alert, check_forecast_drift_alert, collect_all_alerts,
    format_alert_age, SEVERITY_COLORS
)

st.title("🔴 Real-Time Metrics & Alerts")
st.caption("Live operational monitoring with threshold-based alerting")
health_score = 100

if len(st.session_state.get("alert_history", [])) > 0:
    critical = sum(
        1 for a in st.session_state.alert_history
        if a["severity"] == "Critical"
    )
    warning = sum(
        1 for a in st.session_state.alert_history
        if a["severity"] == "Warning"
    )

    health_score = max(0, 100 - critical*15 - warning*5)

st.progress(health_score / 100)

st.metric("System Health Score", f"{health_score}%")

st.info(
    "**About this page:** The underlying dataset is historical "
    "(2009-2011), so live metrics below are SIMULATED for "
    "demonstration. The auto-refresh mechanism and alert logic are "
    "fully production-realistic - only the data source is simulated.",
    icon="ℹ️"
)

# ============================================================
# LOAD BASELINE DATA (used to seed realistic simulated values)
# ============================================================
daily_revenue = safe_load(load_daily_revenue)
recommendations = safe_load(load_inventory_recommendations)
churn_metrics = load_json_metrics("churn_metrics.json")
hybrid_config = load_json_metrics("hybrid_config.json")

# if daily_revenue is not None and len(daily_revenue) > 0:
#     baseline_revenue = float(daily_revenue["Revenue"].tail(30).mean())
# else:
#     baseline_revenue = 3000.0

# ============================================================
# DETERMINE REVENUE COLUMN SAFELY
# ============================================================

if daily_revenue is not None and len(daily_revenue) > 0:

    if "Revenue" in daily_revenue.columns:
        revenue_col = "Revenue"

    elif "TotalRevenue" in daily_revenue.columns:
        revenue_col = "TotalRevenue"

    elif "y" in daily_revenue.columns:
        revenue_col = "y"

    else:
        st.error(
            f"Revenue column not found. Available columns: "
            f"{daily_revenue.columns.tolist()}"
        )
        st.stop()

    baseline_revenue = float(
        daily_revenue[revenue_col].tail(30).mean()
    )

else:
    baseline_revenue = 3000.0

baseline_orders = max(1, int(baseline_revenue / 85))   # rough avg order value assumption
baseline_avg_order_value = baseline_revenue / baseline_orders

# ============================================================
# SIDEBAR CONTROLS (alert thresholds + refresh settings)
# ============================================================
st.sidebar.subheader("Live Monitor Settings")

refresh_interval = st.sidebar.slider(
    "Auto-refresh interval (seconds)", min_value=3, max_value=30, value=5, step=1
)
revenue_warning_threshold = st.sidebar.slider(
    "Revenue alert: Warning threshold (%)", min_value=5, max_value=40, value=15
)
revenue_critical_threshold = st.sidebar.slider(
    "Revenue alert: Critical threshold (%)", min_value=10, max_value=60, value=30
)
churn_alert_threshold = st.sidebar.slider(
    "Churn spike alert threshold (pct points)", min_value=1, max_value=20, value=5
)

auto_refresh_enabled = st.sidebar.toggle("Enable auto-refresh", value=True)

st.sidebar.divider()
st.sidebar.caption(
    f"When enabled, the live metrics section below refreshes every "
    f"{refresh_interval} seconds automatically."
)

# ============================================================
# INITIALIZE SESSION STATE
# ============================================================
# session_state persists across reruns within the SAME user session -
# without this, every single refresh would regenerate fresh random
# values disconnected from the previous tick, producing a jarring
# sawtooth pattern instead of a smooth, realistic-looking live metric.
if "live_snapshot" not in st.session_state:
    st.session_state.live_snapshot = generate_live_snapshot(
        baseline_revenue, baseline_orders, baseline_avg_order_value
    )
if "alert_history" not in st.session_state:
    st.session_state.alert_history = []
if "tick_count" not in st.session_state:
    st.session_state.tick_count = 0

# ============================================================
# LIVE METRICS FRAGMENT
# ============================================================
# Everything inside this function reruns on its OWN timer (run_every),
# independent of the rest of the page - the sidebar, page title, and
# static sections above do NOT reload every tick, only this fragment does.

@st.fragment(run_every=refresh_interval if auto_refresh_enabled else None)
def live_metrics_section():
    # Advance the simulated metrics by one tick, building on the
    # PREVIOUS session_state value (not the original baseline) so the
    # series evolves smoothly tick over tick.
    prev = st.session_state.live_snapshot
    st.session_state.live_snapshot = generate_live_snapshot(
        prev["revenue_today"], prev["orders_today"], prev["avg_order_value"]
    )
    st.session_state.tick_count += 1

    snapshot = st.session_state.live_snapshot

    last_updated_col, refresh_col = st.columns([3, 1])
    with last_updated_col:
        st.caption(
            f"Last updated: {snapshot['timestamp'].strftime('%H:%M:%S')}  "
            f"(tick #{st.session_state.tick_count}, refreshes every "
            f"{refresh_interval}s)" if auto_refresh_enabled else
            f"Last updated: {snapshot['timestamp'].strftime('%H:%M:%S')}  (auto-refresh OFF)"
        )
    with refresh_col:
        if st.button("🔄 Refresh now", width="stretch"):
            st.rerun(scope="fragment")

    # --- Live KPI row ---
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(
            "Revenue Today (simulated)", f"£{snapshot['revenue_today']:,.0f}",
            delta=f"{100*(snapshot['revenue_today']-baseline_revenue)/baseline_revenue:+.1f}% vs 30-day avg"
        )
    with m2:
        st.metric(
            "Orders Today (simulated)", f"{snapshot['orders_today']:,}",
            delta=f"{snapshot['orders_today']-baseline_orders:+d} vs 30-day avg"
        )
    with m3:
        st.metric(
            "Avg Order Value (simulated)", f"£{snapshot['avg_order_value']:.2f}",
            delta=f"{100*(snapshot['avg_order_value']-baseline_avg_order_value)/baseline_avg_order_value:+.1f}% vs 30-day avg"
        )

    if "revenue_history" not in st.session_state:
        st.session_state.revenue_history = []
    
    st.session_state.revenue_history.append(
        snapshot["revenue_today"]
    )
    
    history_df = pd.DataFrame(
        st.session_state.revenue_history,
        columns=["Revenue"]
    )
    
    st.subheader("Live Revenue Trend")
    st.line_chart(history_df)

    # --- Run all alert checks for this tick ---
    revenue_alert = check_revenue_alert(
        snapshot["revenue_today"], baseline_revenue,
        warning_threshold_pct=revenue_warning_threshold,
        critical_threshold_pct=revenue_critical_threshold
    )

    stockout_alerts = []
    if recommendations is not None:
        # Simulate current stock for a couple of products each tick,
        # same illustrative approach as Day 18's "Simulated Current
        # Stock" column, reused here for consistency.
        rng = np.random.default_rng(st.session_state.tick_count)
        sample_products = recommendations.sample(min(3, len(recommendations)), random_state=st.session_state.tick_count % 1000)
        for _, prod in sample_products.iterrows():
            simulated_stock = int(rng.uniform(0.2, 1.5) * prod["RecommendedReorderPoint"])
            alert = check_stockout_alert(
                prod["Description"][:30], simulated_stock,
                prod["RecommendedReorderPoint"], prod["RecommendedSafetyStock"]
            )
            if alert:
                stockout_alerts.append(alert)

    churn_alert = None
    if churn_metrics:
        # Simulate a slightly fluctuating "current" churn rate around
        # the saved baseline, to demonstrate the spike-detection logic.
        simulated_current_churn = churn_metrics["churn_rate"] * 100 + np.random.normal(0, 3)
        churn_alert = check_churn_spike_alert(
            simulated_current_churn, churn_metrics["churn_rate"] * 100,
            threshold_pct_points=churn_alert_threshold
        )

    forecast_alert = None
    if hybrid_config:
        forecast_alert = check_forecast_drift_alert(hybrid_config["hybrid_mape"])

    new_alerts = collect_all_alerts(revenue_alert, stockout_alerts, churn_alert, forecast_alert)

    # Append any NEW alerts to the running history (capped to avoid
    # unbounded memory growth over a long session).
    st.session_state.alert_history = (new_alerts + st.session_state.alert_history)[:50]

    return new_alerts


current_alerts = live_metrics_section()

st.divider()
style_metric_cards()

# ============================================================
# ALERT FEED (outside the fragment - shows accumulated history)
# ============================================================
st.subheader("Alert Summary")

if st.session_state.alert_history:
    alert_df = pd.DataFrame(st.session_state.alert_history)

    alert_counts = alert_df["severity"].value_counts()

    st.bar_chart(alert_counts)
st.subheader("Alert Feed")
critical_count = sum(
    1 for a in st.session_state.alert_history
    if a["severity"] == "Critical"
)

warning_count = sum(
    1 for a in st.session_state.alert_history
    if a["severity"] == "Warning"
)

info_count = sum(
    1 for a in st.session_state.alert_history
    if a["severity"] == "Info"
)

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Critical Alerts", critical_count)

with c2:
    st.metric("Warning Alerts", warning_count)

with c3:
    st.metric("Info Alerts", info_count)

if not st.session_state.alert_history:
    st.success("No alerts triggered yet. All metrics within normal range.")
else:
    severity_filter = st.multiselect(
        "Filter by severity", ["Critical", "Warning", "Info"],
        default=["Critical", "Warning", "Info"]
    )

    visible_alerts = [a for a in st.session_state.alert_history if a["severity"] in severity_filter]

    n_critical = sum(1 for a in st.session_state.alert_history if a["severity"] == "Critical")
    n_warning = sum(1 for a in st.session_state.alert_history if a["severity"] == "Warning")

    sm1, sm2, sm3 = st.columns(3)
    with sm1:
        st.metric("Total Alerts Logged", len(st.session_state.alert_history))
    with sm2:
        st.metric("Critical", n_critical)
    with sm3:
        st.metric("Warning", n_warning)

    st.divider()

    for alert in visible_alerts[:20]:
        color = SEVERITY_COLORS.get(alert["severity"], "#95a5a6")
        age = format_alert_age(alert["timestamp"])
        st.markdown(
            f"""<div style="border-left: 4px solid {color}; padding: 8px 12px;
            margin-bottom: 8px; background-color: #f8f9fb; border-radius: 4px;">
            <strong style="color:{color};">{alert['severity']}</strong> -
            <em>{alert['metric']}</em> ({age})<br>
            {alert['message']}
            </div>""",
            unsafe_allow_html=True
        )

    if len(visible_alerts) > 20:
        st.caption(f"Showing 20 most recent of {len(visible_alerts)} matching alerts.")

    if st.button("Clear alert history"):
        st.session_state.alert_history = []
        st.rerun()

st.divider()

# ============================================================
# ALERT THRESHOLD REFERENCE TABLE
# ============================================================
with st.expander("View alert threshold configuration"):
    threshold_df = pd.DataFrame([
        {"Metric": "Revenue", "Warning": f"±{revenue_warning_threshold}% vs baseline",
         "Critical": f"±{revenue_critical_threshold}% vs baseline"},
        {"Metric": "Inventory", "Warning": "Stock at/below Reorder Point",
         "Critical": "Stock at/below Safety Stock"},
        {"Metric": "Churn", "Warning": f"+{churn_alert_threshold}pp vs baseline",
         "Critical": f"+{churn_alert_threshold*2}pp vs baseline"},
        {"Metric": "Forecast Accuracy", "Warning": "MAPE within 2pp of 12% target",
         "Critical": "MAPE >= 12% target"},
    ])
    st.dataframe(threshold_df, width="stretch")
    st.caption(
        "Revenue and churn thresholds are adjustable live via the "
        "sidebar sliders. Inventory and forecast thresholds reuse the "
        "fixed business rules from Day 18 and the project spec."
    )
