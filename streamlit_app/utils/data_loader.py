"""
RetailPulse Dashboard - Shared Data Loading Utilities
========================================================
Every page in this app needs to load data that was produced by the Days
1-13 notebooks (clean_retail.csv, rfm_clustered.csv, hybrid_forecast
results, churn predictions, inventory recommendations, etc.).

WHY A SEPARATE MODULE INSTEAD OF COPY-PASTING LOADING CODE INTO EVERY PAGE?
  1. DRY (Don't Repeat Yourself) - if a file path or column name changes,
     we fix it in ONE place instead of five page files.
  2. Caching lives here once - every page benefits automatically.
  3. Pages stay focused on PRESENTATION logic, not data plumbing.

WHY @st.cache_data?
Streamlit re-runs the ENTIRE script on every single user interaction
(clicking a button, moving a slider, switching pages). Without caching,
we would re-read large CSV files from disk dozens of times per session,
making the app painfully slow. @st.cache_data tells Streamlit: "run this
function once, remember the result, and reuse it until the underlying
code or input arguments change."
"""

import pandas as pd
import json
import os
import streamlit as st

# All paths are relative to the streamlit_app/ folder (since `streamlit run`
# is executed from there). Adjust DATA_DIR / MODELS_DIR if your folder
# layout differs from the Day 1-14 notebooks' ../data and ../models.
DATA_DIR = "../data"
MODELS_DIR = "../models"


@st.cache_data
def load_clean_retail():
    """Loads the main cleaned transaction-level dataset (Day 2 output)."""
    path = os.path.join(DATA_DIR, "clean_retail.csv")
    df = pd.read_csv(path, parse_dates=["InvoiceDate"])
    return df


@st.cache_data
def load_rfm_clustered():
    """Loads customer-level RFM features with K-Means/DBSCAN labels (Day 3)."""
    path = os.path.join(DATA_DIR, "rfm_clustered.csv")
    return pd.read_csv(path, dtype={"Customer ID": str})


@st.cache_data
def load_daily_revenue():
    """Loads the daily aggregated revenue time series with engineered
    features - rolling averages, lags, etc. (Day 2/4 output)."""
    path = os.path.join(DATA_DIR, "daily_revenue_full.csv")
    return pd.read_csv(path, parse_dates=["Date"])


@st.cache_data
def load_hybrid_forecast_results():
    """Loads the Day 8 hybrid Prophet+LSTM ensemble test-set predictions."""
    path = os.path.join(DATA_DIR, "hybrid_forecast_results.csv")
    return pd.read_csv(path, parse_dates=["ds"])


@st.cache_data
def load_churn_features():
    """Loads the full customer-level churn feature table (Day 9)."""
    path = os.path.join(DATA_DIR, "churn_features.csv")
    return pd.read_csv(path)


@st.cache_data
def load_churn_test_predictions():
    """Loads the held-out test set churn predictions (Day 9)."""
    path = os.path.join(DATA_DIR, "churn_test_predictions.csv")
    return pd.read_csv(path)


@st.cache_data
def load_inventory_recommendations():
    """Loads the final reorder recommendation table (Day 10)."""
    path = os.path.join(DATA_DIR, "reorder_recommendations.csv")
    return pd.read_csv(path)


@st.cache_data
def load_inventory_parameters():
    """Loads the full safety stock / ROP / EOQ parameter table (Day 10)."""
    path = os.path.join(DATA_DIR, "inventory_parameters.csv")
    return pd.read_csv(path)


@st.cache_data
def load_abc_classification():
    """Loads the ABC product classification table (Day 10)."""
    path = os.path.join(DATA_DIR, "abc_classification.csv")
    return pd.read_csv(path)


@st.cache_data
def load_json_metrics(filename):
    """
    Generic loader for any of the small JSON metric/config files saved
    throughout Days 8-14, e.g. 'churn_metrics.json', 'hybrid_config.json'.
    Returns None if the file doesn't exist yet, so pages can show a
    friendly "not available" message instead of crashing.
    """
    path = os.path.join(MODELS_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)


def safe_load(loader_fn, *args, **kwargs):
    """
    Wraps any loader function so that a missing file shows a friendly
    Streamlit warning INSTEAD of crashing the whole page with a raw
    FileNotFoundError traceback. This matters a lot for a checkpoint
    demo - a graceful "data not ready yet" message looks far more
    professional than a red Python traceback on screen.
    """
    try:
        return loader_fn(*args, **kwargs)
    except FileNotFoundError as e:
        st.warning(
            f"Data file not found: `{e.filename}`. "
            "Please make sure the corresponding Day notebook has been run "
            "and its output saved to the data/ folder."
        )
        return None
