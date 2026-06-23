"""
RetailPulse Dashboard - Forecasting Calculation Utilities
=============================================================
Day 16 introduces enough forecast-specific math (MAPE recalculation,
what-if scenario simulation, confidence interval construction) that it
deserves its own module rather than being copy-pasted inline into the
forecast page - same DRY principle as Day 15's data_loader.py.
"""

import numpy as np
import pandas as pd


def calculate_mape(actual, predicted):
    """
    Mean Absolute Percentage Error.
    Rows where actual == 0 are excluded to avoid division by zero
    (a day with zero recorded revenue would otherwise produce an
    undefined/infinite percentage error).
    """
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    mask = actual != 0
    if mask.sum() == 0:
        return np.nan
    return np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100


def calculate_mae(actual, predicted):
    """Mean Absolute Error - same units as revenue (GBP), useful
    alongside MAPE since MAPE alone can be misleading on small values."""
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    return np.mean(np.abs(actual - predicted))


def calculate_rmse(actual, predicted):
    """Root Mean Squared Error - penalizes large errors more heavily
    than MAE, useful for spotting whether a model has occasional big
    misses even if its average error looks fine."""
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    return np.sqrt(np.mean((actual - predicted) ** 2))


def blend_forecast(prophet_pred, lstm_pred, alpha):
    """
    The same hybrid ensemble formula from Day 8, exposed here so the
    What-If slider can recompute it live as the user drags alpha,
    without needing to re-import or duplicate Day 8's notebook code.
    """
    prophet_pred = np.asarray(prophet_pred, dtype=float)
    lstm_pred = np.asarray(lstm_pred, dtype=float)
    return alpha * prophet_pred + (1 - alpha) * lstm_pred


def apply_growth_scenario(forecast_values, growth_pct):
    """
    Applies a simple percentage growth/decline adjustment to a forecast
    series - the core mechanic behind the "What-If: Demand Shock"
    scenario tool. growth_pct=10 means +10% uplift, growth_pct=-15
    means a 15% decline (e.g. simulating a promotion or a downturn).
    """
    forecast_values = np.asarray(forecast_values, dtype=float)
    return forecast_values * (1 + growth_pct / 100)


def apply_seasonal_shock(dates, forecast_values, shock_start, shock_end, shock_pct):
    """
    Applies a growth/decline adjustment ONLY within a specific date
    window - simulating a targeted event like a flash sale, a stockout
    period, or a short-lived marketing campaign, rather than a
    blanket adjustment across the whole forecast horizon.
    """
    dates = pd.to_datetime(pd.Series(dates))
    forecast_values = np.asarray(forecast_values, dtype=float).copy()

    mask = (dates >= pd.Timestamp(shock_start)) & (dates <= pd.Timestamp(shock_end))
    forecast_values[mask.values] = forecast_values[mask.values] * (1 + shock_pct / 100)

    return forecast_values


def build_confidence_band(forecast_values, mape_pct, z_score=1.96):
    """
    Constructs an approximate confidence interval around a point
    forecast, using the model's OWN historical MAPE as a proxy for
    its typical error magnitude. This is a simplification compared to
    Prophet's native yhat_lower/yhat_upper (which come from proper
    posterior uncertainty estimation) - useful here because the HYBRID
    ensemble forecast doesn't have a native uncertainty estimate of
    its own, so we approximate one from the known error rate instead.

    z_score=1.96 corresponds to a ~95% confidence interval under a
    normal-distribution assumption on the percentage error.
    """
    forecast_values = np.asarray(forecast_values, dtype=float)
    error_margin = forecast_values * (mape_pct / 100) * (z_score / 1.96)
    lower = np.clip(forecast_values - error_margin, a_min=0, a_max=None)
    upper = forecast_values + error_margin
    return lower, upper


def summarize_scenario_impact(baseline_total, scenario_total):
    """
    Compares a baseline forecast total against a what-if scenario
    total and returns a small summary dict - used to power the
    "Impact Summary" metric cards on the What-If tab.
    """
    abs_diff = scenario_total - baseline_total
    pct_diff = (abs_diff / baseline_total * 100) if baseline_total != 0 else np.nan
    return {
        "baseline_total": baseline_total,
        "scenario_total": scenario_total,
        "absolute_difference": abs_diff,
        "percent_difference": pct_diff,
    }
