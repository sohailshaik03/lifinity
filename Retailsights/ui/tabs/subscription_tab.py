"""
Subscription Management Tab
Displays current subscription tier, usage stats, upgrade options, and handles payments
"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional
import os

from ...services.subscription_service import SubscriptionService
from ...services.stripe_payment_service import stripe_service, StripePaymentError
from ...repositories.subscription_repo import SubscriptionRepo
from ...logger import log as logger


def render_subscription_tab(state=None):
    """Render the subscription management interface"""
    
    st.title("💎 Subscription Management")
    
    # Check if user is logged in
    user = st.session_state.get('auth_user')
    if not user or not user.get('id'):
        st.warning("⚠️ Please log in to view subscription details")
        return
    
    user_id = user['id']
    user_email = user.get('email', '')
    
    try:
        # Get user's current subscription
        subscription = SubscriptionRepo.get_user_subscription(user_id)
        
        if not subscription:
            # No subscription found - show available plans
            render_no_subscription_view(user, user_id, user_email)
            return
        
        current_tier = subscription.get('tier', 'basic')
        is_trial = subscription.get('is_trial', False)
        trial_ends_at = subscription.get('trial_ends_at')
        subscription_ends_at = subscription.get('subscription_ends_at')
        
        # Get tier features
        tier_limits = SubscriptionService.get_tier_limits(current_tier)
        
        # Display trial banner if applicable
        if is_trial and trial_ends_at:
            days_left = (trial_ends_at - datetime.now()).days
            trial_type = "basic features only" if tier_limits.get('trial_features_only') else "full features"
            
            if days_left > 0:
                st.info(f"🎁 **FREE TRIAL ACTIVE** - {days_left} days remaining ({trial_type})")
            else:
                st.error("⏰ **TRIAL EXPIRED** - Please upgrade to continue using RetailSight")
        
        # Current Plan Section
        st.subheader(f"📦 Current Plan: {current_tier.upper()}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Plan Type", current_tier.replace('_', ' ').title())
        
        with col2:
            price_display = tier_limits.get('price', 'N/A')
            st.metric("Price", price_display)
        
        with col3:
            status = "Trial" if is_trial else "Active"
            st.metric("Status", status)
        
        # Display plan limits
        st.markdown("### 📊 Your Plan Limits")
        
        limits_col1, limits_col2, limits_col3 = st.columns(3)
        
        with limits_col1:
            max_rows = tier_limits.get('max_rows', 'Unlimited')
            st.info(f"**Max Rows:** {max_rows:,}" if isinstance(max_rows, int) else f"**Max Rows:** {max_rows}")
        
        with limits_col2:
            max_cols = tier_limits.get('max_columns', 'Unlimited')
            st.info(f"**Max Columns:** {max_cols:,}" if isinstance(max_cols, int) else f"**Max Columns:** {max_cols}")
        
        with limits_col3:
            max_file_size = tier_limits.get('max_file_size_mb', 'Unlimited')
            st.info(f"**Max File Size:** {max_file_size}MB" if isinstance(max_file_size, int) else f"**Max File Size:** {max_file_size}")
        
        # Features list
        features = tier_limits.get('features', [])
        if features:
            st.markdown("### ✨ Your Features")
            for feature in features:
                st.markdown(f"✅ {feature}")
        
        st.divider()
        
        # Payment prompt for BASIC users after trial
        if current_tier == 'basic' and is_trial and trial_ends_at and (trial_ends_at - datetime.now()).days <= 0:
            st.warning("⚠️ Your trial has ended. Purchase the BASIC plan to continue.")
            if st.button("💳 Pay £25 - Continue with BASIC"):
                st.session_state['show_payment'] = ('basic', 25)
                st.rerun()
        
        st.divider()
        
        # Upgrade Options Section
        st.subheader("🚀 Upgrade Your Plan")
        
        # Show payment modal if triggered
        if st.session_state.get('show_payment'):
            show_payment_modal(user_id, *st.session_state['show_payment'])
        else:
            # Get all available plans
            tiers = ['basic', 'premium', 'ultra_premium']
            
            upgrade_cols = st.columns(len(tiers))
            
            for idx, tier in enumerate(tiers):
                with upgrade_cols[idx]:
                    render_plan_card(tier, current_tier, user_id)
        
        # Billing History Section
        st.divider()
        st.subheader("📄 Billing History")
        
        payments = SubscriptionRepo.get_user_payments(user_id)
        
        if payments and len(payments) > 0:
            for payment in payments:
                with st.expander(f"Payment on {payment['created_at'].strftime('%Y-%m-%d %H:%M')}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        amount_display = payment.get('amount', 0)
                        st.write(f"**Amount:** £{amount_display:.2f}")
                    with col2:
                        status = payment.get('payment_status', 'unknown')
                        st.write(f"**Status:** {status}")
                    with col3:
                        method = payment.get('payment_method', 'N/A')
                        st.write(f"**Method:** {method}")
        else:
            st.info("📭 No billing history yet. Start your subscription to see payment records here.")
        
        # FAQ Section
        st.divider()
        render_faq()
        
    except Exception as e:
        logger.error(f"Error rendering subscription tab: {e}", exc_info=True)
        st.error("❌ Error loading subscription information. Please try again.")


def render_plan_card(tier: str, current_tier: str, user_id: int):
    """Render a single plan card with upgrade option"""
    
    try:
        tier_limits = SubscriptionService.get_tier_limits(tier)
        
        # Card styling
        is_current = tier == current_tier
        border_color = "#4CAF50" if is_current else "#ddd"
        
        st.markdown(f"""
        <div style="border: 2px solid {border_color}; border-radius: 10px; padding: 20px; height: 100%;">
            <h3 style="text-align: center;">{tier.replace('_', ' ').title()}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Price
        price = tier_limits.get('price', 'Contact Us')
        st.markdown(f"### {price}")
        
        # Trial info
        trial_days = tier_limits.get('trial_days', 0)
        trial_type = "basic features only" if tier_limits.get('trial_features_only') else "full features"
        
        if trial_days > 0:
            st.caption(f"🎁 {trial_days}-day free trial ({trial_type})")
        else:
            st.caption("💳 Payment required to start")
        
        # Key features
        st.markdown("**Key Features:**")
        features = tier_limits.get('features', [])[:4]  # Show first 4 features
        for feature in features:
            st.markdown(f"• {feature}")
        
        # Action button
        if is_current:
            st.success("✓ Current Plan")
        else:
            price_amount = tier_limits.get('price_amount', 0)
            billing_type = tier_limits.get('billing_type', 'monthly')
            trial_days = tier_limits.get('trial_days', 0)
            
            if trial_days > 0:
                button_text = f"Start {trial_days}-Day Trial"
            else:
                button_text = "Subscribe Now"
            
            if st.button(button_text, key=f"upgrade_{tier}", width="stretch"):
                st.session_state['show_payment'] = (tier, price_amount)
                st.rerun()
                
    except Exception as e:
        logger.error(f"Error rendering plan card for {tier}: {e}")
        st.error(f"Error loading {tier} plan details")


def show_payment_modal(user_id: int, plan_tier: str, amount: int):
    """Display payment modal with Stripe checkout"""
    
    st.markdown("---")
    st.subheader(f"💳 Checkout - {plan_tier.replace('_', ' ').title()} Plan")
    
    tier_limits = SubscriptionService.get_tier_limits(plan_tier)
    billing_type = tier_limits.get('billing_type', 'monthly')
    
    # Order summary
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Order Summary")
        st.write(f"**Plan:** {plan_tier.replace('_', ' ').title()}")
        st.write(f"**Billing:** {billing_type.replace('-', ' ').title()}")
        
        if billing_type == 'one-time':
            st.write(f"**Total:** £{amount}")
        else:
            st.write(f"**Monthly:** £{amount}")
    
    with col2:
        st.markdown("### 🔒 Secure Payment")
        st.caption("Powered by Stripe")
        st.caption("PCI-DSS Compliant")
        st.caption("3D Secure Protection")
    
    # Payment button
    col_pay, col_cancel = st.columns(2)
    
    with col_pay:
        if st.button("🔐 Proceed to Payment", width="stretch", type="primary"):
            process_payment(user_id, plan_tier, amount, billing_type)
    
    with col_cancel:
        if st.button("❌ Cancel", width="stretch"):
            del st.session_state['show_payment']
            st.rerun()


def process_payment(user_id: int, plan_tier: str, amount: int, billing_type: str):
    """Process payment via Stripe Checkout"""
    
    try:
        # Check if Stripe is configured
        stripe_key = os.getenv('STRIPE_SECRET_KEY')
        
        if not stripe_key or stripe_key.startswith('sk_test_'):
            # Test mode - simulate payment
            st.warning("⚠️ Test Mode: Stripe not configured. Simulating successful payment...")
            
            # In production, this would create a real payment
            success = SubscriptionRepo.upgrade_subscription(
                user_id=user_id,
                new_tier=plan_tier,
                payment_method='test'
            )
            
            if success:
                st.success("✅ Payment successful! Your subscription has been upgraded.")
                st.balloons()
                del st.session_state['show_payment']
                st.rerun()
            else:
                st.error("❌ Failed to upgrade subscription. Please try again.")
            
            return
        
        # Production mode - use Stripe
        payment_service = PaymentService()
        
        # Generate secure token to prevent price tampering
        timestamp = int(datetime.now().timestamp())
        secure_token = payment_service.generate_secure_token(user_id, amount, timestamp)
        
        # Create success and cancel URLs
        base_url = os.getenv('APP_URL', 'http://localhost:8501')
        success_url = f"{base_url}?payment=success&tier={plan_tier}"
        cancel_url = f"{base_url}?payment=cancelled"
        
        # Create Stripe Checkout Session
        checkout_session = payment_service.create_checkout_session(
            amount=amount,
            currency='GBP',
            user_id=user_id,
            plan_tier=plan_tier,
            billing_type=billing_type,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        if checkout_session and 'url' in checkout_session:
            st.success("🔗 Redirecting to secure checkout...")
            st.markdown(f"[Click here if not redirected automatically]({checkout_session['url']})")
            
            # Open checkout in new tab
            st.link_button("🔐 Open Secure Checkout", checkout_session['url'], width="stretch")
        else:
            st.error("❌ Failed to create checkout session. Please try again.")
            
    except Exception as e:
        logger.error(f"Payment processing error: {e}", exc_info=True)
        st.error(f"❌ Payment error: {str(e)}")


def render_no_subscription_view(user: dict, user_id: int, user_email: str):
    """Render view when user has no subscription - show available plans"""
    
    st.subheader("📋 Choose Your Subscription Plan")
    
    # Billing interval selector
    billing_interval = st.radio(
        "Billing Interval:",
        ["Monthly", "Annual (Save 17%)"],
        horizontal=True,
        help="Annual billing includes a 17% discount"
    )
    
    is_annual = "Annual" in billing_interval
    
    st.divider()
    
    # Plan comparison
    plans = {
        "starter": {
            "name": "Starter",
            "price_monthly": 29.99,
            "price_annual": 299.00,
            "icon": "🌱",
            "features": [
                "Up to 3 shop locations",
                "Basic analytics dashboard",
                "Sales & inventory tracking",
                "Expiry date monitoring",
                "Email support",
                "1GB data storage"
            ],
            "recommended": False
        },
        "professional": {
            "name": "Professional",
            "price_monthly": 79.99,
            "price_annual": 799.00,
            "icon": "⭐",
            "features": [
                "Up to 10 shop locations",
                "Advanced analytics & AI insights",
                "Markdown pricing optimization",
                "Waste reduction reports",
                "Custom label printing",
                "Priority support",
                "10GB data storage",
                "API access"
            ],
            "recommended": True
        },
        "enterprise": {
            "name": "Enterprise",
            "price_monthly": 199.99,
            "price_annual": 1999.00,
            "icon": "🚀",
            "features": [
                "Unlimited shop locations",
                "Enterprise AI analytics",
                "Multi-store management",
                "Advanced automation",
                "Dedicated account manager",
                "24/7 phone support",
                "Unlimited data storage",
                "Custom integrations",
                "SLA guarantee"
            ],
            "recommended": False
        }
    }
    
    # Display plans in columns
    cols = st.columns(3)
    
    for idx, (plan_key, plan_data) in enumerate(plans.items()):
        with cols[idx]:
            # Recommended badge
            if plan_data["recommended"]:
                st.info("⭐ **RECOMMENDED**")
            else:
                st.markdown("")
            
            # Plan header
            st.markdown(f"### {plan_data['icon']} {plan_data['name']}")
            
            # Price
            if is_annual:
                price = plan_data['price_annual']
                price_per_month = price / 12
                st.metric(label="Annual Price", value=f"£{price:.0f}/year")
                st.caption(f"£{price_per_month:.2f} per month")
            else:
                price = plan_data['price_monthly']
                st.metric(label="Monthly Price", value=f"£{price:.2f}/mo")
            
            st.markdown("---")
            
            # Features
            st.markdown("**Features:**")
            for feature in plan_data['features']:
                st.markdown(f"✓ {feature}")
            
            st.markdown("---")
            
            # Subscribe button
            button_type = "primary" if plan_data["recommended"] else "secondary"
            if st.button(
                f"Choose {plan_data['name']}", 
                key=f"choose_{plan_key}", 
                type=button_type, 
                use_container_width=True
            ):
                handle_plan_selection(user, plan_key, plan_data, is_annual, user_email)
    
    st.divider()
    
    # Simple info footer
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("💯 30-Day Money-Back Guarantee")
    with col2:
        st.info("🔒 Secure Payment via Stripe")
    with col3:
        st.info("⚡ Instant Activation")
    
    # Simple FAQ
    with st.expander("❓ Frequently Asked Questions"):
        st.markdown("""
        **Can I change plans later?**  
        Yes! You can upgrade or downgrade at any time.
        
        **What payment methods do you accept?**  
        Credit/debit cards, Apple Pay, and Google Pay via Stripe.
        
        **Is my payment secure?**  
        Yes! All payments are processed securely via Stripe with PCI-DSS compliance.
        
        **Can I cancel anytime?**  
        Yes, cancel anytime with no penalties.
        
        **Do you offer refunds?**  
        30-day money-back guarantee on all plans.
        """)
    
    st.info("💬 Need help? Contact **sales@retailsight.com**")


def handle_plan_selection(user: dict, plan_key: str, plan_data: dict, is_annual: bool, user_email: str):
    """Handle when user selects a plan"""
    
    st.session_state['selected_plan'] = {
        'plan_key': plan_key,
        'plan_data': plan_data,
        'is_annual': is_annual,
        'user_email': user_email
    }
    st.rerun()


def render_faq():
    """Render frequently asked questions"""
    
    st.subheader("❓ Frequently Asked Questions")
    
    with st.expander("What happens during the free trial?"):
        st.write("""
        - **BASIC Plan**: 7-day trial with basic features only (limited analysis types, smaller file sizes)
        - **PREMIUM & ULTRA Plans**: No free trial - payment required to start
        - You can cancel BASIC trial anytime without charge
        - After trial ends, BASIC plan requires a one-time payment of £25
        - PREMIUM and ULTRA plans start immediately upon payment
        """)
    
    with st.expander("How does billing work?"):
        st.write("""
        - **BASIC**: £25 one-time payment (lifetime access)
        - **PREMIUM**: £49 charged monthly
        - **ULTRA PREMIUM**: £199 charged monthly
        - All payments are processed securely via Stripe
        - You can cancel subscription anytime
        """)
    
    with st.expander("Can I upgrade or downgrade my plan?"):
        st.write("""
        Yes! You can upgrade or downgrade at any time:
        - Upgrades take effect immediately
        - Downgrades take effect at the end of the current billing period
        - Pro-rated refunds available for annual plans
        """)
    
    with st.expander("What payment methods do you accept?"):
        st.write("""
        We accept:
        - Credit cards (Visa, Mastercard, Amex)
        - Debit cards
        - Apple Pay & Google Pay
        - Bank transfers (for enterprise plans)
        
        All payments are PCI-DSS compliant and secured with 3D Secure authentication.
        """)
    
    with st.expander("Is my payment information secure?"):
        st.write("""
        Absolutely! We use Stripe for payment processing, which means:
        - Your card details never touch our servers
        - PCI-DSS Level 1 compliance (highest security standard)
        - 3D Secure authentication for fraud prevention
        - End-to-end encryption for all transactions
        """)
    
    with st.expander("Can I get a refund?"):
        st.write("""
        - **BASIC plan**: 30-day money-back guarantee (one-time payment)
        - **Monthly plans**: Pro-rated refunds available
        - **Trial period**: Cancel anytime with no charges
        
        Contact support@retailsight.com for refund requests.
        """)
