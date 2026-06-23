"""
RetailPulse Dashboard - Customer Dashboard Page (Day 17 Expansion)
=======================================================================
Day 15 built a SKELETON version of this page. Day 17's job, per the
project plan, is:
  "Customer segmentation and churn risk dashboard"

This page now has THREE tabs:
  1. Segment Overview     - RFM segment breakdown, revenue share, profiles
  2. Churn Risk Explorer  - filterable, sortable churn risk table
  3. Churn Explainability - what drives churn risk (feature importance)

WHY THREE TABS HERE TOO?
Same reasoning as Day 16's forecast page - segmentation and churn are
conceptually two halves of "customer health," but each has enough
depth (multiple charts, a filterable table, an explainability view)
that cramming everything into one un-tabbed scroll would be
overwhelming and hard to navigate during a live demo.
"""
import plotly.express as px
import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utils.data_loader import (
    safe_load, load_rfm_clustered, load_churn_features,
    load_churn_test_predictions, load_permutation_importance,
    load_json_metrics
)
from utils.segment_utils import (
    build_segment_profile, bin_churn_risk, get_segment_action,
    calculate_segment_revenue_share, filter_churn_predictions,
    SEGMENT_ACTIONS, SEGMENT_COLOR_MAP
)

st.title("👥 Customer Dashboard")
st.caption("RFM segmentation and churn risk analysis")

# ============================================================
# LOAD DATA (shared across all tabs)
# ============================================================
rfm = safe_load(load_rfm_clustered)
churn_metrics = load_json_metrics("churn_metrics.json")
test_preds = safe_load(load_churn_test_predictions)
perm_importance = safe_load(load_permutation_importance)

if rfm is None:
    st.stop()

has_segments = "KMeans_Label" in rfm.columns
segment_map = {
    0: "Loyal Customers",
    1: "Champions",
    2: "At Risk",
    3: "Lost Customers"
}

if "KMeans_Label" in rfm.columns:
    rfm["Segment"] = rfm["KMeans_Label"].map(segment_map)

# ============================================================
# TOP-LEVEL KPI ROW
# ============================================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Customers", f"{len(rfm):,}")

with col2:
    if has_segments:
        n_champions = (rfm["KMeans_Label"] == "Champions").sum()
        st.metric("Champions", f"{n_champions:,}",
                   f"{100*n_champions/len(rfm):.1f}% of base")
    else:
        st.metric("Champions", "N/A")

with col3:
    if churn_metrics:
        st.metric("Churn Model AUC-ROC", f"{churn_metrics['auc_roc']:.3f}",
                   help="Target: >= 0.88")
    else:
        st.metric("Churn Model AUC-ROC", "N/A")

with col4:
    if churn_metrics:
        st.metric("Observed Churn Rate", f"{churn_metrics['churn_rate']*100:.1f}%")
    else:
        st.metric("Observed Churn Rate", "N/A")

st.divider()

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3 = st.tabs([
    "🧩 Segment Overview", "⚠️ Churn Risk Explorer", "🔍 Churn Explainability"
])

# ============================================================
# TAB 1: SEGMENT OVERVIEW
# ============================================================
with tab1:
    if not has_segments:
        st.info("Segment labels (KMeans_Label) not found - run Day 3 notebook first.")
    else:
        st.subheader("Customer Segments")
        
        profile = build_segment_profile(rfm)
        
        profile["Segment"] = profile["KMeans_Label"].map(segment_map)
        
        rev_share = calculate_segment_revenue_share(rfm)
        
        if "KMeans_Label" in rev_share.columns:
            rev_share["Segment"] = rev_share["KMeans_Label"].map(segment_map)
        
        left_col, right_col = st.columns(2)
        
        with left_col:
        
            st.markdown("### Customer Segment Distribution")
        
            segment_counts = rfm["Segment"].value_counts()
        
            fig = px.pie(
                values=segment_counts.values,
                names=segment_counts.index,
                hole=0.4,
                title="Customer Segments"
            )
        
            st.plotly_chart(fig, use_container_width=True)
        
        with right_col:
        
            st.markdown("### Revenue Share by Segment")
        
            fig = px.bar(
                rev_share,
                x="Segment",
                y="Revenue_Share_Pct",
                color="Segment",
                title="Revenue Share by Segment"
            )
        
            st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        st.subheader("Segment Profiles (Average RFM Values)")
        
        display_profile = profile[
            [
                "Segment",
                "Count",
                "Avg_Recency",
                "Avg_Frequency",
                "Avg_Monetary",
                "Pct_of_Customers"
            ]
        ]
        
        st.dataframe(
            display_profile.style.format({
                "Avg_Recency": "{:.1f}",
                "Avg_Frequency": "{:.1f}",
                "Avg_Monetary": "£{:,.2f}",
                "Pct_of_Customers": "{:.1f}%"
            }),
            width="stretch"
        )
        
        st.divider()
        
        st.subheader("Recency vs Monetary Analysis")
        
        fig = px.scatter(
            rfm,
            x="Recency",
            y="Monetary",
            color="Segment",
            size="Frequency",
            hover_data=["Frequency"],
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.caption(
            "Lower Recency (more recent buyers) and higher Monetary "
            "(bigger spenders) is the ideal top-left region."
        )
        
        st.divider()
        
        st.subheader("📊 Average Segment Performance")
        
        segment_summary = (
            rfm.groupby("Segment")
            [["Recency", "Frequency", "Monetary"]]
            .mean()
            .reset_index()
        )
        
        fig = px.bar(
            segment_summary,
            x="Segment",
            y="Monetary",
            color="Segment",
            title="Average Monetary Value by Segment"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        st.subheader("Recommended Actions per Segment")
        
        for _, row in profile.iterrows():
        
            seg_name = row["Segment"]
        
            with st.expander(
                f"{seg_name} ({int(row['Count'])} customers, {row['Pct_of_Customers']:.1f}%)"
            ):
        
                m1, m2, m3 = st.columns(3)
        
                with m1:
                    st.metric(
                        "Avg Recency",
                        f"{row['Avg_Recency']:.0f} days"
                    )
        
                with m2:
                    st.metric(
                        "Avg Frequency",
                        f"{row['Avg_Frequency']:.1f}"
                    )
        
                with m3:
                    st.metric(
                        "Avg Monetary",
                        f"£{row['Avg_Monetary']:,.0f}"
                    )
        
                st.info(
                    f"Recommended action: {get_segment_action(seg_name)}"
                )
        
        st.divider()
        
        with st.expander("View full RFM table"):
            st.dataframe(rfm, width="stretch")
# ============================================================
# TAB 2: CHURN RISK EXPLORER
# ============================================================
with tab2:
    if test_preds is None:
        st.info("Churn predictions not found - run Day 9 notebook first.")
    else:
        st.subheader("Churn Risk Explorer")
        st.markdown(
            "Filter customers by predicted churn risk level. This view "
            "is designed for a marketing/retention team to identify "
            "WHO to target with retention offers, not just WHETHER the "
            "model performs well in aggregate."
        )

        filter_col1, filter_col2 = st.columns([1, 2])

        with filter_col1:
            risk_filter = st.selectbox(
                "Risk level", ["All", "High", "Medium", "Low"]
            )

        with filter_col2:
            min_proba = st.slider(
                "Minimum churn probability", min_value=0.0, max_value=1.0,
                value=0.0, step=0.05
            )

        st.caption(
            "Risk bands: Low < 30%, Medium 30-60%, High >= 60% predicted "
            "churn probability."
        )

        filtered = filter_churn_predictions(test_preds, risk_level=risk_filter, min_proba=min_proba)

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Customers Shown", f"{len(filtered):,}")
        with m2:
            if len(filtered) > 0:
                actual_churn_rate_in_view = filtered["actual"].mean() * 100
                st.metric("Actual Churn Rate (in view)", f"{actual_churn_rate_in_view:.1f}%")
            else:
                st.metric("Actual Churn Rate (in view)", "N/A")
        with m3:
            if len(filtered) > 0:
                st.metric("Avg Predicted Probability", f"{filtered['pred_proba'].mean()*100:.1f}%")
            else:
                st.metric("Avg Predicted Probability", "N/A")

        st.dataframe(
            filtered.style.format({"pred_proba": "{:.1%}"}),
            width="stretch"
        )

        st.divider()

        st.subheader("Risk Distribution")
        all_with_risk = test_preds.copy()
        all_with_risk["risk_level"] = bin_churn_risk(all_with_risk["pred_proba"])
        risk_counts = all_with_risk["risk_level"].value_counts().reindex(["Low", "Medium", "High"]).fillna(0)
        st.bar_chart(risk_counts)

# ============================================================
# TAB 3: CHURN EXPLAINABILITY
# ============================================================
with tab3:
    st.subheader("What Drives Churn Risk?")
    st.markdown(
        "This view summarizes which features the churn model relies on "
        "most, computed via **permutation importance** in Day 11 "
        "(measuring how much AUC-ROC drops when a feature's values are "
        "shuffled - a more reliable, model-agnostic signal than "
        "XGBoost's built-in gain-based importance alone)."
    )

    if perm_importance is None:
        st.info("Permutation importance data not found - run Day 11 notebook first.")
    else:
        sort_col = "Importance_Mean" if "Importance_Mean" in perm_importance.columns else perm_importance.columns[1]
        top_features = perm_importance.sort_values(sort_col, ascending=False)

        st.bar_chart(top_features.set_index(top_features.columns[0])[sort_col])

        st.divider()

        st.markdown("**Interpretation Guide**")
        guide_col1, guide_col2 = st.columns(2)
        with guide_col1:
            st.markdown(
                "- **High Recency** (days since last purchase) typically "
                "increases churn risk - a customer going quiet is the "
                "strongest early warning signal.\n"
                "- **Low Frequency** (few past orders) often compounds "
                "churn risk, since infrequent buyers have weaker habit "
                "formation with the brand."
            )
        with guide_col2:
            st.markdown(
                "- **High Monetary** value can sometimes REDUCE churn "
                "risk (loyal big spenders), but isn't always protective "
                "on its own without recent activity.\n"
                "- **RecencyRatio** (Recency relative to the customer's "
                "own typical rhythm) often outperforms raw Recency, "
                "since it accounts for individual buying patterns."
            )

        st.divider()
        with st.expander("View full importance table"):
            st.dataframe(top_features, width="stretch")
