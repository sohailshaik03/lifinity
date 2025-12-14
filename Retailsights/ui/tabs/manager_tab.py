# ui/tabs/manager_tab.py
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from ...services.managers_services import compute_manager_metrics
from ..components import section_header


def _render_top_kpis(metrics: dict):
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Revenue – last 7 days", f"£{metrics['rev_last7']:.2f}")

    if metrics["rev_change_pct"] is not None:
        col2.metric(
            "Vs previous 7 days",
            f"{metrics['rev_change_pct']:+.1f}%",
            help="Change in revenue vs the 7 days before that.",
        )
    else:
        col2.metric("Vs previous 7 days", "N/A")

    col3.metric("Revenue – last 30 days", f"£{metrics['rev_last30']:.2f}")
    col4.metric("Waste cost – last 30 days", f"£{metrics['total_waste_cost']:.2f}")


def _render_revenue_trend(df_last30: pd.DataFrame):
    st.subheader("📈 Revenue trend – last 30 days")

    if df_last30 is None or df_last30.empty:
        st.info("No sales data in the last 30 days.")
        return

    rev_by_day = (
        df_last30.groupby("date_only")["revenue"]
        .sum()
        .reset_index()
        .sort_values("date_only")
    )

    fig = px.line(
        rev_by_day,
        x="date_only",
        y="revenue",
        title="Daily revenue (30 days)",
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_waste_chart(df_waste: pd.DataFrame):
    st.subheader("♻️ Waste by reason – last 30 days")

    if df_waste is None or df_waste.empty:
        st.info("No waste records in the last 30 days.")
        return

    df = df_waste.copy()
    df["waste_reason"] = df["waste_reason"].fillna("Unspecified")
    df["estimated_cost_loss"] = pd.to_numeric(
        df["estimated_cost_loss"], errors="coerce"
    ).fillna(0.0)

    waste_by_reason = (
        df.groupby("waste_reason")["estimated_cost_loss"]
        .sum()
        .reset_index()
        .sort_values("estimated_cost_loss", ascending=False)
    )

    fig = px.bar(
        waste_by_reason,
        x="waste_reason",
        y="estimated_cost_loss",
        title="Waste cost by reason",
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_expiring_stock(metrics: dict):
    st.subheader("⏰ Stock at risk – expiring in next 3 days")

    col1, col2 = st.columns([1, 3])
    col1.metric("Stock value at risk", f"£{metrics['expiring_value']:.2f}")

    df_exp = metrics["df_expiring"]
    if df_exp is None or df_exp.empty:
        col2.info("No batches expiring in the next 3 days.")
        return

    df = df_exp.copy()
    df["sell_price"] = pd.to_numeric(df["sell_price"], errors="coerce").fillna(0.0)
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)
    df["stock_value"] = df["sell_price"] * df["quantity"]

    display_cols = [
        "id",
        "product_name",
        "barcode",
        "quantity",
        "expiry_date",
        "sell_price",
        "stock_value",
    ]

    df_display = (
        df[display_cols]
        .sort_values(["expiry_date", "stock_value"], ascending=[True, False])
        .head(10)
    )

    col2.markdown("**Top at-risk items (next 3 days)**")
    col2.dataframe(df_display)

    st.info(
        "Tip: focus reductions and front-facing on the highest stock value items with the closest expiry dates."
    )


def _render_category_performance(cat_last30: pd.DataFrame):
    st.subheader("🧺 Category performance – last 30 days")

    if cat_last30 is None or cat_last30.empty:
        st.info("No category data in the last 30 days.")
        return

    fig = px.bar(
        cat_last30,
        x="category",
        y="revenue",
        title="Revenue by category (30 days)",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        cat_last30.rename(
            columns={
                "category": "Category",
                "revenue": "Revenue (£)",
                "units_sold": "Units Sold",
            }
        )
    )


def _render_insights(metrics: dict):
    st.subheader("💡 Manager insights")

    bullets = []

    if metrics["rev_change_pct"] is not None:
        if metrics["rev_change_pct"] > 5:
            bullets.append(
                f"Revenue is **up {metrics['rev_change_pct']:.1f}%** vs the previous week – current promotions and stock levels seem effective."
            )
        elif metrics["rev_change_pct"] < -5:
            bullets.append(
                f"Revenue is **down {metrics['rev_change_pct']:.1f}%** vs the previous week – review pricing, dead stock and staff rota."
            )
        else:
            bullets.append(
                "Revenue is relatively stable compared to the previous week."
            )

    if metrics["total_waste_cost"] > 0:
        bullets.append(
            f"Total waste cost in the last 30 days is **£{metrics['total_waste_cost']:.2f}** – consider earlier reductions and tighter ordering."
        )

    if metrics["expiring_value"] > 0:
        bullets.append(
            f"You have around **£{metrics['expiring_value']:.2f}** of stock expiring in the next 3 days – prioritise reductions and off-shelf promotions."
        )

    if not bullets:
        st.write("No critical alerts – the shop looks healthy based on recent data.")
    else:
        for b in bullets:
            st.write(f"- {b}")


# ------------------------------------------------------------
# PUBLIC ENTRY POINT
# ------------------------------------------------------------
def render_manager_tab(state):
    """
    Main entry point for Manager Dashboard tab.
    """
    st.header("📊 Manager Intelligence Dashboard")

    shop = state.get("active_shop")
    if not shop:
        st.error("No active shop selected.")
        return

    shop_id = shop["id"]

    # Load all metrics
    metrics = compute_manager_metrics(shop_id)

    # Top KPIs
    section_header("Store KPIs")
    _render_top_kpis(metrics)

    st.markdown("---")

    # Two-column visuals: revenue trend + waste breakdown
    col_left, col_right = st.columns(2)
    with col_left:
        _render_revenue_trend(metrics["df_last30"])
    with col_right:
        _render_waste_chart(metrics["df_waste"])

    st.markdown("---")

    # Expiring stock
    _render_expiring_stock(metrics)

    st.markdown("---")

    # Category performance
    _render_category_performance(metrics["cat_last30"])

    st.markdown("---")

    # Text insights
    _render_insights(metrics)
