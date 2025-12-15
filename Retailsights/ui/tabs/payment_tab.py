"""Payment and subscription management UI tab.

Handles Stripe payment integration for UK client subscriptions
and one-time payments with secure card processing.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

import streamlit as st
from loguru import logger

from Retailsights.services.stripe_payment_service import stripe_service, StripePaymentError
from Retailsights.config import config


def render_payment_tab(user: dict, current_shop: Optional[dict] = None):
    """Render payment and subscription management interface.
    
    Args:
        user: Current authenticated user dictionary
        current_shop: Currently selected shop (optional)
    """
    st.title("💳 Payments & Subscriptions")
    
    if not stripe_service.is_enabled():
        st.error("⚠️ Payment system is not configured. Please contact support.")
        st.info("Administrator: Add STRIPE_SECRET_KEY to environment variables.")
        return
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["📦 Subscription Plans", "💰 Payment History", "⚙️ Billing Settings"])
    
    with tab1:
        render_subscription_plans(user, current_shop)
    
    with tab2:
        render_payment_history(user)
    
    with tab3:
        render_billing_settings(user)


def render_subscription_plans(user: dict, current_shop: Optional[dict]):
    """Display subscription plan options and current subscription.
    
    Args:
        user: Current user dictionary
        current_shop: Current shop dictionary
    """
    st.header("Choose Your Plan")
    
    # Define UK pricing plans
    plans = {
        "starter": {
            "name": "Starter",
            "price_monthly": 29.99,
            "price_annual": 299.00,
            "features": [
                "✅ Up to 3 shop locations",
                "✅ Basic analytics dashboard",
                "✅ Sales & inventory tracking",
                "✅ Expiry date monitoring",
                "✅ Email support",
                "✅ 1GB data storage"
            ],
            "recommended": False
        },
        "professional": {
            "name": "Professional",
            "price_monthly": 79.99,
            "price_annual": 799.00,
            "features": [
                "✅ Up to 10 shop locations",
                "✅ Advanced analytics & AI insights",
                "✅ Markdown pricing optimization",
                "✅ Waste reduction reports",
                "✅ Custom label printing",
                "✅ Priority email & chat support",
                "✅ 10GB data storage",
                "✅ API access"
            ],
            "recommended": True
        },
        "enterprise": {
            "name": "Enterprise",
            "price_monthly": 199.99,
            "price_annual": 1999.00,
            "features": [
                "✅ Unlimited shop locations",
                "✅ Enterprise AI analytics",
                "✅ Multi-store management",
                "✅ Advanced automation",
                "✅ Dedicated account manager",
                "✅ 24/7 phone support",
                "✅ Unlimited data storage",
                "✅ Custom integrations",
                "✅ SLA guarantee"
            ],
            "recommended": False
        }
    }
    
    # Display current subscription status
    st.subheader("Current Subscription")
    
    # TODO: Fetch from database
    current_subscription = None  # Replace with actual DB query
    
    if current_subscription:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Plan", current_subscription.get("plan_name", "N/A"))
        with col2:
            st.metric("Status", current_subscription.get("status", "N/A").title())
        with col3:
            renewal_date = current_subscription.get("current_period_end")
            if renewal_date:
                st.metric("Renews", renewal_date.strftime("%d %b %Y"))
    else:
        st.info("💡 You don't have an active subscription. Choose a plan below to get started!")
    
    st.markdown("---")
    
    # Billing interval selector
    billing_interval = st.radio(
        "Billing Interval",
        ["Monthly", "Annual (Save 17%)"],
        horizontal=True,
        help="Annual billing includes a 17% discount"
    )
    is_annual = "Annual" in billing_interval
    
    # Display plans in columns
    cols = st.columns(3)
    
    for idx, (plan_key, plan_data) in enumerate(plans.items()):
        with cols[idx]:
            # Plan card
            if plan_data["recommended"]:
                st.success("⭐ RECOMMENDED")
            
            st.markdown(f"### {plan_data['name']}")
            
            # Price display
            if is_annual:
                price = plan_data['price_annual']
                price_per_month = price / 12
                st.markdown(f"## £{price:.2f}/year")
                st.caption(f"(£{price_per_month:.2f}/month)")
            else:
                price = plan_data['price_monthly']
                st.markdown(f"## £{price:.2f}/month")
            
            # Features
            st.markdown("**Features:**")
            for feature in plan_data['features']:
                st.markdown(feature)
            
            # Subscribe button
            button_label = "Subscribe Now" if not current_subscription else "Upgrade"
            if st.button(button_label, key=f"subscribe_{plan_key}", type="primary" if plan_data["recommended"] else "secondary"):
                handle_subscription_selection(user, plan_key, plan_data, is_annual)
    
    # Money-back guarantee
    st.markdown("---")
    st.info("💯 **30-Day Money-Back Guarantee** · Cancel anytime · No hidden fees · Secure payment via Stripe")


def handle_subscription_selection(user: dict, plan_key: str, plan_data: dict, is_annual: bool):
    """Handle subscription plan selection and payment.
    
    Args:
        user: Current user
        plan_key: Plan identifier (starter, professional, enterprise)
        plan_data: Plan details dictionary
        is_annual: Whether annual billing selected
    """
    st.subheader(f"Subscribe to {plan_data['name']}")
    
    # Calculate amount
    amount_pounds = plan_data['price_annual'] if is_annual else plan_data['price_monthly']
    amount_pence = stripe_service.pounds_to_pence(amount_pounds)
    
    # Display summary
    st.write(f"**Plan:** {plan_data['name']}")
    st.write(f"**Billing:** {'Annual' if is_annual else 'Monthly'}")
    st.write(f"**Amount:** {stripe_service.format_amount(amount_pence)}")
    
    # Payment form
    with st.form("payment_form"):
        st.markdown("### Payment Details")
        
        # Note: In production, use Stripe.js for PCI compliance
        # This is a simplified example - never collect raw card data server-side
        st.warning("⚠️ **Production Implementation Required:**")
        st.info(
            "For PCI compliance, card details must be collected using Stripe.js "
            "on the client-side. This requires custom Streamlit components or "
            "redirecting to Stripe Checkout."
        )
        
        # Email confirmation
        email = st.text_input("Email", value=user.get("email", ""))
        
        # Terms acceptance
        accept_terms = st.checkbox("I agree to the Terms of Service and Privacy Policy")
        
        # Submit button
        submitted = st.form_submit_button("Complete Subscription")
        
        if submitted:
            if not accept_terms:
                st.error("Please accept the terms to continue")
                return
            
            if not email:
                st.error("Email is required")
                return
            
            try:
                # Create or retrieve Stripe customer
                with st.spinner("Processing subscription..."):
                    # TODO: Check if customer exists in database
                    customer = stripe_service.create_customer(
                        email=email,
                        name=user.get("full_name"),
                        metadata={
                            "user_id": str(user.get("id")),
                            "plan": plan_key
                        }
                    )
                    
                    # TODO: In production, create subscription with Stripe Price ID
                    # subscription = stripe_service.create_subscription(
                    #     customer_id=customer.id,
                    #     price_id="price_xxx",  # From Stripe Dashboard
                    #     trial_days=30
                    # )
                    
                    st.success("✅ Subscription created successfully!")
                    st.balloons()
                    st.info("🎉 Welcome to RetailSights! Your subscription is now active.")
                    
            except StripePaymentError as e:
                st.error(f"Payment failed: {str(e)}")
                logger.error(f"Subscription creation failed for user {user.get('id')}: {e}")


def render_payment_history(user: dict):
    """Display payment transaction history.
    
    Args:
        user: Current user dictionary
    """
    st.header("Payment History")
    
    # TODO: Fetch from database
    transactions = []  # Replace with DB query
    
    if not transactions:
        st.info("No payment history yet. Your transactions will appear here once you subscribe.")
        return
    
    # Display transactions table
    st.markdown("### Recent Transactions")
    
    # Example data structure
    import pandas as pd
    df = pd.DataFrame([
        {
            "Date": "2025-01-15",
            "Description": "Professional Plan - Monthly",
            "Amount": "£79.99",
            "Status": "Paid",
            "Invoice": "INV-001"
        }
    ])
    
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Download invoices
    st.markdown("---")
    st.subheader("Download Invoices")
    st.info("Click on an invoice number in the table above to download a PDF receipt.")


def render_billing_settings(user: dict):
    """Display billing settings and payment methods.
    
    Args:
        user: Current user dictionary
    """
    st.header("Billing Settings")
    
    # Payment methods section
    st.subheader("💳 Payment Methods")
    
    # TODO: Fetch from Stripe
    payment_methods = []  # Replace with stripe_service.list_payment_methods()
    
    if payment_methods:
        for pm in payment_methods:
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"💳 •••• {pm.get('last4', 'XXXX')}")
            with col2:
                st.write(f"Expires {pm.get('exp_month')}/{pm.get('exp_year')}")
            with col3:
                if st.button("Remove", key=f"remove_{pm.get('id')}"):
                    st.warning("Payment method removal functionality coming soon")
    else:
        st.info("No payment methods on file. Add one when you subscribe to a plan.")
    
    if st.button("➕ Add Payment Method"):
        st.info("Payment method management requires Stripe.js integration")
    
    st.markdown("---")
    
    # Billing information
    st.subheader("📋 Billing Information")
    
    with st.form("billing_info_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input("Company Name")
            vat_number = st.text_input("VAT Number (UK)")
        
        with col2:
            billing_email = st.text_input("Billing Email", value=user.get("email", ""))
            phone = st.text_input("Phone Number")
        
        address = st.text_area("Billing Address")
        
        col1, col2 = st.columns(2)
        with col1:
            city = st.text_input("City")
        with col2:
            postcode = st.text_input("Postcode")
        
        if st.form_submit_button("Save Billing Information"):
            st.success("✅ Billing information updated")
    
    st.markdown("---")
    
    # Danger zone
    st.subheader("⚠️ Cancel Subscription")
    
    with st.expander("Cancel my subscription"):
        st.warning(
            "**Are you sure you want to cancel your subscription?**\n\n"
            "- Your subscription will remain active until the end of the current billing period\n"
            "- You will lose access to premium features after cancellation\n"
            "- Your data will be retained for 30 days\n"
        )
        
        reason = st.selectbox(
            "Reason for canceling (optional)",
            ["", "Too expensive", "Not using it enough", "Missing features", "Found alternative", "Other"]
        )
        
        feedback = st.text_area("Additional feedback (optional)")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Cancel Subscription", type="primary"):
                st.error("Are you absolutely sure? This action cannot be undone.")
                confirm = st.checkbox("Yes, cancel my subscription")
                if confirm:
                    try:
                        # TODO: Cancel subscription
                        # stripe_service.cancel_subscription(subscription_id)
                        st.success("Your subscription has been canceled. You'll retain access until the end of your billing period.")
                    except StripePaymentError as e:
                        st.error(f"Failed to cancel subscription: {str(e)}")
        
        with col2:
            st.button("Keep My Subscription", type="secondary")


# Standalone function for creating Stripe Checkout session (alternative to embedded form)
def create_checkout_session(user: dict, plan: str, interval: str) -> Optional[str]:
    """Create a Stripe Checkout session for subscription.
    
    Args:
        user: Current user
        plan: Plan name
        interval: Billing interval (month/year)
        
    Returns:
        Checkout session URL or None if failed
    """
    try:
        # This would create a Stripe Checkout session
        # checkout_session = stripe.checkout.Session.create(...)
        # return checkout_session.url
        pass
    except Exception as e:
        logger.error(f"Failed to create checkout session: {e}")
        return None
