"""Stripe payment processing service for UK client.

Handles subscription billing, one-time payments, and webhook processing.
Configured for UK market with GBP currency support.
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal

import stripe
from loguru import logger

from Retailsights.config import config


class StripePaymentError(Exception):
    """Custom exception for Stripe payment errors."""
    pass


class StripePaymentService:
    """Stripe payment integration for RetailSights.
    
    Features:
    - Subscription billing (monthly/annual plans)
    - One-time payments
    - Customer management
    - Payment method handling
    - Webhook event processing
    - UK market optimized (GBP, UK payment methods)
    """
    
    def __init__(self):
        """Initialize Stripe with API keys from config."""
        self.stripe = stripe
        
        # Set API key
        stripe_key = config.STRIPE_SECRET_KEY
        if not stripe_key:
            logger.warning("STRIPE_SECRET_KEY not configured - payment features disabled")
            self.enabled = False
            return
        
        self.stripe.api_key = stripe_key
        self.enabled = True
        
        # UK-specific configuration
        self.currency = config.STRIPE_CURRENCY
        self.country = config.STRIPE_COUNTRY
        
        logger.info(f"Stripe payment service initialized - Currency: {self.currency.upper()}, Country: {self.country}")
    
    def is_enabled(self) -> bool:
        """Check if Stripe is properly configured.
        
        Returns:
            True if Stripe API keys are configured
        """
        return self.enabled
    
    # ================================================================
    # CUSTOMER MANAGEMENT
    # ================================================================
    
    def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Create a new Stripe customer.
        
        Args:
            email: Customer email address
            name: Customer full name
            metadata: Additional metadata (e.g., user_id, shop_id)
            
        Returns:
            Customer object dictionary
            
        Raises:
            StripePaymentError: If customer creation fails
        """
        if not self.enabled:
            raise StripePaymentError("Stripe is not configured")
        
        try:
            customer = self.stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {},
                preferred_locales=["en-GB"],  # UK English
            )
            
            logger.info(f"Created Stripe customer: {customer.id} for {email}")
            return customer
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            raise StripePaymentError(f"Customer creation failed: {str(e)}")
    
    def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve customer by Stripe customer ID.
        
        Args:
            customer_id: Stripe customer ID
            
        Returns:
            Customer object or None if not found
        """
        if not self.enabled:
            return None
        
        try:
            customer = self.stripe.Customer.retrieve(customer_id)
            return customer
        except stripe.error.InvalidRequestError:
            logger.warning(f"Customer not found: {customer_id}")
            return None
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving customer: {e}")
            return None
    
    def update_customer(
        self,
        customer_id: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Update customer information.
        
        Args:
            customer_id: Stripe customer ID
            email: New email address
            name: New name
            metadata: Updated metadata
            
        Returns:
            Updated customer object
            
        Raises:
            StripePaymentError: If update fails
        """
        if not self.enabled:
            raise StripePaymentError("Stripe is not configured")
        
        try:
            update_data = {}
            if email:
                update_data["email"] = email
            if name:
                update_data["name"] = name
            if metadata:
                update_data["metadata"] = metadata
            
            customer = self.stripe.Customer.modify(customer_id, **update_data)
            logger.info(f"Updated Stripe customer: {customer_id}")
            return customer
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to update customer: {e}")
            raise StripePaymentError(f"Customer update failed: {str(e)}")
    
    # ================================================================
    # PAYMENT METHODS
    # ================================================================
    
    def attach_payment_method(
        self,
        customer_id: str,
        payment_method_id: str
    ) -> Dict[str, Any]:
        """Attach payment method to customer.
        
        Args:
            customer_id: Stripe customer ID
            payment_method_id: Payment method ID from Stripe.js
            
        Returns:
            PaymentMethod object
            
        Raises:
            StripePaymentError: If attachment fails
        """
        if not self.enabled:
            raise StripePaymentError("Stripe is not configured")
        
        try:
            payment_method = self.stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id
            )
            
            # Set as default payment method
            self.stripe.Customer.modify(
                customer_id,
                invoice_settings={
                    "default_payment_method": payment_method_id
                }
            )
            
            logger.info(f"Attached payment method {payment_method_id} to customer {customer_id}")
            return payment_method
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to attach payment method: {e}")
            raise StripePaymentError(f"Payment method attachment failed: {str(e)}")
    
    def list_payment_methods(self, customer_id: str) -> List[Dict[str, Any]]:
        """List all payment methods for customer.
        
        Args:
            customer_id: Stripe customer ID
            
        Returns:
            List of PaymentMethod objects
        """
        if not self.enabled:
            return []
        
        try:
            payment_methods = self.stripe.PaymentMethod.list(
                customer=customer_id,
                type="card"
            )
            return payment_methods.data
        except stripe.error.StripeError as e:
            logger.error(f"Failed to list payment methods: {e}")
            return []
    
    # ================================================================
    # ONE-TIME PAYMENTS
    # ================================================================
    
    def create_payment_intent(
        self,
        amount: int,
        customer_id: str,
        description: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Create a payment intent for one-time payment.
        
        Args:
            amount: Amount in pence (e.g., 1000 = £10.00)
            customer_id: Stripe customer ID
            description: Payment description
            metadata: Additional metadata
            
        Returns:
            PaymentIntent object with client_secret
            
        Raises:
            StripePaymentError: If creation fails
        """
        if not self.enabled:
            raise StripePaymentError("Stripe is not configured")
        
        try:
            payment_intent = self.stripe.PaymentIntent.create(
                amount=amount,
                currency=self.currency,
                customer=customer_id,
                description=description,
                metadata=metadata or {},
                automatic_payment_methods={"enabled": True},
            )
            
            logger.info(f"Created payment intent: {payment_intent.id} for £{amount/100:.2f}")
            return payment_intent
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create payment intent: {e}")
            raise StripePaymentError(f"Payment creation failed: {str(e)}")
    
    def confirm_payment(self, payment_intent_id: str) -> Tuple[bool, Optional[str]]:
        """Confirm and retrieve payment status.
        
        Args:
            payment_intent_id: PaymentIntent ID
            
        Returns:
            Tuple of (success, error_message)
        """
        if not self.enabled:
            return False, "Stripe not configured"
        
        try:
            payment_intent = self.stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if payment_intent.status == "succeeded":
                logger.info(f"Payment succeeded: {payment_intent_id}")
                return True, None
            elif payment_intent.status == "requires_payment_method":
                return False, "Payment method required"
            elif payment_intent.status == "canceled":
                return False, "Payment was canceled"
            else:
                return False, f"Payment status: {payment_intent.status}"
                
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve payment: {e}")
            return False, str(e)
    
    # ================================================================
    # SUBSCRIPTION MANAGEMENT
    # ================================================================
    
    def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        trial_days: Optional[int] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Create a subscription for customer.
        
        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID (from product setup)
            trial_days: Number of trial days (optional)
            metadata: Additional metadata
            
        Returns:
            Subscription object
            
        Raises:
            StripePaymentError: If creation fails
        """
        if not self.enabled:
            raise StripePaymentError("Stripe is not configured")
        
        try:
            subscription_data = {
                "customer": customer_id,
                "items": [{"price": price_id}],
                "metadata": metadata or {},
            }
            
            if trial_days:
                subscription_data["trial_period_days"] = trial_days
            
            subscription = self.stripe.Subscription.create(**subscription_data)
            
            logger.info(f"Created subscription: {subscription.id} for customer {customer_id}")
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create subscription: {e}")
            raise StripePaymentError(f"Subscription creation failed: {str(e)}")
    
    def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True
    ) -> Dict[str, Any]:
        """Cancel a subscription.
        
        Args:
            subscription_id: Stripe subscription ID
            at_period_end: If True, cancel at end of billing period
            
        Returns:
            Canceled subscription object
            
        Raises:
            StripePaymentError: If cancellation fails
        """
        if not self.enabled:
            raise StripePaymentError("Stripe is not configured")
        
        try:
            if at_period_end:
                subscription = self.stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
                logger.info(f"Subscription {subscription_id} will cancel at period end")
            else:
                subscription = self.stripe.Subscription.delete(subscription_id)
                logger.info(f"Subscription {subscription_id} canceled immediately")
            
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription: {e}")
            raise StripePaymentError(f"Subscription cancellation failed: {str(e)}")
    
    def get_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve subscription details.
        
        Args:
            subscription_id: Stripe subscription ID
            
        Returns:
            Subscription object or None
        """
        if not self.enabled:
            return None
        
        try:
            subscription = self.stripe.Subscription.retrieve(subscription_id)
            return subscription
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve subscription: {e}")
            return None
    
    def list_customer_subscriptions(self, customer_id: str) -> List[Dict[str, Any]]:
        """List all subscriptions for customer.
        
        Args:
            customer_id: Stripe customer ID
            
        Returns:
            List of subscription objects
        """
        if not self.enabled:
            return []
        
        try:
            subscriptions = self.stripe.Subscription.list(
                customer=customer_id,
                status="all"
            )
            return subscriptions.data
        except stripe.error.StripeError as e:
            logger.error(f"Failed to list subscriptions: {e}")
            return []
    
    # ================================================================
    # PRODUCTS & PRICES (UK Market)
    # ================================================================
    
    def create_product(
        self,
        name: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Create a product (subscription tier).
        
        Args:
            name: Product name (e.g., "Professional Plan")
            description: Product description
            metadata: Additional metadata
            
        Returns:
            Product object
        """
        if not self.enabled:
            raise StripePaymentError("Stripe is not configured")
        
        try:
            product = self.stripe.Product.create(
                name=name,
                description=description,
                metadata=metadata or {}
            )
            logger.info(f"Created product: {product.id} - {name}")
            return product
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create product: {e}")
            raise StripePaymentError(f"Product creation failed: {str(e)}")
    
    def create_price(
        self,
        product_id: str,
        amount: int,
        interval: str = "month",
        interval_count: int = 1
    ) -> Dict[str, Any]:
        """Create a price for product.
        
        Args:
            product_id: Stripe product ID
            amount: Amount in pence (e.g., 2999 = £29.99/month)
            interval: Billing interval (month, year)
            interval_count: Number of intervals between billings
            
        Returns:
            Price object
        """
        if not self.enabled:
            raise StripePaymentError("Stripe is not configured")
        
        try:
            price = self.stripe.Price.create(
                product=product_id,
                unit_amount=amount,
                currency=self.currency,
                recurring={
                    "interval": interval,
                    "interval_count": interval_count
                }
            )
            logger.info(f"Created price: {price.id} - £{amount/100:.2f}/{interval}")
            return price
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create price: {e}")
            raise StripePaymentError(f"Price creation failed: {str(e)}")
    
    # ================================================================
    # WEBHOOKS
    # ================================================================
    
    def construct_webhook_event(
        self,
        payload: bytes,
        signature: str
    ) -> Optional[Dict[str, Any]]:
        """Verify and construct webhook event.
        
        Args:
            payload: Raw request body
            signature: Stripe-Signature header
            
        Returns:
            Webhook event object or None if verification fails
        """
        if not self.enabled:
            return None
        
        webhook_secret = config.STRIPE_WEBHOOK_SECRET
        if not webhook_secret:
            logger.error("STRIPE_WEBHOOK_SECRET not configured")
            return None
        
        try:
            event = self.stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
            logger.info(f"Webhook event verified: {event['type']}")
            return event
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e}")
            return None
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {e}")
            return None
    
    # ================================================================
    # UTILITY METHODS
    # ================================================================
    
    def format_amount(self, amount_pence: int) -> str:
        """Format amount for display.
        
        Args:
            amount_pence: Amount in pence
            
        Returns:
            Formatted string (e.g., "£29.99")
        """
        return f"£{amount_pence / 100:.2f}"
    
    def pence_to_pounds(self, pence: int) -> Decimal:
        """Convert pence to pounds.
        
        Args:
            pence: Amount in pence
            
        Returns:
            Amount in pounds as Decimal
        """
        return Decimal(pence) / 100
    
    def pounds_to_pence(self, pounds: float) -> int:
        """Convert pounds to pence.
        
        Args:
            pounds: Amount in pounds
            
        Returns:
            Amount in pence as integer
        """
        return int(pounds * 100)


# Singleton instance
stripe_service = StripePaymentService()
