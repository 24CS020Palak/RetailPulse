"""
RetailPulse Dashboard - About This Project Page
===================================================
A simple static info page. Useful for a live demo per the spec's
"Live Demo Requirements" section ("Include brief instructions on demo
page if non-obvious") - this page doubles as that instruction page.
"""

import streamlit as st

st.title("ℹ️ About RetailPulse")

st.markdown(
"""
**RetailPulse** is an end-to-end data science platform that ingests
sales, customer, and inventory data to deliver demand forecasts,
customer segmentation, churn prediction, and inventory optimization
recommendations.

### Technology Stack
- **Language:** Python 3.11
- **Data Processing:** Pandas, NumPy, Scikit-learn
- **Forecasting:** Prophet + LSTM (PyTorch) hybrid ensemble
- **Churn Prediction:** XGBoost + SHAP explainability
- **Dashboard:** Streamlit (this app)
- **Experiment Tracking:** MLflow
- **Monitoring:** Evidently AI (drift detection)
- **Orchestration:** Apache Airflow (automated retraining)

### Dataset
UCI Online Retail II - approximately 1 million transactions from a
UK-based online gift retailer, covering December 2009 to December 2011.

### How to Use This Dashboard
1. Use the sidebar to navigate between pages.
2. Each analytics page has its own filters in the sidebar when relevant.
3. The Forecast Dashboard includes an interactive "what-if" slider to
   explore different Prophet/LSTM blending weights live.
4. If any page shows "N/A" or a warning about a missing file, it means
   the corresponding Day notebook hasn't been run yet to produce that
   output file.

### Project Status
This dashboard reflects work completed through Week 2 (Day 14) of the
RetailPulse project plan. Pages will gain additional interactivity
(deeper what-if analysis, real-time alerts, export functionality) in
upcoming Week 3 days.
"""
)

st.divider()
st.caption("Built as part of the Zidio Development Data Science & Analytics program.")
