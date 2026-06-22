"""
RetailPulse Dashboard - Entrypoint File
=========================================
This is the file you run with: streamlit run app.py

WHAT THIS FILE DOES:
This is the "router" for the whole multi-page app. Streamlit re-runs this
ENTIRE file on every interaction (button click, page switch, etc.) - this is
how Streamlit works under the hood: there is no separate backend server
logic, the script just re-executes top to bottom each time something changes.

We use the MODERN st.Page + st.navigation API (the current recommended
approach as of Streamlit's official docs), instead of the older "just drop
files in a pages/ folder" approach. This gives us full control over:
  - The exact order pages appear in the sidebar
  - Custom icons per page
  - Custom titles per page
  - Grouping pages into sections (Overview / Operations / Forecast / Admin)

ANY code written in THIS file (outside of the page definitions) runs on
EVERY page load - this is where we put shared elements like the sidebar
logo, global CSS, or a shared "last data refresh" timestamp.
"""

import streamlit as st

# ============================================================
# PAGE CONFIG - must be the FIRST Streamlit command in the app
# ============================================================
st.set_page_config(
    page_title="RetailPulse Dashboard",
    page_icon="📊",
    layout="wide",                  # use the full browser width, not a centered column
    initial_sidebar_state="expanded"
)

# ============================================================
# SHARED ELEMENTS (run on EVERY page, since this file is the
# "picture frame" around every page per Streamlit's own docs
# language for st.navigation)
# ============================================================

# Load shared CSS (defined once, applies app-wide)
with open("utils/styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Sidebar branding - shown above the navigation menu on every page
with st.sidebar:
    st.markdown("## 📊 RetailPulse")
    st.caption("AI-Powered Customer Analytics & Demand Forecasting")
    st.divider()

# ============================================================
# DEFINE EVERY PAGE USING st.Page
# ============================================================
# st.Page(path_to_file, title=..., icon=..., default=...)
#   - path_to_file is relative to THIS entrypoint file's location
#   - title is what shows in the sidebar AND the browser tab
#   - icon accepts any emoji
#   - default=True marks which page loads first when the app opens

home_page = st.Page(
    "pages/0_home.py",
    title="Home",
    icon="🏠",
    default=True,
)

sales_page = st.Page(
    "pages/1_sales_dashboard.py",
    title="Sales Dashboard",
    icon="💰",
)

customer_page = st.Page(
    "pages/2_customer_dashboard.py",
    title="Customer Dashboard",
    icon="👥",
)

forecast_page = st.Page(
    "pages/3_forecast_dashboard.py",
    title="Forecast Dashboard",
    icon="📈",
)

inventory_page = st.Page(
    "pages/4_inventory_dashboard.py",
    title="Inventory Dashboard",
    icon="📦",
)

about_page = st.Page(
    "pages/5_about.py",
    title="About This Project",
    icon="ℹ️",
)

# ============================================================
# BUILD THE NAVIGATION MENU
# ============================================================
# Passing a DICTIONARY to st.navigation groups pages into labeled
# sections in the sidebar (this is one of the reasons we use the
# modern API instead of the plain pages/ folder auto-discovery -
# auto-discovery cannot create these section headers).

pg = st.navigation(
    {
        "Overview": [home_page],
        "Analytics": [sales_page, customer_page],
        "Operations": [forecast_page, inventory_page],
        "Project Info": [about_page],
    }
)

# ============================================================
# RUN THE CURRENTLY SELECTED PAGE
# ============================================================
# st.navigation() only BUILDS the menu and figures out which page
# the user wants - it does NOT execute that page's code. We must
# explicitly call .run() to actually render the selected page's
# content. This separation is what lets us put shared sidebar
# elements (like the branding above) BEFORE the page content runs.

pg.run()
