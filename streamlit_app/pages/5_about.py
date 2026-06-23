"""
RetailPulse Dashboard - About This Project Page
===================================================
A simple static info page. Useful for a live demo per the spec's
"Live Demo Requirements" section ("Include brief instructions on demo
page if non-obvious") - this page doubles as that instruction page.
"""

import streamlit as st

st.title("ℹ️ About RetailPulse")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Revenue", "£17.7M")

with col2:
    st.metric("Customers", "5,878")

with col3:
    st.metric("Forecast MAPE", "11.2%")

with col4:
    st.metric("Churn AUC", "0.814")

st.divider()

st.markdown("""
**RetailPulse** is an end-to-end data science platform that ingests
sales, customer, and inventory data to deliver demand forecasts,
customer segmentation, churn prediction, and inventory optimization
recommendations.
""")

st.subheader("🛠 Technology Stack")

tech1, tech2, tech3 = st.columns(3)

with tech1:
    st.info("""
    Data Science

    - Pandas
    - NumPy
    - Scikit-Learn
    - XGBoost
    """)

with tech2:
    st.info("""
    Forecasting

    - Prophet
    - LSTM
    - PyTorch
    - Hybrid Ensemble
    """)

with tech3:
    st.info("""
    Deployment

    - Streamlit
    - MLflow
    - Airflow
    - Evidently AI
    """)

st.divider()

st.divider()

st.subheader("🏗 RetailPulse Workflow")

st.markdown("""
📥 Raw Retail Data

⬇️

🧹 Data Cleaning & Feature Engineering

⬇️

👥 Customer Segmentation

⬇️

📈 Demand Forecasting

⬇️

📦 Inventory Optimization

⬇️

🚨 Real-Time Monitoring

⬇️

🌐 Streamlit Dashboard
""")
st.divider()

st.subheader("📊 Dataset Overview")

d1, d2, d3, d4 = st.columns(4)

with d1:
    st.metric("Transactions", "1M+")

with d2:
    st.metric("Customers", "5,878")

with d3:
    st.metric("Countries", "37")

with d4:
    st.metric("Period", "2009-2011")

st.subheader("🏆 Key Achievements")

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Forecast Accuracy", "88.8%")

with c2:
    st.metric("Churn AUC", "0.814")

with c3:
    st.metric("Inventory Reduction", "32%")
st.caption("Built as part of the Zidio Development Data Science & Analytics program.")
