# ui/components.py
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from Retailsights.utils.session_manager import SessionManager


def show_top_bar(user: dict | None):
    cols = st.columns([3, 1])
    with cols[0]:
        st.markdown("### 🛒 RetailSight")
    with cols[1]:
        if user:
            st.markdown(f"**{user['full_name']}**  \n`{user['role']}`")


def show_logout_button():
    if st.sidebar.button("Logout"):
        # Clear session state
        for key in list(st.session_state.keys()):
            if key.startswith("auth_") or key in ("user", "is_authenticated", "_cookie_user_id", "_cookie_auth_token", "_auto_login_attempted"):
                del st.session_state[key]
        
        # Clear cookies
        try:
            session_mgr = SessionManager()
            session_mgr.clear_session()
        except Exception:
            pass
        
        st.rerun()


def show_support_widget():
    """Display quick support access in sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎧 Need Help?")
    
    with st.sidebar.expander("💬 Quick Support", expanded=False):
        st.markdown("""
        **📧 Email Support**  
        support@retailsight.com
        
        **⏰ Hours**  
        Mon-Fri: 9 AM - 6 PM GMT
        
        **⚡ Response Time**  
        Within 24 hours
        """)
        
        if st.button("Open Support Center", use_container_width=True):
            st.session_state["_navigate_to_support"] = True
            st.rerun()
        
        st.markdown("---")
        
        # Quick FAQ
        st.markdown("**Quick Help:**")
        st.markdown("• [Reset Password](#)")
        st.markdown("• [Upload Issues](#)")
        st.markdown("• [Scanning Help](#)")


def section_header(title: str):
    """Display a section header with visual separation."""
    st.markdown(f"### {title}")
    st.divider()


def render_sales_dashboard(df: pd.DataFrame):
    """
    Render a basic sales dashboard from DataFrame with sales data.
    Expects columns: datetime, quantity, revenue, product, category
    """
    if df.empty:
        st.info("No data to display")
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Revenue", f"${df['revenue'].sum():.2f}")
    with col2:
        st.metric("Total Items", int(df["quantity"].sum()))
    with col3:
        st.metric("Transactions", len(df))
    with col4:
        st.metric("Avg Order Value", f"${df['revenue'].sum() / max(len(df), 1):.2f}")

    # Revenue over time
    st.subheader("Revenue Trend")
    daily_revenue = df.groupby(df["datetime"].dt.date)["revenue"].sum().reset_index()
    if not daily_revenue.empty:
        fig = px.line(daily_revenue, x="datetime", y="revenue", markers=True)
        st.plotly_chart(fig, use_container_width=True)

    # Top products
    st.subheader("Top Products")
    top_products = (
        df.groupby("product")["revenue"].sum().sort_values(ascending=False).head(10)
    )
    if not top_products.empty:
        fig = px.bar(
            x=top_products.index,
            y=top_products.values,
            labels={"x": "Product", "y": "Revenue"},
        )
        st.plotly_chart(fig, use_container_width=True)
