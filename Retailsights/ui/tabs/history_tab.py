# ui/tabs/history_tab.py
from __future__ import annotations

from datetime import date, datetime, timedelta

import streamlit as st

from ...services.analytics_service import load_sales_for_period
from ..components import render_sales_dashboard, section_header


def render_history_tab(state):
    """
    View historical sales stored in MySQL.
    Works with:
        state["current_shop"]
    """
    st.header("📚 History & Reports")

    shop = state.get("current_shop")
    if not shop:
        st.error("No shop selected.")
        return

    shop_id = shop["id"]

    # --- Date selector ---
    st.write("### Select date range")

    today = date.today()
    default_start = today - timedelta(days=30)

    col1, col2 = st.columns(2)
    start_date = col1.date_input("Start date", value=default_start)
    end_date = col2.date_input("End date", value=today)

    if start_date > end_date:
        st.error("Start date must be <= end date")
        return

    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date + timedelta(days=1), datetime.min.time())

    # --- Load DB ---
    st.write("### Loading sales...")
    df = load_sales_for_period(shop_id, start_dt, end_dt)

    if df.empty:
        st.info("No sales found in this period.")
        return

    section_header("Performance Summary")
    render_sales_dashboard(df)

    with st.expander("View raw sales data"):
        st.dataframe(df)
