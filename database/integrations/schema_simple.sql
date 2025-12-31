-- Phase 3: Advanced Integrations Database Schema (Simple Version)
-- Core Integration Tables

-- Webhook Subscriptions
CREATE TABLE IF NOT EXISTS webhook_subscriptions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    endpoint_url TEXT NOT NULL,
    secret_key TEXT NOT NULL,
    event_types TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    retry_config TEXT,
    headers TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_delivery_at DATETIME,
    total_deliveries INTEGER DEFAULT 0,
    successful_deliveries INTEGER DEFAULT 0,
    failed_deliveries INTEGER DEFAULT 0
);

-- Webhook Events
CREATE TABLE IF NOT EXISTS webhook_events (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    event_data TEXT NOT NULL,
    user_id TEXT,
    source_ip TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE
);

-- Webhook Deliveries
CREATE TABLE IF NOT EXISTS webhook_deliveries (
    id TEXT PRIMARY KEY,
    subscription_id TEXT NOT NULL,
    event_id TEXT NOT NULL,
    attempt_number INTEGER NOT NULL,
    status TEXT NOT NULL,
    response_code INTEGER,
    response_body TEXT,
    response_headers TEXT,
    error_message TEXT,
    delivered_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- API Keys and Authentication
CREATE TABLE IF NOT EXISTS api_keys (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    key_name TEXT NOT NULL,
    api_key TEXT NOT NULL UNIQUE,
    api_secret TEXT NOT NULL,
    tier TEXT NOT NULL DEFAULT 'free',
    rate_limit_per_minute INTEGER DEFAULT 60,
    rate_limit_per_day INTEGER DEFAULT 1000,
    permissions TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    usage_count INTEGER DEFAULT 0,
    daily_usage_count INTEGER DEFAULT 0,
    daily_usage_reset_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- API Usage Tracking
CREATE TABLE IF NOT EXISTS api_usage_logs (
    id TEXT PRIMARY KEY,
    api_key_id TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    request_ip TEXT,
    user_agent TEXT,
    request_size INTEGER DEFAULT 0,
    response_size INTEGER DEFAULT 0,
    response_time_ms INTEGER,
    status_code INTEGER,
    error_message TEXT,
    request_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Third-party API Configurations
CREATE TABLE IF NOT EXISTS external_apis (
    id TEXT PRIMARY KEY,
    provider_name TEXT NOT NULL,
    api_name TEXT NOT NULL,
    base_url TEXT NOT NULL,
    rate_limit_per_minute INTEGER DEFAULT 100,
    timeout_seconds INTEGER DEFAULT 30,
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at DATETIME,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    avg_response_time_ms INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Payment Plans
CREATE TABLE IF NOT EXISTS payment_plans (
    id TEXT PRIMARY KEY,
    plan_name TEXT NOT NULL,
    plan_type TEXT NOT NULL,
    price_cents INTEGER NOT NULL,
    currency TEXT DEFAULT 'USD',
    billing_interval TEXT,
    features TEXT,
    rate_limits TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- User Subscriptions
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    plan_id TEXT NOT NULL,
    payment_provider TEXT NOT NULL,
    subscription_id TEXT,
    status TEXT NOT NULL,
    current_period_start DATETIME,
    current_period_end DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Payment Transactions
CREATE TABLE IF NOT EXISTS payment_transactions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    subscription_id TEXT,
    payment_provider TEXT NOT NULL,
    provider_transaction_id TEXT,
    amount_cents INTEGER NOT NULL,
    currency TEXT DEFAULT 'USD',
    status TEXT NOT NULL,
    payment_method TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME
);

-- Enhanced BIN Data Cache
CREATE TABLE IF NOT EXISTS enhanced_bin_data (
    bin_number TEXT PRIMARY KEY,
    issuer_name TEXT,
    issuer_website TEXT,
    issuer_phone TEXT,
    card_brand TEXT,
    card_type TEXT,
    card_category TEXT,
    country_code TEXT,
    country_name TEXT,
    bank_name TEXT,
    bank_website TEXT,
    bank_phone TEXT,
    supported_currencies TEXT,
    card_features TEXT,
    fraud_score INTEGER DEFAULT 0,
    is_commercial BOOLEAN DEFAULT FALSE,
    is_prepaid BOOLEAN DEFAULT FALSE,
    data_source TEXT,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    cache_expires_at DATETIME
);

-- Insert Default Payment Plans
INSERT OR REPLACE INTO payment_plans (id, plan_name, plan_type, price_cents, currency, billing_interval, features, rate_limits) VALUES
('free', 'Free Plan', 'subscription', 0, 'USD', 'monthly', 
 '["Basic BIN lookup", "100 requests/day", "Community support"]',
 '{"requests_per_minute": 10, "requests_per_day": 100}'),
 
('pro', 'Pro Plan', 'subscription', 2999, 'USD', 'monthly',
 '["Enhanced BIN data", "10,000 requests/day", "Webhook support", "Priority support", "Card generation"]',
 '{"requests_per_minute": 100, "requests_per_day": 10000}'),
 
('enterprise', 'Enterprise Plan', 'subscription', 9999, 'USD', 'monthly',
 '["Unlimited requests", "Custom integrations", "SLA guarantee", "Dedicated support", "White-label options"]',
 '{"requests_per_minute": 1000, "requests_per_day": -1}');

-- Insert Default External APIs
INSERT OR REPLACE INTO external_apis (id, provider_name, api_name, base_url, rate_limit_per_minute) VALUES
('binlist', 'BinList.net', 'BIN Lookup API', 'https://lookup.binlist.net', 60),
('stripe', 'Stripe', 'Payment API', 'https://api.stripe.com/v1', 100),
('paypal', 'PayPal', 'Payment API', 'https://api-m.paypal.com/v1', 50);