"""
RetailPulse Dashboard - Shared Data Loading Utilities
========================================================
See Day 15 for full documentation of this module's design rationale
(caching strategy, why a separate module, safe_load error handling).
"""

import pandas as pd
import json
import os
import streamlit as st

DATA_DIR = "../data"
MODELS_DIR = "../models"


@st.cache_data
def load_clean_retail():
    path = os.path.join(DATA_DIR, "clean_retail.csv")
    df = pd.read_csv(path, parse_dates=["InvoiceDate"])
    return df


@st.cache_data
def load_rfm_clustered():
    path = os.path.join(DATA_DIR, "rfm_clustered.csv")
    return pd.read_csv(path, dtype={"Customer ID": str})


@st.cache_data
def load_daily_revenue():
    path = os.path.join(DATA_DIR, "daily_revenue_full.csv")
    return pd.read_csv(path, parse_dates=["Date"])


@st.cache_data
def load_hybrid_forecast_results():
    path = os.path.join(DATA_DIR, "hybrid_forecast_results.csv")
    return pd.read_csv(path, parse_dates=["ds"])


@st.cache_data
def load_prophet_ready():
    """Loads the full historical daily revenue series used to train
    the forecasting models (Day 4 output) - needed on Day 16 to show
    historical context alongside the forecast."""
    path = os.path.join(DATA_DIR, "prophet_ready.csv")
    return pd.read_csv(path, parse_dates=["ds"])


@st.cache_data
def load_churn_features():
    path = os.path.join(DATA_DIR, "churn_features.csv")
    return pd.read_csv(path)


@st.cache_data
def load_churn_test_predictions():
    path = os.path.join(DATA_DIR, "churn_test_predictions.csv")
    return pd.read_csv(path)


@st.cache_data
def load_inventory_recommendations():
    path = os.path.join(DATA_DIR, "reorder_recommendations.csv")
    return pd.read_csv(path)


@st.cache_data
def load_inventory_parameters():
    path = os.path.join(DATA_DIR, "inventory_parameters.csv")
    return pd.read_csv(path)


@st.cache_data
def load_abc_classification():
    path = os.path.join(DATA_DIR, "abc_classification.csv")
    return pd.read_csv(path)


@st.cache_data
def load_json_metrics(filename):
    path = os.path.join(MODELS_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)


@st.cache_data
def load_permutation_importance():
    """Loads the Day 11 permutation importance table for the churn
    model - used by Day 17's churn explainer view to show WHICH
    features drive churn risk most, at a population level."""
    path = os.path.join(DATA_DIR, "permutation_importance.csv")
    return pd.read_csv(path)


def safe_load(loader_fn, *args, **kwargs):
    try:
        return loader_fn(*args, **kwargs)
    except FileNotFoundError as e:
        st.warning(
            f"Data file not found: `{e.filename}`. "
            "Please make sure the corresponding Day notebook has been run "
            "and its output saved to the data/ folder."
        )
        return None
