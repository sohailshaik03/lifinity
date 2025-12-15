-- Migration: Add Stripe payment tables
-- Date: 2025-12-15
-- Description: Add tables for Stripe customer mapping, payment transactions, and subscriptions

-- Create stripe_customers table
CREATE TABLE IF NOT EXISTS stripe_customers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    stripe_customer_id VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_stripe_customers_user_id ON stripe_customers(user_id);
CREATE INDEX idx_stripe_customers_stripe_id ON stripe_customers(stripe_customer_id);

-- Create payment_transactions table
CREATE TABLE IF NOT EXISTS payment_transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    shop_id INTEGER REFERENCES shops(id) ON DELETE SET NULL,
    stripe_payment_intent_id VARCHAR(255) UNIQUE,
    stripe_customer_id VARCHAR(255),
    
    -- Transaction details
    amount INTEGER NOT NULL, -- Amount in pence/cents
    currency VARCHAR(3) NOT NULL DEFAULT 'gbp',
    status VARCHAR(50) NOT NULL, -- succeeded, failed, pending, canceled
    
    -- Payment type and description
    payment_type VARCHAR(50) NOT NULL, -- subscription, one_time, upgrade
    description TEXT,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_payment_transactions_user_id ON payment_transactions(user_id);
CREATE INDEX idx_payment_transactions_shop_id ON payment_transactions(shop_id);
CREATE INDEX idx_payment_transactions_status ON payment_transactions(status);
CREATE INDEX idx_payment_transactions_created_at ON payment_transactions(created_at);

-- Create subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    shop_id INTEGER REFERENCES shops(id) ON DELETE SET NULL,
    
    -- Stripe integration
    stripe_subscription_id VARCHAR(255) UNIQUE,
    stripe_customer_id VARCHAR(255),
    stripe_price_id VARCHAR(255),
    
    -- Subscription details
    plan_name VARCHAR(100) NOT NULL, -- Starter, Professional, Enterprise
    status VARCHAR(50) NOT NULL, -- active, canceled, past_due, trialing
    billing_interval VARCHAR(20) NOT NULL, -- month, year
    amount INTEGER NOT NULL, -- Monthly/annual price in pence
    
    -- Billing periods
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    trial_end TIMESTAMP,
    canceled_at TIMESTAMP,
    ended_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_shop_id ON subscriptions(shop_id);
CREATE INDEX idx_subscriptions_stripe_id ON subscriptions(stripe_subscription_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);

-- Add comments for documentation
COMMENT ON TABLE stripe_customers IS 'Maps RetailSights users to Stripe customer IDs for payment processing';
COMMENT ON TABLE payment_transactions IS 'Audit trail of all payment transactions for compliance and support';
COMMENT ON TABLE subscriptions IS 'Active and historical subscription records with Stripe integration';

COMMENT ON COLUMN payment_transactions.amount IS 'Amount in smallest currency unit (pence for GBP, cents for USD)';
COMMENT ON COLUMN subscriptions.amount IS 'Subscription price in smallest currency unit per billing interval';
