"""
RetailPulse Dashboard - Export Center Page (Day 20)
========================================================
Project plan, Day 20: "Export functionality (CSV/PDF reports)"

WHY A DEDICATED EXPORT PAGE INSTEAD OF JUST PER-PAGE DOWNLOAD BUTTONS?
Day 16 already added a per-page CSV download button on the Forecast
Dashboard (one dataset, one button, scoped to that page's content).
Day 20's job is broader: give a stakeholder ONE place to grab
EVERYTHING at once - either as a single ZIP of every available
dataset, or as a polished PDF business summary they can read without
opening the dashboard at all. This is the natural "export hub" a real
analytics platform would have, separate from the inline per-chart
export buttons scattered across individual pages.
"""

import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime
from streamlit_extras.metric_cards import style_metric_cards

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utils.data_loader import (
    safe_load, load_clean_retail, load_rfm_clustered, load_daily_revenue,
    load_hybrid_forecast_results, load_churn_features, load_churn_test_predictions,
    load_inventory_recommendations, load_inventory_parameters, load_abc_classification,
    load_json_metrics
)
from utils.segment_utils import build_segment_profile
from utils.export_utils import build_csv_zip_bundle, generate_business_report

st.title("⬇️ Export Center")
st.caption("Download data and reports for offline use or sharing with stakeholders")

# ============================================================
# LOAD EVERYTHING (each load is independently optional - the page
# degrades gracefully and shows exactly what's actually available)
# ============================================================
clean_retail = safe_load(load_clean_retail)
rfm = safe_load(load_rfm_clustered)
daily_revenue = safe_load(load_daily_revenue)
forecast_results = safe_load(load_hybrid_forecast_results)
churn_features = safe_load(load_churn_features)
churn_test_preds = safe_load(load_churn_test_predictions)
inventory_recs = safe_load(load_inventory_recommendations)
inventory_params = safe_load(load_inventory_parameters)
abc_data = safe_load(load_abc_classification)

hybrid_config = load_json_metrics("hybrid_config.json")
churn_metrics = load_json_metrics("churn_metrics.json")
inventory_config = load_json_metrics("inventory_config.json")

# ============================================================
# DATA AVAILABILITY OVERVIEW
# ============================================================
st.subheader("Data Availability")

availability = [
    ("Clean Transaction Data", clean_retail),
    ("Customer RFM Segments", rfm),
    ("Daily Revenue Series", daily_revenue),
    ("Forecast Results", forecast_results),
    ("Churn Features", churn_features),
    ("Churn Test Predictions", churn_test_preds),
    ("Inventory Recommendations", inventory_recs),
    ("Inventory Parameters", inventory_params),
    ("ABC Classification", abc_data),
]

n_available = sum(1 for _, df in availability if df is not None)
st.progress(n_available / len(availability))
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Datasets Available", n_available)

with col2:
    st.metric("Total Datasets", len(availability))

with col3:
    st.metric(
        "Forecast Status",
        "Ready" if forecast_results is not None else "Missing"
    )

with col4:
    st.metric(
        "PDF Reports",
        "Enabled"
    )

style_metric_cards()
st.caption(f"{n_available} of {len(availability)} datasets available for export")

with st.expander("View detailed availability checklist"):
    for name, df in availability:
        status = f"✅ Available ({len(df):,} rows)" if df is not None else "❌ Not found"
        st.markdown(f"- **{name}**: {status}")

st.divider()

# ============================================================
# TABS: CSV Export | PDF Report | Scheduled Export Info
# ============================================================
tab1, tab2, tab3 = st.tabs(["📁 CSV Exports", "📄 PDF Business Report", "ℹ️ About Exports"])

# ============================================================
# TAB 1: CSV EXPORTS
# ============================================================
with tab1:
    all_datasets = {
        "clean_retail_transactions": clean_retail,
        "customer_rfm_segments": rfm,
        "daily_revenue_timeseries": daily_revenue,
        "forecast_results": forecast_results,
        "churn_features": churn_features,
        "churn_test_predictions": churn_test_preds,
        "inventory_reorder_recommendations": inventory_recs,
        "inventory_parameters": inventory_params,
        "abc_product_classification": abc_data,
    }
    
    available_datasets = {
        k: v for k, v in all_datasets.items()
        if v is not None
    }
    
    st.subheader("📊 Export Statistics")
    
    e1, e2, e3 = st.columns(3)
    
    with e1:
        st.metric("Available Datasets", len(available_datasets))
    
    with e2:
        total_rows = sum(
            len(df) for df in available_datasets.values()
        )
        st.metric("Total Records", f"{total_rows:,}")
    
    with e3:
        st.metric("Export Formats", "CSV + PDF")
    
    st.divider()
    st.subheader("Bulk CSV Download")
    st.markdown(
        "Select which datasets to include, then download a single ZIP "
        "file containing each as a separate CSV - useful for further "
        "analysis in Excel, Power BI, or another tool outside this "
        "dashboard."
    )

    all_datasets = {
        "clean_retail_transactions": clean_retail,
        "customer_rfm_segments": rfm,
        "daily_revenue_timeseries": daily_revenue,
        "forecast_results": forecast_results,
        "churn_features": churn_features,
        "churn_test_predictions": churn_test_preds,
        "inventory_reorder_recommendations": inventory_recs,
        "inventory_parameters": inventory_params,
        "abc_product_classification": abc_data,
    }
    available_datasets = {k: v for k, v in all_datasets.items() if v is not None}
    dataset_sizes = pd.DataFrame({
        "Dataset": list(available_datasets.keys()),
        "Rows": [len(df) for df in available_datasets.values()]
    })
    
    st.bar_chart(
        dataset_sizes.set_index("Dataset")
    )

    if not available_datasets:
        st.warning("No datasets are currently available to export. Run the Day 1-13 notebooks first.")
    else:
        selected_names = st.multiselect(
            "Datasets to include",
            options=list(available_datasets.keys()),
            default=list(available_datasets.keys()),
        )

        selected_data = {name: available_datasets[name] for name in selected_names}

        if selected_data:
            zip_bytes = build_csv_zip_bundle(selected_data)
            total_rows = sum(len(df) for df in selected_data.values())

            m1, m2 = st.columns(2)
            with m1:
                st.metric("Datasets Selected", len(selected_data))
            with m2:
                st.metric("Total Rows", f"{total_rows:,}")

            st.download_button(
                label=f"⬇️ Download {len(selected_data)} CSV files (.zip)",
                data=zip_bytes,
                file_name=f"retailpulse_export_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                mime="application/zip",
            )
        else:
            st.info("Select at least one dataset above to enable download.")

    st.divider()

    st.subheader("Individual Dataset Preview & Download")
    if available_datasets:
        preview_choice = st.selectbox("Preview a dataset", list(available_datasets.keys()))
        preview_df = available_datasets[preview_choice]

        st.dataframe(preview_df.head(50), width="stretch")
        st.caption(f"Showing first 50 of {len(preview_df):,} rows")

        single_csv = preview_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=f"⬇️ Download {preview_choice}.csv",
            data=single_csv,
            file_name=f"{preview_choice}.csv",
            mime="text/csv",
        )

# ============================================================
# TAB 2: PDF BUSINESS REPORT
# ============================================================
with tab2:
    st.subheader("Report Contents")
    
    r1, r2, r3 = st.columns(3)
    
    with r1:
        st.success("Forecast Metrics")
    
    with r2:
        st.success("Customer Analytics")
    
    with r3:
        st.success("Inventory Insights")
    st.subheader("Generate PDF Business Summary")
    st.markdown(
        "Produces a polished, multi-section PDF combining headline "
        "results from forecasting, churn prediction, and inventory "
        "optimization - suitable for sharing with stakeholders who "
        "won't open the dashboard directly, or for inclusion in your "
        "project submission documentation."
    )

    st.markdown("**Choose which sections to include:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        include_forecast = st.checkbox("Demand Forecasting", value=hybrid_config is not None)
    with col2:
        include_churn = st.checkbox("Churn Prediction", value=churn_metrics is not None)
    with col3:
        include_inventory = st.checkbox("Inventory Optimization", value=inventory_config is not None)

    segment_summary_df = build_segment_profile(rfm) if (rfm is not None and "KMeans_Label" in rfm.columns) else None

    top_products_df = None
    if clean_retail is not None:
        top_products_df = (
            clean_retail.groupby("Description")["TotalRevenue"]
            .sum().sort_values(ascending=False).head(10).reset_index()
        )

    if st.button("📄 Generate PDF Report", type="primary"):
        with st.spinner("Building report..."):
            pdf_bytes = generate_business_report(
                forecast_metrics=hybrid_config if include_forecast else None,
                churn_metrics=churn_metrics if include_churn else None,
                inventory_metrics=inventory_config if include_inventory else None,
                top_products_df=top_products_df,
                segment_summary_df=segment_summary_df if include_churn else None,
                reorder_df=inventory_recs if include_inventory else None,
            )

        st.success(f"Report generated successfully ({len(pdf_bytes):,} bytes)")

        st.download_button(
            label="⬇️ Download PDF Report",
            data=pdf_bytes,
            file_name=f"RetailPulse_Business_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
        )

    st.divider()
    st.caption(
        "Sections with no underlying data available will show 'N/A' "
        "in the generated PDF rather than being silently omitted, so "
        "it's always clear what was and wasn't included."
    )

# ============================================================
# TAB 3: ABOUT EXPORTS
# ============================================================
with tab3:
    st.subheader("About These Export Tools")

    st.info("""
    RetailPulse Export Center provides:
    
    • Bulk CSV exports
    
    • PDF business reports
    
    • Dataset previews
    
    • Stakeholder-ready summaries
    
    • Offline analytics support
    """)
    st.markdown(
        """
**CSV Exports** give you the raw underlying data behind every chart
in this dashboard, for further analysis in your own tools.

**PDF Business Report** is generated fresh each time you click
"Generate," always reflecting the LATEST saved model outputs - it is
NOT a static file, so re-running any Day 1-14 notebook and refreshing
this page will produce an updated report on the next click.

**Note on production deployment:** in a real production system, this
page's manual "click to export" pattern would typically be
supplemented by a SCHEDULED export (e.g. an automated nightly PDF
emailed to stakeholders) - that would be implemented as an additional
task in the Day 13 Airflow retraining DAG, reusing this exact
`generate_business_report()` function, just triggered by a schedule
instead of a button click.
        """
    )
