"""
RetailPulse Dashboard - Entrypoint File
=========================================
See Day 15 for full design rationale (st.Page/st.navigation choice,
why shared elements live here, etc.)
"""

import streamlit as st

st.set_page_config(
    page_title="RetailPulse Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

with open("utils/styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

with st.sidebar:

    st.markdown("""
    # 📊 RetailPulse

    ### AI Retail Analytics Platform

    ---
    """)

    st.success("System Status: Online")

    st.metric(
        "Forecast Accuracy",
        "88.8%"
    )

    st.metric(
        "Churn AUC",
        "0.91"
    )

    st.divider()

home_page = st.Page("pages/0_home.py", title="Home", icon="🏠", default=True)
sales_page = st.Page("pages/1_sales_dashboard.py", title="Sales Dashboard", icon="💰")
customer_page = st.Page("pages/2_customer_dashboard.py", title="Customer Dashboard", icon="👥")
forecast_page = st.Page("pages/3_forecast_dashboard.py", title="Forecast Dashboard", icon="📈")
inventory_page = st.Page("pages/4_inventory_dashboard.py", title="Inventory Dashboard", icon="📦")
realtime_page = st.Page("pages/6_realtime_alerts.py", title="Real-Time Alerts", icon="🔴")
export_page = st.Page("pages/7_export_center.py", title="Export Center", icon="⬇️")
about_page = st.Page("pages/5_about.py", title="About This Project", icon="ℹ️")

pg = st.navigation({
    "Overview": [home_page],
    "Analytics": [sales_page, customer_page],
    "Operations": [forecast_page, inventory_page, realtime_page],
    "Tools": [export_page],
    "Project Info": [about_page],
})

pg.run()
