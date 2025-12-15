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
        # Set flag to prevent session restoration
        st.session_state["_just_logged_out"] = True
        
        # Clear session state
        keys_to_clear = [
            "auth_user", "is_authenticated", "current_shop",
            "_persistent_user_id", "_persistent_user_email", 
            "_persistent_user_name", "_persistent_user_role",
            "_db_initialized", "current_page"
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        # Clear cookies and persistent storage
        try:
            from Retailsights.utils.session_manager import SessionManager
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
        
        if st.button("Open Support Center", width="stretch"):
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
        st.plotly_chart(fig, width="stretch")

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
        st.plotly_chart(fig, width="stretch")
