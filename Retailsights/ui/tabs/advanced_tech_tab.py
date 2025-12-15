"""
Advanced Tech Integration Tab
Blockchain, IoT Sensors, and Computer Vision monitoring.
"""
from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from ...services.blockchain_service import BlockchainService
from ...services.iot_sensor_service import IoTSensorService
from ...services.computer_vision_service import ComputerVisionService
from ..components import section_header


def render_advanced_tech_tab(state):
    """Advanced technology integrations dashboard."""
    st.title("🚀 Advanced Technology Hub")
    
    user = state.get("auth_user") or state.get("user")
    if not user:
        st.error("Please log in")
        return
    
    # Store user in state for child components
    state["user"] = user
    
    tabs = st.tabs([
        "🔗 Blockchain Traceability",
        "📡 IoT Sensors",
        "👁️ Computer Vision"
    ])
    
    with tabs[0]:
        render_blockchain_tab(state)
    
    with tabs[1]:
        render_iot_sensors_tab(state)
    
    with tabs[2]:
        render_computer_vision_tab(state)


def render_blockchain_tab(state):
    """Blockchain traceability interface."""
    section_header("Blockchain Product Traceability")
    
    shop = state.get("current_shop") or state.get("active_shop")
    if not shop:
        st.info("Please select a store")
        return
    
    st.markdown("""
    ### 🔗 Immutable Supply Chain Tracking
    Every product event is recorded on the blockchain for:
    - ✅ Tamper-proof audit trail
    - 🔍 Complete product history
    - 📋 Regulatory compliance
    - 🛡️ Instant batch recalls
    """)
    
    # Verify blockchain integrity
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🔐 Blockchain Verification")
        if st.button("🔍 Verify Blockchain Integrity"):
            with st.spinner("Verifying blockchain..."):
                result = BlockchainService.verify_blockchain_integrity(shop['id'])
            
            if result.get('valid'):
                st.success(f"✅ {result.get('message', 'Blockchain verified')}")
                st.metric("Total Blocks", result.get('total_blocks', 0))
            else:
                st.error(f"⚠️ {result.get('message', 'Blockchain verification failed')}")
                if result.get('tampered_blocks'):
                    st.warning("Tampered blocks detected:")
                    st.json(result['tampered_blocks'])
    
    with col2:
        st.subheader("📊 Blockchain Stats")
        st.metric("Blockchain Status", "🟢 Active")
        st.metric("Consensus", "Proof of Authority")
    
    st.markdown("---")
    
    # Product history lookup
    st.subheader("🔍 Product History Lookup")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        product_id = st.number_input("Product ID", min_value=1, value=1)
    with col2:
        if st.button("📜 View History"):
            history = BlockchainService.get_product_history(product_id)
            
            if history:
                st.success(f"Found {len(history)} blockchain events")
                
                # Display timeline
                for event in history:
                    with st.expander(f"Block #{event['block_index']} - {event['event_type']} - {event['timestamp']}"):
                        st.write(f"**Hash:** `{event['block_hash']}`")
                        st.write(f"**Verified:** {'✅' if event['verified'] else '❌'}")
                        if event.get('data'):
                            st.json(event['data'])
            else:
                st.info("No blockchain history for this product")
    
    # Batch recall simulation
    st.markdown("---")
    st.subheader("🚨 Batch Recall System")
    
    with st.expander("⚠️ Initiate Product Recall"):
        batch_id = st.text_input("Batch ID", placeholder="BATCH-2025-001")
        recall_reason = st.text_area("Recall Reason", placeholder="Quality control issue detected")
        
        if st.button("🚨 INITIATE RECALL", type="primary"):
            if batch_id and recall_reason:
                result = BlockchainService.track_batch_recall(batch_id, recall_reason, shop['id'])
                
                if result.get('success'):
                    st.success(f"✅ Recall initiated for {result['products_recalled']} products")
                    st.info(f"SKUs recalled: {', '.join(result['product_skus'][:5])}")
                    st.warning("⚠️ All affected products marked as RECALLED on blockchain")
                else:
                    st.error(result.get('message', 'Recall failed'))
            else:
                st.warning("Please fill in all fields")


def render_iot_sensors_tab(state):
    """IoT sensor monitoring interface."""
    section_header("IoT Sensor Monitoring")
    
    shop = state.get("current_shop") or state.get("active_shop")
    if not shop:
        st.info("Please select a store")
        return
    
    shop_id = shop["id"]
    
    # Simulate sensor data for demo
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🎲 Generate Demo Data"):
            result = IoTSensorService.simulate_sensor_data(shop_id, sensor_count=5)
            st.success(f"✅ {result['sensors_created']} sensors activated")
    
    # Get sensor dashboard
    dashboard = IoTSensorService.get_sensor_dashboard(shop_id)
    
    if not dashboard:
        st.info("No sensor data available. Click 'Generate Demo Data' to simulate.")
        return
    
    # Summary metrics
    summary = dashboard.get('summary', {})
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Total Sensors", summary.get('total_sensors', 0))
    col2.metric("🟢 Online", summary.get('online_sensors', 0))
    col3.metric("🔴 Offline", summary.get('offline_sensors', 0))
    col4.metric("⚠️ Alerts", summary.get('active_alerts', 0), 
               delta=None, delta_color="inverse")
    
    st.markdown("---")
    
    # Active alerts
    alerts = dashboard.get('alerts', [])
    if alerts:
        st.subheader("🚨 Active Alerts")
        for alert in alerts[:5]:
            severity_emoji = {
                'CRITICAL': '🔴',
                'HIGH': '🟠',
                'MEDIUM': '🟡',
                'LOW': '🟢'
            }.get(alert['severity'], '⚪')
            
            with st.expander(f"{severity_emoji} {alert['severity']} - {alert['alert_type']} - {alert['message']}"):
                st.write(f"**Sensor:** {alert['sensor_id']}")
                st.write(f"**Triggered:** {alert['triggered_at']}")
    else:
        st.success("✅ No active alerts")
    
    st.markdown("---")
    
    # Sensor grid
    st.subheader("📊 Sensor Status Grid")
    sensors = dashboard.get('sensors', [])
    
    if sensors:
        df = pd.DataFrame(sensors)
        
        # Format for display
        display_df = df[[
            'sensor_id', 'location', 'zone_type', 'temperature', 
            'humidity', 'status', 'last_reading'
        ]].copy()
        
        # Color code temperatures
        st.dataframe(
            display_df.style.applymap(
                lambda x: 'background-color: #ffcccc' if isinstance(x, (int, float)) and x > 10 else '',
                subset=['temperature']
            ),
            width="stretch"
        )
        
        # Temperature chart
        st.subheader("🌡️ Temperature Monitoring")
        
        sensor_id = st.selectbox("Select Sensor", df['sensor_id'].tolist())
        hours = st.slider("History (hours)", 1, 24, 6)
        
        history = IoTSensorService.get_temperature_history(sensor_id, hours)
        
        if history:
            df_history = pd.DataFrame(history)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_history['timestamp'],
                y=df_history['temperature'],
                mode='lines+markers',
                name='Temperature',
                line=dict(color='#ff6b6b', width=2)
            ))
            
            # Add threshold lines
            fig.add_hline(y=5, line_dash="dash", line_color="green", 
                         annotation_text="Max Safe Temp")
            fig.add_hline(y=0, line_dash="dash", line_color="blue",
                         annotation_text="Min Safe Temp")
            
            fig.update_layout(
                title=f"Temperature History - {sensor_id}",
                xaxis_title="Time",
                yaxis_title="Temperature (°C)",
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, width="stretch")
    
    # Spoilage risk prediction
    st.markdown("---")
    st.subheader("⚠️ Spoilage Risk Prediction")
    
    risks = IoTSensorService.predict_spoilage_risk(shop_id)
    
    if risks:
        for risk in risks:
            risk_emoji = "🔴" if risk['risk_level'] == "HIGH" else "🟡"
            with st.expander(f"{risk_emoji} {risk['location']} - {risk['affected_products']} products at risk"):
                st.write(f"**Violations:** {risk['violation_count']} in 24h")
                st.write(f"**Avg Temperature:** {risk['avg_temperature']:.1f}°C")
                st.write(f"**Recommendation:** {risk['recommendation']}")
                
                if risk.get('products'):
                    st.write("**Affected Products:**")
                    for prod in risk['products'][:3]:
                        st.write(f"- {prod['name']} (expires in {prod['days_left']} days)")
    else:
        st.success("✅ No spoilage risks detected")


def render_computer_vision_tab(state):
    """Computer vision interface."""
    section_header("Computer Vision Quality Control")
    
    shop = state.get("current_shop") or state.get("active_shop")
    if not shop:
        st.info("Please select a store")
        return
    
    st.markdown("""
    ### 👁️ AI-Powered Visual Inspection
    Automated quality control using computer vision:
    - 🍎 Freshness detection
    - 📦 Packaging damage detection
    - 📊 Shelf compliance monitoring
    - 🔢 Automated stock counting
    """)
    
    tabs = st.tabs(["📸 Quality Inspection", "📊 Shelf Monitoring", "🔢 Stock Counting"])
    
    with tabs[0]:
        st.subheader("🍎 Product Quality Inspection")
        
        uploaded_file = st.file_uploader("Upload product image", type=['jpg', 'jpeg', 'png'])
        
        if uploaded_file:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.image(uploaded_file, caption="Uploaded Image", width="stretch")
            
            with col2:
                if st.button("🔍 Analyze Quality"):
                    image_data = uploaded_file.read()
                    
                    with st.spinner("Running AI analysis..."):
                        freshness = ComputerVisionService.detect_product_freshness(
                            image_data, 
                            "produce"
                        )
                        
                        packaging = ComputerVisionService.detect_damaged_packaging(image_data)
                    
                    # Display results
                    if freshness.get('success'):
                        score = freshness['freshness_score']
                        grade = freshness['quality_grade']
                        
                        st.metric("Freshness Score", f"{score:.0f}/100")
                        
                        if grade == "EXCELLENT":
                            st.success(f"✅ {grade}")
                        elif grade == "GOOD":
                            st.info(f"👍 {grade}")
                        elif grade == "FAIR":
                            st.warning(f"⚠️ {grade}")
                        else:
                            st.error(f"❌ {grade}")
                        
                        st.write(f"**Recommendation:** {freshness['recommendation']}")
                    
                    if packaging.get('success'):
                        st.markdown("---")
                        if packaging['is_damaged']:
                            st.error(f"⚠️ Packaging Damage Detected ({packaging['damage_score']:.0f}/100)")
                        else:
                            st.success("✅ Packaging Intact")
    
    with tabs[1]:
        st.subheader("📊 Shelf Compliance Monitoring")
        
        shelf_image = st.file_uploader("Upload shelf image", type=['jpg', 'jpeg', 'png'], key="shelf")
        
        if shelf_image:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.image(shelf_image, caption="Shelf Image", width="stretch")
            
            with col2:
                if st.button("📊 Analyze Shelf"):
                    image_data = shelf_image.read()
                    
                    with st.spinner("Analyzing shelf..."):
                        result = ComputerVisionService.detect_shelf_compliance(
                            image_data,
                            {"expected_products": 20}
                        )
                    
                    if result.get('success'):
                        st.metric("Compliance Score", f"{result['compliance_score']:.0f}/100")
                        st.metric("Shelf Fullness", f"{result['shelf_fullness']:.0f}%")
                        st.metric("Products Detected", result['estimated_products'])
                        
                        if result['issues']:
                            st.warning("⚠️ Issues Detected:")
                            for issue in result['issues']:
                                st.write(f"- {issue['message']}")
                        
                        st.info(result['recommendation'])
    
    with tabs[2]:
        st.subheader("🔢 Automated Stock Counting")
        
        stock_image = st.file_uploader("Upload product shelf", type=['jpg', 'jpeg', 'png'], key="stock")
        category = st.selectbox("Product Category", ["Dairy", "Meat", "Produce", "Bakery", "Frozen"])
        
        if stock_image:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.image(stock_image, caption="Product Image", width="stretch")
            
            with col2:
                if st.button("🔢 Count Products"):
                    image_data = stock_image.read()
                    
                    with st.spinner("Counting products..."):
                        result = ComputerVisionService.count_products_on_shelf(
                            image_data,
                            category
                        )
                    
                    if result.get('success'):
                        count = result['product_count']
                        st.success(f"🔢 Detected: {count} products")
                        st.metric("Confidence", f"{result['confidence']:.0f}%")
                        st.info(f"Category: {result['category']}")
                        st.caption(result.get('note', ''))
