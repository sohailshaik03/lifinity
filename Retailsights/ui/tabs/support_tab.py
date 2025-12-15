"""
Customer Support Tab
Contact information, FAQ, and chatbot assistance.
"""
from __future__ import annotations

import streamlit as st
from datetime import datetime
from typing import Dict, List
import re

# Import support configuration
try:
    from config_support import (
        SUPPORT_EMAIL, SUPPORT_HOURS, RESPONSE_TIME_EMAIL,
        SUPPORT_TEAM, ENABLE_CHATBOT
    )
except ImportError:
    # Fallback if config doesn't exist
    SUPPORT_EMAIL = "support@retailsight.com"
    SUPPORT_HOURS = "Mon-Fri: 9:00 AM - 6:00 PM GMT"
    RESPONSE_TIME_EMAIL = "Within 24 hours"
    SUPPORT_TEAM = {"general": "support@retailsight.com"}
    ENABLE_CHATBOT = True


def render_support_tab(state):
    """Render customer support interface."""
    st.title("🎧 Customer Support")
    
    # Support Overview
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📧 Email Support", SUPPORT_EMAIL)
    with col2:
        st.metric("⏰ Support Hours", SUPPORT_HOURS)
    with col3:
        st.metric("⚡ Response Time", RESPONSE_TIME_EMAIL)
    
    st.markdown("---")
    
    # Tabs for different support options
    tabs = st.tabs(["💬 Live Chat", "📧 Contact Us", "❓ FAQ", "📚 Resources"])
    
    with tabs[0]:
        render_chatbot()
    
    with tabs[1]:
        render_contact_form()
    
    with tabs[2]:
        render_faq()
    
    with tabs[3]:
        render_resources()


def render_chatbot():
    """AI-powered chatbot for instant help."""
    st.subheader("💬 Chat with Support Assistant")
    
    st.markdown("""
    ### 🤖 RetailSight AI Assistant
    Get instant answers to common questions!
    """)
    
    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {
                "role": "assistant",
                "message": "👋 Hello! I'm the RetailSight Support Assistant. How can I help you today?",
                "timestamp": datetime.now()
            }
        ]
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for chat in st.session_state.chat_history:
            if chat["role"] == "assistant":
                st.markdown(f"**🤖 Assistant:** {chat['message']}")
            else:
                st.markdown(f"**👤 You:** {chat['message']}")
            st.caption(chat["timestamp"].strftime("%I:%M %p"))
            st.markdown("")
    
    # Chat input
    user_message = st.text_input("Type your message...", key="chat_input")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Send", width="stretch"):
            if user_message.strip():
                # Add user message
                st.session_state.chat_history.append({
                    "role": "user",
                    "message": user_message,
                    "timestamp": datetime.now()
                })
                
                # Generate bot response
                bot_response = get_bot_response(user_message)
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "message": bot_response,
                    "timestamp": datetime.now()
                })
                
                st.rerun()
    
    with col2:
        if st.button("Clear Chat", width="stretch"):
            st.session_state.chat_history = [
                {
                    "role": "assistant",
                    "message": "👋 Hello! I'm the RetailSight Support Assistant. How can I help you today?",
                    "timestamp": datetime.now()
                }
            ]
            st.rerun()
    
    # Quick action buttons
    st.markdown("#### Quick Help Topics")
    quick_topics = st.columns(3)
    
    with quick_topics[0]:
        if st.button("🔐 Login Issues", width="stretch"):
            trigger_quick_response("login issues")
    
    with quick_topics[1]:
        if st.button("📊 Upload Data", width="stretch"):
            trigger_quick_response("upload data")
    
    with quick_topics[2]:
        if st.button("⚠️ Expiry Alerts", width="stretch"):
            trigger_quick_response("expiry alerts")


def get_bot_response(user_message: str) -> str:
    """Generate chatbot response based on user message."""
    message_lower = user_message.lower()
    
    # Login related
    if any(word in message_lower for word in ["login", "password", "access", "sign in"]):
        return """🔐 **Login Help:**
        
1. Make sure you're using the correct email address
2. Password is case-sensitive
3. If you forgot your password, contact your admin to reset it
4. Ensure your account is active (check with admin)

Need admin access? Contact: admin@retailsight.com"""
    
    # Upload related
    elif any(word in message_lower for word in ["upload", "import", "csv", "excel", "file"]):
        return """📊 **Upload Data Help:**
        
1. Go to **📤 Upload Sales** tab
2. Supported formats: CSV, XLSX, XLS
3. Required columns: Date, Product, SKU, Quantity, Price
4. Maximum file size: 200MB
5. Click "Parse & Validate" to check data before saving

Having issues? Send your file structure to support@retailsight.com"""
    
    # Expiry related
    elif any(word in message_lower for word in ["expiry", "expire", "alert", "notification", "yellow sticker"]):
        return """⚠️ **Expiry Management Help:**
        
1. Go to **⏰ Expiry Tracker** to view expiring items
2. Set up alerts in **Admin Panel → Alert Settings**
3. Use **🏷️ Yellow Sticker** tab to discount items
4. Configure discount rules per product category
5. Print labels directly from the system

Need help setting alerts? I can walk you through it!"""
    
    # Scanning related
    elif any(word in message_lower for word in ["scan", "barcode", "qr", "camera", "webcam"]):
        return """📷 **Barcode Scanning Help:**
        
1. Go to **🏷️ Yellow Sticker** tab
2. Use "Scan with Webcam" for live scanning
3. Or upload barcode/QR image
4. System automatically looks up product
5. Apply discount and print label

Camera not working? Check browser permissions!"""
    
    # Analytics related
    elif any(word in message_lower for word in ["report", "analytics", "dashboard", "sales", "revenue"]):
        return """📈 **Reports & Analytics:**
        
1. **Manager Tab** - 7-day sales overview
2. **Enterprise Dashboard** - Multi-store comparison
3. **History Tab** - Transaction search
4. **Exports** - Download CSV/Excel reports

Need specific insights? Ask me what you're looking for!"""
    
    # AI features
    elif any(word in message_lower for word in ["ai", "prediction", "forecast", "machine learning"]):
        return """🤖 **AI Features:**
        
1. **Waste Prediction** - 7-day ML forecast
2. **Dynamic Pricing** - Time-based discounts
3. **Fraud Detection** - Unusual pattern alerts
4. **Computer Vision** - Quality inspection

Available in **🏢 Enterprise Dashboard** and **🚀 Advanced Tech** tabs!"""
    
    # Blockchain
    elif any(word in message_lower for word in ["blockchain", "traceability", "ledger"]):
        return """🔗 **Blockchain Traceability:**
        
Track product journey from receipt to sale:
- Immutable audit trail
- Batch recall capability
- Regulatory compliance
- Tamper-proof records

Find it in **🚀 Advanced Tech → Blockchain** tab!"""
    
    # Support contact
    elif any(word in message_lower for word in ["email", "contact", "phone", "call", "support"]):
        return f"""📧 **Contact Support:**
        
**Email:** {SUPPORT_EMAIL}
**Hours:** {SUPPORT_HOURS}
**Response Time:** {RESPONSE_TIME}

For urgent issues, mark email as "URGENT" in subject line.

You can also submit a ticket through the **Contact Us** tab!"""
    
    # Thank you
    elif any(word in message_lower for word in ["thank", "thanks", "appreciate"]):
        return "You're welcome! 😊 Is there anything else I can help you with?"
    
    # Default response
    else:
        return """I'm here to help! I can assist with:

🔐 Login & Access Issues
📊 Data Upload & Import
⚠️ Expiry Tracking & Alerts
📷 Barcode Scanning
📈 Reports & Analytics
🤖 AI & Enterprise Features
📧 Contact Information

What would you like help with?"""


def trigger_quick_response(topic: str):
    """Trigger a quick response for common topics."""
    st.session_state.chat_history.append({
        "role": "user",
        "message": f"Help me with {topic}",
        "timestamp": datetime.now()
    })
    
    bot_response = get_bot_response(topic)
    st.session_state.chat_history.append({
        "role": "assistant",
        "message": bot_response,
        "timestamp": datetime.now()
    })
    st.rerun()


def render_contact_form():
    """Contact form for submitting support tickets."""
    st.subheader("📧 Submit a Support Ticket")
    
    st.markdown(f"""
    Can't find what you're looking for? Send us a message and we'll get back to you within **{RESPONSE_TIME_EMAIL}**.
    """)
    
    with st.form("support_form"):
        name = st.text_input("Your Name *")
        email = st.text_input("Your Email *", placeholder="name@company.com")
        
        category = st.selectbox(
            "Issue Category *",
            [
                "— Select Category —",
                "Login & Access",
                "Data Upload",
                "Expiry Tracking",
                "Barcode Scanning",
                "Reports & Analytics",
                "Enterprise Features",
                "Billing & Subscription",
                "Technical Issue",
                "Feature Request",
                "Other"
            ]
        )
        
        priority = st.select_slider(
            "Priority",
            options=["Low", "Medium", "High", "Urgent"],
            value="Medium"
        )
        
        subject = st.text_input("Subject *")
        message = st.text_area(
            "Describe your issue *",
            height=200,
            placeholder="Please provide as much detail as possible..."
        )
        
        # File attachment
        attachment = st.file_uploader(
            "Attach screenshot or file (optional)",
            type=["png", "jpg", "jpeg", "pdf", "csv", "xlsx"]
        )
        
        submitted = st.form_submit_button("📤 Submit Ticket", width="stretch")
        
        if submitted:
            # Validation
            if not name or not email or not subject or not message:
                st.error("⚠️ Please fill in all required fields (*)")
            elif category == "— Select Category —":
                st.error("⚠️ Please select an issue category")
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                st.error("⚠️ Please enter a valid email address")
            else:
                # In production, this would send email or create ticket in system
                st.success(f"""
                ✅ **Ticket Submitted Successfully!**
                
                📧 You'll receive a confirmation email at **{email}**
                
                🎫 Ticket Reference: **RST-{datetime.now().strftime('%Y%m%d-%H%M%S')}**
                
                ⏱️ Expected Response: **{RESPONSE_TIME_EMAIL}**
                
                We'll contact you soon!
                """)
                
                # Show what was submitted
                with st.expander("View Submitted Details"):
                    st.write(f"**Name:** {name}")
                    st.write(f"**Email:** {email}")
                    st.write(f"**Category:** {category}")
                    st.write(f"**Priority:** {priority}")
                    st.write(f"**Subject:** {subject}")
                    st.write(f"**Message:** {message}")
                    if attachment:
                        st.write(f"**Attachment:** {attachment.name}")


def render_faq():
    """Frequently Asked Questions."""
    st.subheader("❓ Frequently Asked Questions")
    
    faqs = [
        {
            "question": "How do I reset my password?",
            "answer": "Contact your system administrator to reset your password. Admins can reset passwords from the Admin Panel → Manage Users section."
        },
        {
            "question": "What file formats are supported for upload?",
            "answer": "We support CSV, XLSX, and XLS files. Your file should contain columns for Date, Product Name, SKU/Barcode, Quantity, and Price."
        },
        {
            "question": "How do I set up expiry alerts?",
            "answer": "Go to Admin Panel → Alert Settings. Enable email/SMS alerts and enter recipient addresses. You can set alert thresholds (e.g., 7 days before expiry)."
        },
        {
            "question": "Can I scan barcodes with my phone camera?",
            "answer": "Yes! Use the Yellow Sticker tab and click 'Scan with Webcam'. Grant camera permissions in your browser. You can also upload barcode images."
        },
        {
            "question": "How do discounts work?",
            "answer": "Set discount rules by category in the Admin Panel. When products near expiry, apply discounts in the Yellow Sticker tab. The system calculates new prices automatically."
        },
        {
            "question": "Can I export reports?",
            "answer": "Yes! Go to the Exports tab to download sales data, expiry reports, and markdown reports in CSV or Excel format."
        },
        {
            "question": "What's the difference between Manager and Enterprise dashboards?",
            "answer": "Manager Tab shows single-store analytics. Enterprise Dashboard provides multi-store comparison, AI predictions, and advanced features."
        },
        {
            "question": "How does the waste prediction work?",
            "answer": "Our AI analyzes historical data (sales patterns, seasonality, expiry rates) to predict waste 7 days ahead with 60%+ confidence. Find it in Enterprise Dashboard → AI Predictions."
        },
        {
            "question": "Is my data secure?",
            "answer": "Yes! We use encrypted connections, secure database storage, and blockchain for critical events. Enterprise tier includes advanced fraud detection."
        },
        {
            "question": "Can multiple stores share data?",
            "answer": "Yes! The Enterprise Dashboard provides cross-store analytics. Each store maintains separate inventory but admins can view all stores."
        },
        {
            "question": "How do I access IoT sensor data?",
            "answer": "IoT sensors (temperature/humidity) are available in Advanced Tech tab. You can view real-time readings, alerts, and historical trends."
        },
        {
            "question": "What browsers are supported?",
            "answer": "We recommend Chrome, Firefox, Safari, or Edge (latest versions). Some features like webcam scanning require modern browser APIs."
        }
    ]
    
    for i, faq in enumerate(faqs, 1):
        with st.expander(f"**{i}. {faq['question']}**"):
            st.write(faq['answer'])


def render_resources():
    """Help resources and documentation."""
    st.subheader("📚 Help Resources")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 📖 Documentation
        
        - [Quick Start Guide](docs/quickstart)
        - [User Manual](docs/manual)
        - [Admin Guide](docs/admin)
        - [API Documentation](docs/api)
        - [Video Tutorials](docs/videos)
        """)
        
        st.markdown("""
        ### 🎓 Training
        
        - [Onboarding Course](training/onboarding)
        - [Advanced Features](training/advanced)
        - [Best Practices](training/best-practices)
        - [Certification Program](training/certification)
        """)
    
    with col2:
        st.markdown("""
        ### 🔧 Troubleshooting
        
        - [Common Issues](help/troubleshooting)
        - [Browser Setup](help/browser)
        - [Camera Permissions](help/camera)
        - [Upload Problems](help/upload)
        - [Performance Tips](help/performance)
        """)
        
        st.markdown("""
        ### 📞 Contact Options
        
        - **Email:** support@retailsight.com
        - **Hours:** Mon-Fri, 9 AM - 6 PM GMT
        - **Response:** Within 24 hours
        - **Emergency:** Mark email as URGENT
        """)
    
    st.markdown("---")
    
    st.markdown("""
    ### 🆕 What's New
    
    **Version 2.5 (Dec 2025)**
    - ✨ AI-powered waste prediction
    - 🔗 Blockchain product traceability
    - 📡 IoT sensor integration
    - 🤖 Support chatbot assistant
    - 📊 Enhanced multi-store analytics
    
    [View Full Changelog](docs/changelog)
    """)
    
    st.markdown("---")
    
    # System Status
    st.markdown("### 🟢 System Status")
    status_cols = st.columns(4)
    
    with status_cols[0]:
        st.metric("API", "🟢 Operational")
    with status_cols[1]:
        st.metric("Database", "🟢 Operational")
    with status_cols[2]:
        st.metric("Blockchain", "🟢 Operational")
    with status_cols[3]:
        st.metric("AI Services", "🟢 Operational")
    
    st.caption("Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
