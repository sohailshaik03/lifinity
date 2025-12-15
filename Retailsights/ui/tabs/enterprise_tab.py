"""
Enterprise Dashboard Tab
Multi-store analytics, predictions, and executive-level insights.
"""
from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from ...services.waste_prediction_service import WastePredictionService
from ...services.multi_store_analytics import MultiStoreAnalytics
from ...services.dynamic_pricing_service import DynamicPricingService
from ..components import section_header


def render_enterprise_dashboard(state):
    """Main enterprise-level dashboard."""
    st.title("🏢 Enterprise Command Center")
    
    user = state.get("auth_user") or state.get("user")
    if not user:
        st.error("Please log in")
        return
    
    # All logged-in users can access (removed admin restriction)
    # Store user in state for child components
    state["user"] = user
    
    tabs = st.tabs([
        "🌐 Multi-Store Overview",
        "🤖 AI Predictions",
        "💰 Dynamic Pricing",
        "👥 Staff Performance",
        "⚠️ Anomaly Detection"
    ])
    
    with tabs[0]:
        render_multi_store_overview()
    
    with tabs[1]:
        render_ai_predictions(state)
    
    with tabs[2]:
        render_dynamic_pricing_tab(state)
    
    with tabs[3]:
        render_staff_performance(state)
    
    with tabs[4]:
        render_anomaly_detection(state)


def render_multi_store_overview():
    """Multi-store comparison dashboard."""
    section_header("All Stores Performance")
    
    with st.spinner("Loading store data..."):
        stores = MultiStoreAnalytics.get_all_stores_overview()
    
    if not stores:
        st.info("No stores found")
        return
    
    # Top KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    total_revenue = sum(s.get('revenue_last_7_days', 0) for s in stores)
    total_waste = sum(s.get('waste_cost_last_30_days', 0) for s in stores)
    avg_efficiency = sum(s.get('efficiency_score', 0) for s in stores) / len(stores) if stores else 0
    total_markdown = sum(s.get('markdown_revenue_7d', 0) for s in stores)
    
    col1.metric("Total Revenue (7d)", f"£{total_revenue:,.0f}")
    col2.metric("Total Waste (30d)", f"£{total_waste:,.0f}")
    col3.metric("Avg Efficiency Score", f"{avg_efficiency:.1f}/100")
    col4.metric("Markdown Revenue (7d)", f"£{total_markdown:,.0f}")
    
    st.markdown("---")
    
    # Store comparison table
    st.subheader("📊 Store Comparison")
    df = pd.DataFrame(stores)
    
    # Format for display
    display_df = df[[
        'store_name', 'location', 'revenue_last_7_days', 
        'waste_cost_last_30_days', 'waste_as_pct_revenue', 
        'efficiency_score', 'total_products', 'staff_count'
    ]].copy()
    
    display_df.columns = [
        'Store', 'Location', 'Revenue (7d)', 
        'Waste Cost (30d)', 'Waste %', 
        'Efficiency', 'Products', 'Staff'
    ]
    
    # Style the dataframe
    st.dataframe(
        display_df.style.background_gradient(subset=['Efficiency'], cmap='RdYlGn')
                       .format({
                           'Revenue (7d)': '£{:,.0f}',
                           'Waste Cost (30d)': '£{:,.0f}',
                           'Waste %': '{:.1f}%',
                           'Efficiency': '{:.1f}'
                       }),
        width="stretch"
    )
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Revenue by Store")
        fig_revenue = px.bar(
            df.sort_values('revenue_last_7_days', ascending=False),
            x='store_name',
            y='revenue_last_7_days',
            color='efficiency_score',
            color_continuous_scale='RdYlGn',
            labels={'revenue_last_7_days': 'Revenue (£)', 'store_name': 'Store'}
        )
        st.plotly_chart(fig_revenue, width="stretch")
    
    with col2:
        st.subheader("Waste by Store")
        fig_waste = px.bar(
            df.sort_values('waste_cost_last_30_days', ascending=False),
            x='store_name',
            y='waste_cost_last_30_days',
            color='waste_as_pct_revenue',
            color_continuous_scale='Reds',
            labels={'waste_cost_last_30_days': 'Waste Cost (£)', 'store_name': 'Store'}
        )
        st.plotly_chart(fig_waste, width="stretch")
    
    # Regional performance
    st.markdown("---")
    st.subheader("🗺️ Regional Performance")
    regional = MultiStoreAnalytics.get_regional_performance(days=30)
    
    if regional:
        df_regional = pd.DataFrame(regional)
        st.dataframe(
            df_regional.style.format({
                'total_revenue': '£{:,.0f}',
                'avg_revenue_per_store': '£{:,.0f}',
                'total_waste_cost': '£{:,.0f}',
                'avg_waste_per_store': '£{:,.0f}'
            }),
            width="stretch"
        )


def render_ai_predictions(state):
    """AI-powered predictions and recommendations."""
    section_header("AI-Powered Waste Prediction")
    
    shop = state.get("current_shop") or state.get("active_shop")
    if not shop:
        st.info("Please select a store")
        return
    
    shop_id = shop["id"]
    
    # Waste prediction
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📈 7-Day Waste Forecast")
        with st.spinner("Running ML prediction model..."):
            prediction = WastePredictionService.predict_waste_next_week(shop_id)
        
        if prediction.get('prediction_available'):
            # Display prediction
            pred_col1, pred_col2, pred_col3 = st.columns(3)
            pred_col1.metric(
                "Predicted Waste (7 days)",
                f"{prediction['predicted_waste_units']:.0f} units"
            )
            pred_col2.metric(
                "Estimated Cost",
                f"£{prediction['predicted_waste_cost']:.2f}"
            )
            pred_col3.metric(
                "Confidence",
                f"{prediction['confidence']:.0f}%",
                help=f"Model: {prediction.get('method', 'N/A')}"
            )
            
            # Daily predictions chart
            if 'daily_predictions' in prediction:
                daily_df = pd.DataFrame({
                    'Day': [f"Day {i+1}" for i in range(len(prediction['daily_predictions']))],
                    'Predicted Waste': prediction['daily_predictions']
                })
                fig = px.line(
                    daily_df,
                    x='Day',
                    y='Predicted Waste',
                    markers=True,
                    title="Daily Waste Forecast"
                )
                st.plotly_chart(fig, width="stretch")
            
            # Feature importance (if ML model)
            if 'feature_importance' in prediction:
                st.subheader("🔍 Model Insights")
                importance_df = pd.DataFrame([
                    {"Feature": k, "Importance": v} 
                    for k, v in prediction['feature_importance'].items()
                ]).sort_values('Importance', ascending=False)
                
                fig_importance = px.bar(
                    importance_df,
                    x='Importance',
                    y='Feature',
                    orientation='h',
                    title="Factors Affecting Waste Prediction"
                )
                st.plotly_chart(fig_importance, width="stretch")
        else:
            st.warning(prediction.get('message', 'Prediction not available'))
    
    with col2:
        st.subheader("⚠️ High-Risk Products")
        high_risk = WastePredictionService.get_high_risk_products(shop_id, threshold=0.3)
        
        if high_risk:
            for product in high_risk[:5]:
                waste_rate = product.get('waste_rate', 0) * 100
                with st.expander(f"🔴 {product['name']} ({waste_rate:.0f}% waste)"):
                    st.write(f"**SKU:** {product['sku']}")
                    st.write(f"**Category:** {product['category']}")
                    st.write(f"**Total Wasted:** {product['total_wasted_units']} units")
                    st.write(f"**Cost:** £{product['total_waste_cost']:.2f}")
                    st.error(f"⚠️ {waste_rate:.1f}% of this product goes to waste")
        else:
            st.success("✅ No high-risk products found")
    
    # Recommendations
    st.markdown("---")
    st.subheader("💡 AI Recommendations")
    recommendations = WastePredictionService.get_prevention_recommendations(shop_id)
    
    if recommendations:
        for rec in recommendations:
            priority_color = "🔴" if rec['priority'] == 'HIGH' else "🟡"
            with st.expander(f"{priority_color} {rec['product_name']} - {rec['issue']}"):
                st.write(f"**SKU:** {rec['product_sku']}")
                st.write(f"**Priority:** {rec['priority']}")
                st.write("**Recommended Actions:**")
                for action in rec['recommendations']:
                    st.write(f"- {action}")
    else:
        st.success("✅ No critical recommendations at this time")
    
    # Category analysis
    st.markdown("---")
    st.subheader("📦 Waste by Category")
    category_waste = WastePredictionService.get_waste_by_category(shop_id, days=30)
    
    if category_waste:
        df_cat = pd.DataFrame(category_waste)
        fig_cat = px.pie(
            df_cat,
            values='total_waste_cost',
            names='category',
            title="Waste Cost Distribution by Category (30 days)"
        )
        st.plotly_chart(fig_cat, width="stretch")


def render_dynamic_pricing_tab(state):
    """Dynamic pricing engine interface."""
    section_header("Dynamic Pricing Engine")
    
    shop = state.get("current_shop") or state.get("active_shop")
    if not shop:
        st.info("Please select a store")
        return
    
    shop_id = shop["id"]
    
    # Time-based pricing
    st.subheader("⏰ Time-Based Pricing Multipliers")
    current_time = datetime.now()
    multiplier = DynamicPricingService.get_time_based_multiplier(current_time)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Current Time", current_time.strftime("%H:%M"))
    col2.metric("Active Multiplier", f"{multiplier}x")
    col3.metric("Additional Discount", f"+{(multiplier - 1) * 100:.0f}%")
    
    st.info("💡 Deeper discounts automatically apply during evening hours (6pm-midnight) to maximize clearance")
    
    # Time schedule
    with st.expander("View Full Time-Based Schedule"):
        schedule_df = pd.DataFrame([
            {"Time Period": "6am - 11am (Morning)", "Multiplier": "1.0x", "Extra Discount": "0%"},
            {"Time Period": "11am - 3pm (Lunch)", "Multiplier": "1.0x", "Extra Discount": "0%"},
            {"Time Period": "3pm - 6pm (Afternoon)", "Multiplier": "1.15x", "Extra Discount": "+15%"},
            {"Time Period": "6pm - 9pm (Evening)", "Multiplier": "1.30x", "Extra Discount": "+30%"},
            {"Time Period": "9pm - Midnight (Night)", "Multiplier": "1.50x", "Extra Discount": "+50%"},
        ])
        st.table(schedule_df)
    
    # Discount simulator
    st.markdown("---")
    st.subheader("🧮 Discount Calculator")
    
    col1, col2, col3 = st.columns(3)
    base_discount = col1.slider("Base Discount %", 0, 50, 20)
    days_left = col2.slider("Days Until Expiry", 1, 14, 5)
    stock_qty = col3.slider("Current Stock", 1, 50, 10)
    
    # Calculate dynamic discount
    result = DynamicPricingService.calculate_dynamic_discount(
        product_id=1,  # Placeholder
        base_discount_percent=base_discount,
        days_left=days_left,
        current_stock=stock_qty,
        include_time_factor=True,
        include_velocity_factor=False  # Simplified
    )
    
    # Display result
    st.markdown("### Calculated Discount")
    result_col1, result_col2, result_col3 = st.columns(3)
    result_col1.metric("Base Discount", f"{base_discount}%")
    result_col2.metric("Additional Boost", f"+{result['total_boost']:.1f}%", 
                      help="From time-of-day, urgency, and stock factors")
    result_col3.metric("**Final Discount**", f"{result['final_discount_percent']:.1f}%")
    
    # Show factors
    if result['factors_applied']:
        st.markdown("**Factors Applied:**")
        for factor in result['factors_applied']:
            st.write(f"- ✅ **{factor['factor']}**: +{factor['additional_discount']:.1f}% - {factor['reason']}")
    
    # Bundle suggestions
    st.markdown("---")
    st.subheader("📦 Bundle Pricing Suggestions")
    bundles = DynamicPricingService.suggest_bundle_pricing(shop_id)
    
    if bundles:
        for bundle in bundles:
            with st.expander(f"💰 {bundle['bundle_name']} - Save £{bundle['savings']:.2f}"):
                st.write("**Products in Bundle:**")
                for prod in bundle['products']:
                    st.write(f"- {prod['name']} (expires in {prod['days_left']} days)")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Regular Price", f"£{bundle['total_regular_price']:.2f}")
                col2.metric("Bundle Price", f"£{bundle['bundle_price']:.2f}")
                col3.metric("Discount", f"{bundle['discount_percent']}%")
    else:
        st.info("No bundle opportunities available right now")


def render_staff_performance(state):
    """Staff performance tracking."""
    section_header("Staff Performance & Leaderboard")
    
    shop = state.get("current_shop") or state.get("active_shop")
    if not shop:
        st.info("Please select a store")
        return
    
    shop_id = shop["id"]
    days = st.slider("Analysis Period (days)", 7, 90, 30)
    
    staff_data = MultiStoreAnalytics.get_staff_performance(shop_id, days=days)
    
    if not staff_data:
        st.info("No staff performance data available")
        return
    
    df = pd.DataFrame(staff_data)
    
    # Top performers
    st.subheader("🏆 Top Performers")
    top_3 = df.nlargest(3, 'performance_score')
    
    cols = st.columns(3)
    medals = ["🥇", "🥈", "🥉"]
    
    for idx, (i, row) in enumerate(top_3.iterrows()):
        if idx < 3:
            with cols[idx]:
                st.markdown(f"### {medals[idx]} {row['username']}")
                st.metric("Performance Score", f"{row['performance_score']:.0f}/130")
                st.write(f"**Role:** {row['role']}")
                st.write(f"**Markdown Sales:** {row['markdown_sales_count']}")
                st.write(f"**Revenue:** £{row['markdown_revenue']:.2f}")
    
    # Full leaderboard
    st.markdown("---")
    st.subheader("📊 Full Leaderboard")
    
    display_df = df[[
        'username', 'role', 'performance_score', 
        'markdown_sales_count', 'markdown_revenue', 
        'total_markdown_units', 'waste_logged_count'
    ]].copy()
    
    display_df.columns = [
        'Staff', 'Role', 'Score', 
        'Markdown Sales', 'Revenue', 
        'Units Sold', 'Waste Logged'
    ]
    
    st.dataframe(
        display_df.style.background_gradient(subset=['Score'], cmap='RdYlGn')
                       .format({
                           'Revenue': '£{:,.2f}',
                           'Score': '{:.0f}'
                       }),
        width="stretch"
    )
    
    # Performance chart
    fig = px.bar(
        df.sort_values('performance_score', ascending=False),
        x='username',
        y='performance_score',
        color='performance_score',
        color_continuous_scale='RdYlGn',
        title=f"Staff Performance Scores ({days} days)",
        labels={'performance_score': 'Score', 'username': 'Staff Member'}
    )
    st.plotly_chart(fig, width="stretch")


def render_anomaly_detection(state):
    """Real-time anomaly detection."""
    section_header("Anomaly Detection & Alerts")
    
    shop = state.get("current_shop") or state.get("active_shop")
    if not shop:
        st.info("Please select a store")
        return
    
    shop_id = shop["id"]
    
    with st.spinner("Scanning for anomalies..."):
        anomalies = MultiStoreAnalytics.detect_anomalies(shop_id)
    
    if not anomalies:
        st.success("✅ No anomalies detected - all systems normal")
        return
    
    # Display anomalies by severity
    high_severity = [a for a in anomalies if a.get('severity') == 'HIGH']
    medium_severity = [a for a in anomalies if a.get('severity') == 'MEDIUM']
    
    if high_severity:
        st.error(f"🚨 {len(high_severity)} HIGH SEVERITY ALERTS")
        for anomaly in high_severity:
            with st.expander(f"🔴 {anomaly['type']}: {anomaly['message']}", expanded=True):
                st.write(f"**Severity:** {anomaly['severity']}")
                st.write(f"**Recommendation:** {anomaly['recommendation']}")
                if 'products' in anomaly:
                    st.write(f"**Affected Products:** {', '.join(anomaly['products'])}")
    
    if medium_severity:
        st.warning(f"⚠️ {len(medium_severity)} MEDIUM PRIORITY ALERTS")
        for anomaly in medium_severity:
            with st.expander(f"🟡 {anomaly['type']}: {anomaly['message']}"):
                st.write(f"**Severity:** {anomaly['severity']}")
                st.write(f"**Recommendation:** {anomaly['recommendation']}")
                if 'products' in anomaly:
                    st.write(f"**Affected Products:** {', '.join(anomaly['products'])}")
    
    # Auto-refresh option
    st.markdown("---")
    if st.button("🔄 Refresh Anomaly Scan"):
        st.rerun()
