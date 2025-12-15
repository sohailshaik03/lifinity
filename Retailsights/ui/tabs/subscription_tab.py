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
    
    st.info("👋 Welcome! Choose a subscription plan to unlock premium features for your retail business.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Billing interval selector - centered
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        billing_interval = st.radio(
            "Select Billing Interval",
            ["Monthly", "Annual (Save 17%)"],
            horizontal=True,
            help="Annual billing includes a 17% discount"
        )
    
    is_annual = "Annual" in billing_interval
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Plan comparison
    plans = {
        "starter": {
            "name": "Starter",
            "price_monthly": 29.99,
            "price_annual": 299.00,
            "icon": "🌱",
            "color": "#4CAF50",
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
            "color": "#2196F3",
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
            "color": "#9C27B0",
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
    
    # Display plans in columns with equal height cards
    cols = st.columns(3, gap="medium")
    
    for idx, (plan_key, plan_data) in enumerate(plans.items()):
        with cols[idx]:
            # Use Streamlit container for consistent styling
            with st.container():
                # Recommended badge with fixed height
                if plan_data["recommended"]:
                    st.markdown(f"""
                        <div style="
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            padding: 8px 16px;
                            border-radius: 20px;
                            text-align: center;
                            font-weight: bold;
                            font-size: 13px;
                            margin-bottom: 12px;
                            height: 34px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                        ">
                            ⭐ RECOMMENDED
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("<div style='height: 46px; margin-bottom: 12px;'></div>", unsafe_allow_html=True)
                
                # Card with border
                st.markdown(f"""
                    <div style="
                        border: 3px solid {plan_data['color']};
                        border-radius: 16px;
                        padding: 28px 24px;
                        background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(250,250,250,0.98) 100%);
                        box-shadow: 0 8px 16px rgba(0,0,0,0.08);
                        min-height: 650px;
                    ">
                """, unsafe_allow_html=True)
                
                # Plan icon and name
                st.markdown(f"""
                    <div style="text-align: center; margin-bottom: 24px;">
                        <div style="font-size: 56px; margin-bottom: 12px; line-height: 1;">{plan_data['icon']}</div>
                        <h2 style="margin: 0; color: {plan_data['color']}; font-size: 28px; font-weight: 700;">{plan_data['name']}</h2>
                    </div>
                """, unsafe_allow_html=True)
                
                # Price display with fixed height
                if is_annual:
                    price = plan_data['price_annual']
                    price_per_month = price / 12
                    st.markdown(f"""
                        <div style="text-align: center; margin: 24px 0; height: 110px; display: flex; flex-direction: column; justify-content: center;">
                            <div style="font-size: 42px; font-weight: 800; color: {plan_data['color']}; line-height: 1;">
                                £{price:.0f}
                            </div>
                            <div style="font-size: 15px; color: #666; margin-top: 6px; font-weight: 500;">
                                per year
                            </div>
                            <div style="font-size: 13px; color: #999; margin-top: 4px;">
                                (£{price_per_month:.2f}/month)
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    price = plan_data['price_monthly']
                    st.markdown(f"""
                        <div style="text-align: center; margin: 24px 0; height: 110px; display: flex; flex-direction: column; justify-content: center;">
                            <div style="font-size: 42px; font-weight: 800; color: {plan_data['color']}; line-height: 1;">
                                £{price:.2f}
                            </div>
                            <div style="font-size: 15px; color: #666; margin-top: 6px; font-weight: 500;">
                                per month
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("<hr style='margin: 20px 0; border: none; border-top: 2px solid #e8e8e8;'>", unsafe_allow_html=True)
                
                # Features list with fixed height
                st.markdown("<div style='min-height: 280px; max-height: 280px; overflow-y: auto;'>", unsafe_allow_html=True)
                for feature in plan_data['features']:
                    st.markdown(f"""
                        <div style="margin: 12px 0; padding-left: 4px; display: flex; align-items: flex-start;">
                            <span style="color: {plan_data['color']}; font-size: 18px; margin-right: 10px; flex-shrink: 0;">✓</span>
                            <span style="font-size: 14px; color: #333; line-height: 1.5;">{feature}</span>
                        </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Button outside the card for better alignment
                st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
                button_type = "primary" if plan_data["recommended"] else "secondary"
                if st.button(
                    f"Choose {plan_data['name']}", 
                    key=f"choose_{plan_key}", 
                    type=button_type, 
                    use_container_width=True
                ):
                    handle_plan_selection(user, plan_key, plan_data, is_annual, user_email)
    
    # Additional info
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Trust badges
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
            <div style="text-align: center; padding: 16px;">
                <div style="font-size: 32px;">💯</div>
                <div style="font-size: 12px; font-weight: bold; margin-top: 8px;">30-Day Money-Back</div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
            <div style="text-align: center; padding: 16px;">
                <div style="font-size: 32px;">🔒</div>
                <div style="font-size: 12px; font-weight: bold; margin-top: 8px;">Secure Payment</div>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
            <div style="text-align: center; padding: 16px;">
                <div style="font-size: 32px;">⚡</div>
                <div style="font-size: 12px; font-weight: bold; margin-top: 8px;">Instant Activation</div>
            </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown("""
            <div style="text-align: center; padding: 16px;">
                <div style="font-size: 32px;">🎯</div>
                <div style="font-size: 12px; font-weight: bold; margin-top: 8px;">No Hidden Fees</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # FAQ
    with st.expander("❓ Frequently Asked Questions"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Can I change plans later?**  
            Yes! You can upgrade or downgrade at any time. Changes take effect immediately.
            
            **What payment methods do you accept?**  
            We accept all major credit/debit cards, Apple Pay, and Google Pay via Stripe.
            
            **Is there a free trial?**  
            Contact our sales team for enterprise trial options.
            """)
        
        with col2:
            st.markdown("""
            **Is my payment secure?**  
            Absolutely! All payments are processed securely via Stripe with PCI-DSS compliance and 3D Secure authentication.
            
            **Can I cancel anytime?**  
            Yes, you can cancel your subscription at any time with no penalties.
            
            **Do you offer refunds?**  
            Yes! We offer a 30-day money-back guarantee on all plans.
            """)
    
    # Support contact
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("💬 Need help choosing? Contact our sales team at **sales@retailsight.com** or chat with us below.")



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
