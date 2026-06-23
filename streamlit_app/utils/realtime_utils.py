"""
RetailPulse Dashboard - Real-Time Metrics and Alerting Utilities
=====================================================================
Day 19's job is "Real-time metrics and alerts." Since this project's
data is HISTORICAL (UCI Online Retail II ends in Dec 2011), there is
no genuinely live transaction feed to poll. Instead, this module
provides:

  1. A SIMULATED live data generator - mimics what a real-time feed
     would produce, so the live-refresh UI mechanics can be properly
     built and demonstrated.
  2. THRESHOLD-BASED alert rules - the actual reusable logic a real
     production system would apply identically, whether the metrics
     come from a simulator (here) or a real Kafka/database stream
     (in production). This separation matters: the ALERTING LOGIC is
     production-realistic even though the DATA SOURCE is simulated
     for this academic project.

This mirrors the same honest-about-limitations approach used in Day
12 (drift detection simulation) and Day 18 ("Simulated Current Stock")
- the project explicitly doesn't have a live production data pipeline,
so we simulate the DATA but keep the LOGIC genuine and reusable.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta


# ============================================================
# ALERT SEVERITY LEVELS
# ============================================================
# A small, fixed vocabulary keeps alert handling code (coloring,
# sorting, filtering) simple and consistent across the whole page,
# rather than allowing arbitrary free-text severity strings.
SEVERITY_ORDER = {"Critical": 3, "Warning": 2, "Info": 1}
SEVERITY_COLORS = {"Critical": "#e74c3c", "Warning": "#f39c12", "Info": "#3498db"}


def simulate_live_metric_tick(previous_value, volatility=0.05, trend=0.0, min_value=0.0):
    """
    Generates ONE new simulated metric reading based on the previous
    value - a simple random walk with optional drift (trend), rather
    than pure independent random noise each tick. This produces a
    more REALISTIC-looking live metric (smooth wandering, occasional
    spikes) than re-randomizing from scratch every refresh, which
    would look obviously fake (sawtooth jumps with no continuity).

    volatility: standard deviation of the percentage change per tick
    trend: average percentage drift per tick (small positive = slow growth)
    """
    pct_change = np.random.normal(trend, volatility)
    new_value = previous_value * (1 + pct_change)
    return max(new_value, min_value)


def generate_live_snapshot(baseline_revenue, baseline_orders, baseline_avg_order_value):
    """
    Produces one simulated 'current snapshot' of key live metrics,
    each evolving independently via simulate_live_metric_tick. Used
    to seed and update Streamlit session_state on every auto-refresh
    tick (see the dashboard page for how this integrates with
    st.fragment's run_every mechanism).
    """
    return {
        "timestamp": datetime.now(),
        "revenue_today": simulate_live_metric_tick(baseline_revenue, volatility=0.08, trend=0.002),
        "orders_today": max(1, round(simulate_live_metric_tick(baseline_orders, volatility=0.10, trend=0.001))),
        "avg_order_value": simulate_live_metric_tick(baseline_avg_order_value, volatility=0.04, trend=0.0),
    }


def check_revenue_alert(current_revenue, expected_revenue, warning_threshold_pct=15, critical_threshold_pct=30):
    """
    Compares CURRENT revenue against an EXPECTED baseline (e.g. the
    forecast for today, or yesterday's actual figure) and returns an
    alert if the deviation exceeds a threshold - in EITHER direction.
    A large unexpected revenue SPIKE deserves investigation just as
    much as a large DROP (could be a pricing bug, a bot, or a genuine
    demand surge worth reacting to operationally).
    """
    if expected_revenue == 0:
        return None

    deviation_pct = 100 * (current_revenue - expected_revenue) / expected_revenue

    if abs(deviation_pct) >= critical_threshold_pct:
        severity = "Critical"
    elif abs(deviation_pct) >= warning_threshold_pct:
        severity = "Warning"
    else:
        return None  # within normal range, no alert

    direction = "above" if deviation_pct > 0 else "below"
    return {
        "severity": severity,
        "metric": "Revenue",
        "message": (
            f"Today's revenue is {abs(deviation_pct):.1f}% {direction} "
            f"expected (£{current_revenue:,.0f} vs £{expected_revenue:,.0f} expected)"
        ),
        "deviation_pct": deviation_pct,
        "timestamp": datetime.now(),
    }


def check_stockout_alert(product_name, current_stock, reorder_point, safety_stock):
    """
    Flags products that have crossed into Critical or Reorder Now
    territory - reuses the SAME urgency thresholds from Day 18's
    classify_urgency function, so the Day 18 inventory table and Day
    19's alert feed never disagree about what counts as urgent.
    """
    if current_stock <= safety_stock:
        return {
            "severity": "Critical",
            "metric": "Inventory",
            "message": f"{product_name} stock CRITICAL: {current_stock} units (below safety stock of {safety_stock})",
            "timestamp": datetime.now(),
        }
    elif current_stock <= reorder_point:
        return {
            "severity": "Warning",
            "metric": "Inventory",
            "message": f"{product_name} needs reorder: {current_stock} units (reorder point: {reorder_point})",
            "timestamp": datetime.now(),
        }
    return None


def check_churn_spike_alert(current_period_churn_rate, baseline_churn_rate, threshold_pct_points=5):
    """
    Flags a meaningful RISE in churn rate compared to a historical
    baseline - expressed in PERCENTAGE POINTS rather than percentage
    change, since churn rate is already a percentage and comparing
    '5 percentage points higher' is more directly interpretable to a
    business stakeholder than a relative percentage-of-percentage figure.
    """
    diff_points = current_period_churn_rate - baseline_churn_rate

    if diff_points >= threshold_pct_points:
        severity = "Critical" if diff_points >= threshold_pct_points * 2 else "Warning"
        return {
            "severity": severity,
            "metric": "Churn",
            "message": (
                f"Churn rate has risen {diff_points:.1f} percentage points "
                f"above baseline ({current_period_churn_rate:.1f}% vs "
                f"{baseline_churn_rate:.1f}% baseline)"
            ),
            "timestamp": datetime.now(),
        }
    return None


def check_forecast_drift_alert(current_mape, target_mape=12.0, warning_buffer=2.0):
    """
    Flags when the forecasting model's error rate creeps close to or
    exceeds the project's target MAPE (<=12% per spec) - an early
    warning that retraining (Day 13's pipeline) may need to trigger
    soon, even before the hard threshold is technically breached.
    """
    if current_mape >= target_mape:
        return {
            "severity": "Critical",
            "metric": "Forecast Accuracy",
            "message": f"Forecast MAPE ({current_mape:.1f}%) has exceeded the target threshold ({target_mape:.1f}%)",
            "timestamp": datetime.now(),
        }
    elif current_mape >= target_mape - warning_buffer:
        return {
            "severity": "Warning",
            "metric": "Forecast Accuracy",
            "message": f"Forecast MAPE ({current_mape:.1f}%) is approaching the target threshold ({target_mape:.1f}%)",
            "timestamp": datetime.now(),
        }
    return None


def collect_all_alerts(revenue_alert, stockout_alerts, churn_alert, forecast_alert):
    """
    Merges every alert source into one list, drops any None entries
    (sources that didn't trigger), and sorts by severity (Critical
    first) then recency - giving the alert feed a sensible,
    consistent display order regardless of which sources fired.
    """
    all_alerts = []
    if revenue_alert:
        all_alerts.append(revenue_alert)
    if stockout_alerts:
        all_alerts.extend([a for a in stockout_alerts if a is not None])
    if churn_alert:
        all_alerts.append(churn_alert)
    if forecast_alert:
        all_alerts.append(forecast_alert)

    all_alerts.sort(key=lambda a: (-SEVERITY_ORDER.get(a["severity"], 0), a["timestamp"]), reverse=False)
    # Re-sort properly: severity descending (Critical first), then most recent first
    all_alerts.sort(key=lambda a: SEVERITY_ORDER.get(a["severity"], 0), reverse=True)

    return all_alerts


def format_alert_age(alert_timestamp):
    """
    Converts an alert's timestamp into a human-friendly relative time
    string ('just now', '3 min ago') - far more scannable in a live
    alert feed than a raw datetime string, especially when multiple
    alerts arrive within the same minute.
    """
    delta = datetime.now() - alert_timestamp
    seconds = delta.total_seconds()

    if seconds < 10:
        return "just now"
    elif seconds < 60:
        return f"{int(seconds)} sec ago"
    elif seconds < 3600:
        return f"{int(seconds // 60)} min ago"
    else:
        return f"{int(seconds // 3600)} hr ago"
