"""
RetailPulse Dashboard - Customer Segmentation Utilities
===========================================================
Day 17 needs enough segment-specific calculation logic (segment
profile summaries, churn-risk binning, recommended actions per
segment) that it deserves its own module - same reasoning as
forecast_utils.py on Day 16.
"""

import pandas as pd
import numpy as np


# Business action recommendations per RFM segment. Defined once here
# so both the segment overview AND any future email/campaign export
# tool can reuse the SAME mapping, rather than risking two different
# pages giving contradictory advice for the same segment name.
SEGMENT_ACTIONS = {
    "Champions": "Send VIP rewards, request reviews, invite to referral program.",
    "Loyal Customers": "Offer loyalty points, upsell premium or related products.",
    "Potential Loyalist": "Encourage repeat purchase with a small incentive.",
    "New Customers": "Send a welcome series, highlight popular products.",
    "Need Attention": "Re-engagement email with a modest discount.",
    "At Risk": "Targeted win-back offer before they fully churn.",
    "Lost": "Strong incentive win-back campaign as a last attempt.",
}

# Display order and colors used consistently across charts on this page
SEGMENT_COLOR_MAP = {
    "Champions": "#2ecc71",
    "Loyal Customers": "#3498db",
    "Potential Loyalist": "#1abc9c",
    "New Customers": "#9b59b6",
    "Need Attention": "#f39c12",
    "At Risk": "#e67e22",
    "Lost": "#e74c3c",
}


def build_segment_profile(rfm_df, segment_col="KMeans_Label"):
    """
    Aggregates the RFM table into one row per segment with average
    Recency/Frequency/Monetary and customer count - the data behind
    the segment summary cards and bar charts.
    """
    profile = rfm_df.groupby(segment_col).agg(
        Count=("Customer ID", "count"),
        Avg_Recency=("Recency", "mean"),
        Avg_Frequency=("Frequency", "mean"),
        Avg_Monetary=("Monetary", "mean"),
    ).reset_index()
    profile["Pct_of_Customers"] = 100 * profile["Count"] / profile["Count"].sum()
    return profile.sort_values("Count", ascending=False)


def bin_churn_risk(pred_proba, low_threshold=0.3, high_threshold=0.6):
    """
    Converts a continuous churn probability into a 3-level risk
    category (Low / Medium / High) - easier for a non-technical
    stakeholder to scan a table of 300 customers than raw decimals.
    Thresholds are deliberately exposed as parameters so the page can
    let the user adjust sensitivity live (see the risk threshold
    slider in the dashboard page).
    """
    pred_proba = np.asarray(pred_proba, dtype=float)
    risk = np.where(
        pred_proba >= high_threshold, "High",
        np.where(pred_proba >= low_threshold, "Medium", "Low")
    )
    return risk


def get_segment_action(segment_label):
    """Looks up the recommended business action for a segment label,
    with a safe fallback for any unrecognized/custom segment name."""
    return SEGMENT_ACTIONS.get(segment_label, "Standard retention monitoring.")


def calculate_segment_revenue_share(rfm_df, segment_col="KMeans_Label"):
    """
    Computes what share of TOTAL customer monetary value each segment
    represents - distinct from customer COUNT share. A segment can be
    small in headcount but large in revenue share (e.g. Champions),
    which is exactly the kind of insight a stakeholder needs to see
    explicitly rather than infer from two separate charts.
    """
    by_segment = rfm_df.groupby(segment_col)["Monetary"].sum().reset_index()
    by_segment.columns = [segment_col, "Total_Monetary"]
    total = by_segment["Total_Monetary"].sum()
    by_segment["Revenue_Share_Pct"] = 100 * by_segment["Total_Monetary"] / total if total > 0 else 0
    return by_segment.sort_values("Total_Monetary", ascending=False)


def filter_churn_predictions(test_preds_df, risk_level=None, min_proba=0.0):
    """
    Applies the risk-level and minimum-probability filters used by
    the churn risk explorer table. Returns a filtered copy, leaving
    the original dataframe untouched (important since Streamlit
    re-runs the whole script on every interaction - we never want to
    mutate cached data in place).
    """
    filtered = test_preds_df.copy()
    filtered["risk_level"] = bin_churn_risk(filtered["pred_proba"])

    if risk_level and risk_level != "All":
        filtered = filtered[filtered["risk_level"] == risk_level]

    filtered = filtered[filtered["pred_proba"] >= min_proba]

    return filtered.sort_values("pred_proba", ascending=False)
