# Stripe Payment Integration Guide

## Overview
This document describes the Stripe payment integration for RetailSights, configured specifically for the UK market with GBP currency support.

## Features
- ✅ Subscription billing (monthly/annual)
- ✅ One-time payments
- ✅ Customer management
- ✅ Payment method storage
- ✅ Webhook event processing
- ✅ UK market optimized (GBP, UK payment methods)
- ✅ PCI compliance ready
- ✅ Comprehensive audit trail

## Architecture

### Components

1. **StripePaymentService** (`services/stripe_payment_service.py`)
   - Core payment processing logic
   - Customer and subscription management
   - Webhook handling
   - 600+ lines of production-ready code

2. **Payment UI** (`ui/tabs/payment_tab.py`)
   - Subscription plan selection
   - Payment history
   - Billing settings
   - User-friendly interface

3. **Database Models** (`models.py`)
   - `StripeCustomer` - User-to-Stripe customer mapping
   - `PaymentTransaction` - Payment audit trail
   - `Subscription` - Subscription management

4. **Configuration** (`config.py`)
   - Stripe API keys
   - Currency and country settings
   - Webhook secrets

## Setup Instructions

### 1. Create Stripe Account

1. Sign up at [https://stripe.com](https://stripe.com)
2. Complete business verification for UK
3. Enable payment methods (cards, Apple Pay, Google Pay)

### 2. Get API Keys

1. Go to Stripe Dashboard → Developers → API keys
2. Copy your keys:
   - **Secret Key** (starts with `sk_test_` or `sk_live_`)
   - **Publishable Key** (starts with `pk_test_` or `pk_live_`)

### 3. Configure Environment Variables

Add to your `.env` file or Streamlit Cloud secrets:

```env
# Stripe Configuration (UK)
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxx
STRIPE_CURRENCY=gbp
STRIPE_COUNTRY=GB
```

**For Streamlit Cloud:**
```toml
# .streamlit/secrets.toml
[default]
STRIPE_SECRET_KEY = "sk_live_xxxxxxxxxxxxxxxxxxxxx"
STRIPE_PUBLISHABLE_KEY = "pk_live_xxxxxxxxxxxxxxxxxxxxx"
STRIPE_WEBHOOK_SECRET = "whsec_xxxxxxxxxxxxxxxxxxxxx"
STRIPE_CURRENCY = "gbp"
STRIPE_COUNTRY = "GB"
```

### 4. Install Dependencies

```bash
pip install stripe>=7.0.0
```

### 5. Run Database Migration

```bash
# Apply the payment tables migration
psql $DATABASE_URL < Retailsights/migrations/add_stripe_payment_tables.sql
```

Or using Python:
```python
from Retailsights.db import engine
from Retailsights.models import Base

# Create all tables including payment tables
Base.metadata.create_all(bind=engine)
```

## Creating Products & Prices in Stripe

### Option 1: Stripe Dashboard

1. Go to **Products** → **Add Product**
2. Create three products:

**Starter Plan:**
- Name: "Starter Plan"
- Description: "Perfect for small retailers"
- Pricing:
  - Monthly: £29.99/month
  - Annual: £299/year (save 17%)

**Professional Plan:**
- Name: "Professional Plan"
- Description: "For growing retail businesses"
- Pricing:
  - Monthly: £79.99/month
  - Annual: £799/year (save 17%)

**Enterprise Plan:**
- Name: "Enterprise Plan"
- Description: "For large retail operations"
- Pricing:
  - Monthly: £199.99/month
  - Annual: £1,999/year (save 17%)

3. Copy the **Price IDs** for each (format: `price_xxxxxxxxxxxxx`)

### Option 2: Using the API

```python
from Retailsights.services.stripe_payment_service import stripe_service

# Create Starter product
starter_product = stripe_service.create_product(
    name="Starter Plan",
    description="Perfect for small retailers"
)

# Create monthly price
starter_monthly = stripe_service.create_price(
    product_id=starter_product.id,
    amount=2999,  # £29.99 in pence
    interval="month"
)

# Create annual price (17% discount)
starter_annual = stripe_service.create_price(
    product_id=starter_product.id,
    amount=29900,  # £299.00 in pence
    interval="year"
)
```

## Usage Examples

### Creating a Customer

```python
from Retailsights.services.stripe_payment_service import stripe_service

customer = stripe_service.create_customer(
    email="customer@example.com",
    name="John Smith",
    metadata={
        "user_id": "123",
        "shop_id": "456"
    }
)
print(f"Customer ID: {customer.id}")
```

### Creating a Subscription

```python
subscription = stripe_service.create_subscription(
    customer_id="cus_xxxxxxxxxxxxx",
    price_id="price_xxxxxxxxxxxxx",  # From Stripe Dashboard
    trial_days=30,  # 30-day free trial
    metadata={
        "user_id": "123",
        "plan": "professional"
    }
)
```

### Processing One-Time Payment

```python
payment_intent = stripe_service.create_payment_intent(
    amount=9999,  # £99.99 in pence
    customer_id="cus_xxxxxxxxxxxxx",
    description="One-time setup fee",
    metadata={"invoice_id": "INV-001"}
)

# Use payment_intent.client_secret with Stripe.js
```

### Canceling Subscription

```python
# Cancel at end of billing period (recommended)
subscription = stripe_service.cancel_subscription(
    subscription_id="sub_xxxxxxxxxxxxx",
    at_period_end=True
)

# Cancel immediately (refund handling required)
subscription = stripe_service.cancel_subscription(
    subscription_id="sub_xxxxxxxxxxxxx",
    at_period_end=False
)
```

## Webhook Configuration

### 1. Set Up Webhook Endpoint

1. Go to Stripe Dashboard → Developers → Webhooks
2. Click **Add Endpoint**
3. Enter your URL: `https://your-app.streamlit.app/webhook/stripe`
4. Select events to listen to:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `invoice.paid`
   - `invoice.payment_failed`

5. Copy the **Webhook Secret** (starts with `whsec_`)

### 2. Handle Webhooks

```python
from Retailsights.services.stripe_payment_service import stripe_service

def handle_webhook(request):
    """Handle incoming Stripe webhook."""
    payload = request.body
    sig_header = request.headers.get('Stripe-Signature')
    
    event = stripe_service.construct_webhook_event(payload, sig_header)
    
    if not event:
        return {"error": "Invalid signature"}, 400
    
    # Handle different event types
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        # Update database, send confirmation email
        
    elif event['type'] == 'customer.subscription.created':
        subscription = event['data']['object']
        # Activate user's subscription
        
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        # Send payment failure notification
    
    return {"status": "success"}, 200
```

## Security Best Practices

### 1. Never Store Card Details

❌ **NEVER** do this:
```python
card_number = st.text_input("Card Number")  # NEVER collect raw card data
```

✅ **Always** use Stripe.js:
```javascript
// Client-side with Stripe.js
const stripe = Stripe('pk_test_...');
const result = await stripe.confirmCardPayment(clientSecret, {
  payment_method: {card: cardElement}
});
```

### 2. Use Stripe Checkout (Recommended for Streamlit)

Instead of embedded forms, redirect to Stripe Checkout:

```python
import stripe

checkout_session = stripe.checkout.Session.create(
    customer=customer_id,
    line_items=[{
        'price': 'price_xxxxxxxxxxxxx',
        'quantity': 1,
    }],
    mode='subscription',
    success_url='https://your-app.streamlit.app/success',
    cancel_url='https://your-app.streamlit.app/cancel',
)

# Redirect user to checkout_session.url
```

### 3. Validate Webhook Signatures

Always verify webhooks:
```python
event = stripe_service.construct_webhook_event(payload, signature)
if not event:
    return 400  # Invalid signature
```

### 4. Use HTTPS Only

- ✅ Streamlit Cloud (automatic HTTPS)
- ✅ Custom domain with SSL certificate
- ❌ Never use HTTP in production

## Testing

### Test Mode

Use test API keys for development:
```env
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxx
```

### Test Card Numbers

```
Successful payment: 4242 4242 4242 4242
Requires authentication: 4000 0025 0000 3155
Declined: 4000 0000 0000 9995
Insufficient funds: 4000 0000 0000 9995

Expiry: Any future date
CVC: Any 3 digits
```

### Webhook Testing

Use Stripe CLI:
```bash
stripe listen --forward-to localhost:8501/webhook/stripe
stripe trigger payment_intent.succeeded
```

## Pricing Plans (UK Market)

| Plan | Monthly | Annual | Save | Features |
|------|---------|--------|------|----------|
| **Starter** | £29.99 | £299.00 | 17% | 3 shops, basic analytics |
| **Professional** | £79.99 | £799.00 | 17% | 10 shops, AI insights, priority support |
| **Enterprise** | £199.99 | £1,999.00 | 17% | Unlimited shops, dedicated support, SLA |

### Price IDs Setup

After creating products in Stripe, update your code:

```python
PRICE_IDS = {
    "starter_monthly": "price_xxxxxxxxxxxxx",
    "starter_annual": "price_xxxxxxxxxxxxx",
    "professional_monthly": "price_xxxxxxxxxxxxx",
    "professional_annual": "price_xxxxxxxxxxxxx",
    "enterprise_monthly": "price_xxxxxxxxxxxxx",
    "enterprise_annual": "price_xxxxxxxxxxxxx",
}
```

## Error Handling

### Common Errors

**Card Declined:**
```python
try:
    payment_intent = stripe_service.create_payment_intent(...)
except StripePaymentError as e:
    if "card_declined" in str(e):
        st.error("Your card was declined. Please try another payment method.")
```

**Insufficient Funds:**
```python
if "insufficient_funds" in error_message:
    st.error("Insufficient funds. Please use a different card.")
```

**Authentication Required:**
```python
if payment_intent.status == "requires_action":
    # Redirect to 3D Secure authentication
    st.info("Additional authentication required")
```

## Compliance

### GDPR (UK)
- Customer data stored securely
- Right to deletion supported
- Data retention: 30 days after cancellation

### PCI DSS
- No card data stored in database
- Stripe.js for card collection
- Webhook signature verification

### UK Tax (VAT)
- Configure tax rates in Stripe Dashboard
- Automatic VAT calculation
- VAT invoices generated

## Database Schema

### stripe_customers
```sql
id                   SERIAL PRIMARY KEY
user_id              INTEGER UNIQUE REFERENCES users(id)
stripe_customer_id   VARCHAR(255) UNIQUE
created_at           TIMESTAMP
updated_at           TIMESTAMP
```

### payment_transactions
```sql
id                          SERIAL PRIMARY KEY
user_id                     INTEGER REFERENCES users(id)
shop_id                     INTEGER REFERENCES shops(id)
stripe_payment_intent_id    VARCHAR(255) UNIQUE
amount                      INTEGER (pence)
currency                    VARCHAR(3) DEFAULT 'gbp'
status                      VARCHAR(50)
payment_type                VARCHAR(50)
description                 TEXT
created_at                  TIMESTAMP
completed_at                TIMESTAMP
```

### subscriptions
```sql
id                      SERIAL PRIMARY KEY
user_id                 INTEGER REFERENCES users(id)
stripe_subscription_id  VARCHAR(255) UNIQUE
plan_name               VARCHAR(100)
status                  VARCHAR(50)
billing_interval        VARCHAR(20)
amount                  INTEGER (pence per interval)
current_period_start    TIMESTAMP
current_period_end      TIMESTAMP
trial_end               TIMESTAMP
created_at              TIMESTAMP
updated_at              TIMESTAMP
```

## Support

### Documentation
- [Stripe Docs](https://stripe.com/docs)
- [Stripe API Reference](https://stripe.com/docs/api)
- [Stripe Testing](https://stripe.com/docs/testing)

### Stripe Dashboard
- View customers: `https://dashboard.stripe.com/customers`
- View payments: `https://dashboard.stripe.com/payments`
- View subscriptions: `https://dashboard.stripe.com/subscriptions`

### Common Issues

**"Stripe not configured"**
- Check STRIPE_SECRET_KEY is set
- Verify key starts with `sk_test_` or `sk_live_`

**"Webhook verification failed"**
- Check STRIPE_WEBHOOK_SECRET matches dashboard
- Ensure raw request body is used (not parsed JSON)

**"Payment requires authentication"**
- Implement 3D Secure (Stripe.js handles automatically)
- Redirect user to authentication URL

## Next Steps

1. ✅ Set up Stripe account
2. ✅ Add API keys to environment
3. ✅ Create products and prices
4. ✅ Run database migration
5. ✅ Configure webhooks
6. 🔄 Implement Stripe.js for card collection
7. 🔄 Test with test cards
8. 🔄 Go live with production keys

---

**Implementation Status:** ✅ Backend Complete | ⚠️ Frontend PCI Compliance Required

**Last Updated:** December 15, 2025
