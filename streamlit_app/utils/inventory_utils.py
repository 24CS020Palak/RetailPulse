"""
RetailPulse Dashboard - Inventory Calculation Utilities
============================================================
Day 18 needs a live, INTERACTIVE re-simulation of stock levels under
adjustable policy parameters (the user can drag lead time / service
level sliders and see the simulated stockout/inventory impact change
immediately) - this is different from Day 10's notebook, which ran
ONE fixed simulation and saved the result. Here the simulation itself
must be fast and parameterized so it can run live inside a Streamlit
widget callback without noticeable lag.
"""

import numpy as np
import pandas as pd
from scipy.stats import norm


def calculate_z_score(service_level_pct):
    """
    Converts a service level percentage (e.g. 95) into the
    corresponding Z-score from the standard normal distribution,
    used in the Safety Stock formula. This is the SAME logic as
    Day 10's notebook, exposed here as a reusable function so the
    dashboard's service-level slider can recompute it live.
    """
    return norm.ppf(service_level_pct / 100)


def calculate_safety_stock(std_daily_demand, lead_time_days, service_level_pct):
    """Safety Stock = Z * std_demand * sqrt(lead_time). See Day 10
    for the full derivation and business rationale."""
    z = calculate_z_score(service_level_pct)
    return z * std_daily_demand * np.sqrt(lead_time_days)


def calculate_reorder_point(avg_daily_demand, lead_time_days, safety_stock):
    """Reorder Point = expected demand during lead time + safety stock."""
    return avg_daily_demand * lead_time_days + safety_stock


def calculate_eoq(annual_demand, order_cost, holding_cost_per_unit):
    """Economic Order Quantity = sqrt(2 * D * S / H). Guards against
    a zero or negative holding cost (which would otherwise produce a
    division error or an infinite/undefined EOQ)."""
    holding_cost_per_unit = max(holding_cost_per_unit, 0.01)
    return np.sqrt((2 * annual_demand * order_cost) / holding_cost_per_unit)


def simulate_inventory_policy(demand_series, reorder_point, order_qty,
                                lead_time, initial_stock):
    """
    Simulates inventory levels day-by-day under a single (reorder_point,
    order_qty) policy. Identical logic to Day 10's notebook simulation,
    refactored here as a standalone reusable function (no notebook-only
    globals) so the dashboard can call it repeatedly with different
    parameters as the user adjusts sliders.

    Returns: (stockout_days, avg_inventory, daily_stock_levels list)
    The daily_stock_levels list is the NEW addition vs Day 10's version -
    Day 10 only needed the summary numbers, but Day 18's UI needs the
    full day-by-day trace to actually PLOT the simulated stock timeline.
    """
    stock = initial_stock
    pending_orders = []
    stockout_days = 0
    daily_levels = []

    for day, demand in enumerate(demand_series):
        arriving = [q for (d, q) in pending_orders if d == day]
        stock += sum(arriving)
        pending_orders = [(d, q) for (d, q) in pending_orders if d != day]

        if stock < demand:
            stockout_days += 1
            stock = 0
        else:
            stock -= demand

        daily_levels.append(stock)

        if stock <= reorder_point and len(pending_orders) == 0:
            pending_orders.append((day + lead_time, order_qty))

    avg_inventory = float(np.mean(daily_levels)) if daily_levels else 0.0
    return stockout_days, avg_inventory, daily_levels


def generate_demand_sequence(avg_daily_demand, std_daily_demand, n_days, seed=42):
    """
    Generates a reproducible random demand sequence for simulation.
    A FIXED seed is used (rather than true randomness) so that
    re-running the simulation with the SAME policy parameters always
    gives the SAME result - important for a dashboard where a user
    might compare two policies and expects a fair, repeatable test,
    not new random noise each time the page reruns.
    """
    rng = np.random.default_rng(seed)
    demand = rng.normal(max(avg_daily_demand, 0.1), max(std_daily_demand, 0.1), n_days)
    demand = np.clip(demand, 0, None)
    return np.round(demand).astype(int)


def compare_policies(avg_daily_demand, std_daily_demand, naive_order_qty,
                       optimized_reorder_point, optimized_order_qty,
                       lead_time_days, sim_days=180, seed=42):
    """
    Runs BOTH the naive policy (reorder at zero stock) and the
    optimized policy (reorder at calculated reorder point) against the
    SAME generated demand sequence, returning a comparison dict plus
    both daily stock-level traces for charting. This wraps Day 10's
    comparison logic into one convenience function for the dashboard.
    """
    demand_seq = generate_demand_sequence(avg_daily_demand, std_daily_demand, sim_days, seed)
    initial_stock = int(round(avg_daily_demand * 30))

    naive_stockouts, naive_avg_inv, naive_levels = simulate_inventory_policy(
        demand_seq, reorder_point=0, order_qty=naive_order_qty,
        lead_time=lead_time_days, initial_stock=initial_stock
    )
    opt_stockouts, opt_avg_inv, opt_levels = simulate_inventory_policy(
        demand_seq, reorder_point=optimized_reorder_point, order_qty=optimized_order_qty,
        lead_time=lead_time_days, initial_stock=initial_stock
    )

    stockout_reduction = (
        100 * (naive_stockouts - opt_stockouts) / naive_stockouts
        if naive_stockouts > 0 else 0.0
    )
    inventory_reduction = (
        100 * (naive_avg_inv - opt_avg_inv) / naive_avg_inv
        if naive_avg_inv > 0 else 0.0
    )

    return {
        "naive_stockout_days": naive_stockouts,
        "optimized_stockout_days": opt_stockouts,
        "naive_avg_inventory": naive_avg_inv,
        "optimized_avg_inventory": opt_avg_inv,
        "stockout_reduction_pct": stockout_reduction,
        "inventory_reduction_pct": inventory_reduction,
        "naive_daily_levels": naive_levels,
        "optimized_daily_levels": opt_levels,
        "demand_sequence": demand_seq,
    }


def classify_urgency(current_stock, reorder_point, safety_stock):
    """
    Classifies a product's restocking urgency for the dashboard's
    color-coded status column - a quick visual triage tool so a buyer
    scanning a table of 15+ products can immediately spot which ones
    need action TODAY vs which are healthy.
    """
    if current_stock <= safety_stock:
        return "Critical"
    elif current_stock <= reorder_point:
        return "Reorder Now"
    else:
        return "Healthy"
