# services/manager_service.py
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict

import pandas as pd

from ..repositories.expiry_repo import (get_expiring_batches,
                                      get_recent_waste_events)
from .analytics_service import load_sales_for_period


def compute_manager_metrics(shop_id: int) -> Dict[str, Any]:
    """
    Central place for manager KPIs.
    Returns both numbers and DataFrames for charts.
    """
    today = date.today()

    # --- 7-day windows ---
    last7_start = today - timedelta(days=7)
    prev7_start = today - timedelta(days=14)

    start_last7 = datetime.combine(last7_start, datetime.min.time())
    end_last7 = datetime.combine(today + timedelta(days=1), datetime.min.time())

    start_prev7 = datetime.combine(prev7_start, datetime.min.time())
    end_prev7 = datetime.combine(last7_start, datetime.min.time())

    df_last7 = load_sales_for_period(shop_id, start_last7, end_last7)
    df_prev7 = load_sales_for_period(shop_id, start_prev7, end_prev7)

    rev_last7 = df_last7["revenue"].sum() if not df_last7.empty else 0.0
    rev_prev7 = df_prev7["revenue"].sum() if not df_prev7.empty else 0.0

    if rev_prev7 > 0:
        rev_change_pct = (rev_last7 - rev_prev7) / rev_prev7 * 100.0
    else:
        rev_change_pct = None

    # --- 30-day window ---
    last30_start = today - timedelta(days=30)
    start_last30 = datetime.combine(last30_start, datetime.min.time())
    end_last30 = datetime.combine(today + timedelta(days=1), datetime.min.time())

    df_last30 = load_sales_for_period(shop_id, start_last30, end_last30)
    rev_last30 = df_last30["revenue"].sum() if not df_last30.empty else 0.0

    if not df_last30.empty and "category" in df_last30.columns:
        cat_last30 = (
            df_last30.groupby("category")
            .agg(
                revenue=("revenue", "sum"),
                units_sold=("quantity", "sum"),
            )
            .reset_index()
            .sort_values("revenue", ascending=False)
        )
    else:
        cat_last30 = pd.DataFrame(columns=["category", "revenue", "units_sold"])

    # --- Waste (last 30 days) ---
    waste_rows = get_recent_waste_events(shop_id, days_back=30)
    df_waste = pd.DataFrame(waste_rows) if waste_rows else pd.DataFrame()
    if not df_waste.empty:
        df_waste["estimated_cost_loss"] = pd.to_numeric(
            df_waste["estimated_cost_loss"], errors="coerce"
        ).fillna(0.0)
        total_waste_cost = df_waste["estimated_cost_loss"].sum()
    else:
        total_waste_cost = 0.0

    # --- Expiring stock (next 3 days) ---
    exp_rows = get_expiring_batches(shop_id, days_ahead=3)
    df_exp = pd.DataFrame(exp_rows) if exp_rows else pd.DataFrame()
    if not df_exp.empty:
        df_exp["sell_price"] = pd.to_numeric(
            df_exp["sell_price"], errors="coerce"
        ).fillna(0.0)
        df_exp["quantity"] = pd.to_numeric(df_exp["quantity"], errors="coerce").fillna(
            0
        )
        df_exp["stock_value"] = df_exp["sell_price"] * df_exp["quantity"]
        expiring_value = df_exp["stock_value"].sum()
    else:
        expiring_value = 0.0

    return {
        "rev_last7": float(rev_last7),
        "rev_prev7": float(rev_prev7),
        "rev_change_pct": float(rev_change_pct) if rev_change_pct is not None else None,
        "rev_last30": float(rev_last30),
        "df_last7": df_last7,
        "df_last30": df_last30,
        "cat_last30": cat_last30,
        "df_waste": df_waste,
        "total_waste_cost": float(total_waste_cost),
        "df_expiring": df_exp,
        "expiring_value": float(expiring_value),
    }
