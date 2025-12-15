# Quick Start: Stripe Payment Setup for UK Client

## 🚀 5-Minute Setup Guide

### Step 1: Get Your Stripe Keys (2 minutes)

1. **Sign up at Stripe:**
   - Go to [https://dashboard.stripe.com/register](https://dashboard.stripe.com/register)
   - Select **United Kingdom** as your country
   - Complete business verification

2. **Get API Keys:**
   - Go to [Developers → API Keys](https://dashboard.stripe.com/test/apikeys)
   - Copy these two keys:
     - **Secret key** (starts with `sk_test_...`)
     - **Publishable key** (starts with `pk_test_...`)

### Step 2: Add Keys to Streamlit Cloud (1 minute)

1. Go to your Streamlit Cloud app settings
2. Click **Secrets** tab
3. Add these lines:

```toml
STRIPE_SECRET_KEY = "sk_test_paste_your_key_here"
STRIPE_PUBLISHABLE_KEY = "pk_test_paste_your_key_here"
STRIPE_CURRENCY = "gbp"
STRIPE_COUNTRY = "GB"
```

4. Click **Save**
5. Your app will automatically restart

### Step 3: Create Products in Stripe (2 minutes)

1. Go to [Products](https://dashboard.stripe.com/test/products)
2. Click **Add product**

**Create these 3 products:**

#### Product 1: Starter Plan
- **Name:** Starter Plan
- **Description:** Perfect for small retailers
- **Pricing:**
  - Add price: **£29.99** per month
  - Add price: **£299.00** per year

#### Product 2: Professional Plan ⭐
- **Name:** Professional Plan
- **Description:** For growing retail businesses
- **Pricing:**
  - Add price: **£79.99** per month
  - Add price: **£799.00** per year

#### Product 3: Enterprise Plan
- **Name:** Enterprise Plan
- **Description:** For large retail operations
- **Pricing:**
  - Add price: **£199.99** per month
  - Add price: **£1,999.00** per year

### Step 4: Test Your Integration (30 seconds)

1. Go to your app → **💳 Payments** tab
2. You should see all three plans
3. Try clicking "Subscribe Now"

**Test Card Numbers:**
- **Success:** `4242 4242 4242 4242`
- **Declined:** `4000 0000 0000 0002`
- **Expiry:** Any future date (e.g., 12/30)
- **CVC:** Any 3 digits (e.g., 123)

---

## ✅ You're Done!

Your payment system is now live in **test mode**. When you're ready to accept real payments:

### Going Live Checklist:

1. **Complete Stripe Activation:**
   - Verify your business details
   - Connect your bank account
   - Submit required documents

2. **Switch to Live Keys:**
   - Go to [API Keys](https://dashboard.stripe.com/apikeys) (remove `/test`)
   - Copy **live keys** (start with `sk_live_...` and `pk_live_...`)
   - Update Streamlit secrets with live keys

3. **Set Up Webhooks:**
   - Go to [Webhooks](https://dashboard.stripe.com/webhooks)
   - Add endpoint: `https://your-app.streamlit.app/webhook/stripe`
   - Select events: `customer.subscription.*`, `payment_intent.*`
   - Copy webhook secret and add to secrets

---

## 💰 Pricing Summary

| Plan | Monthly | Annual | Annual Savings |
|------|---------|--------|----------------|
| **Starter** | £29.99 | £299.00 | £60 (17%) |
| **Professional** | £79.99 | £799.00 | £160 (17%) |
| **Enterprise** | £199.99 | £1,999.00 | £400 (17%) |

---

## 🔒 Security Notes

- ✅ All payments processed through Stripe (PCI compliant)
- ✅ No card data stored in your database
- ✅ Automatic VAT calculation for UK customers
- ✅ 3D Secure authentication supported
- ✅ Fraud detection included

---

## 📞 Support

**Stripe Support:**
- Dashboard: [https://dashboard.stripe.com](https://dashboard.stripe.com)
- Docs: [https://stripe.com/docs](https://stripe.com/docs)
- Support: [https://support.stripe.com](https://support.stripe.com)

**Common Issues:**

**"Stripe is not configured"**
→ Check STRIPE_SECRET_KEY is added to secrets

**"Payment requires authentication"**
→ Normal for some UK cards - 3D Secure popup will show

**"Card declined"**
→ Try a different card or use test card `4242 4242 4242 4242`

---

## 📊 What Your Customers See

1. Click **💳 Payments** tab
2. See three pricing plans with features
3. Select Monthly or Annual billing
4. Click **Subscribe Now**
5. Enter payment details (securely via Stripe)
6. Receive confirmation email
7. Access premium features immediately

---

## 🎯 Next Steps

After going live:

1. **Monitor Dashboard:**
   - View customers: [Customers](https://dashboard.stripe.com/customers)
   - Track payments: [Payments](https://dashboard.stripe.com/payments)
   - Check subscriptions: [Subscriptions](https://dashboard.stripe.com/subscriptions)

2. **Set Up Notifications:**
   - Email receipts (automatic)
   - Subscription renewal reminders
   - Payment failure alerts

3. **Tax Configuration:**
   - Set up VAT rates: [Tax Settings](https://dashboard.stripe.com/settings/tax)
   - Automatic tax calculation for UK customers

---

**Setup Time:** ~5 minutes  
**Status:** ✅ Ready to accept payments  
**Support:** Fully documented in `docs/STRIPE_INTEGRATION_GUIDE.md`
