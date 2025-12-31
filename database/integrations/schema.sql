-- Phase 3: Advanced Integrations Database Schema
-- Webhook System Tables

-- Webhook Subscriptions
CREATE TABLE IF NOT EXISTS webhook_subscriptions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    endpoint_url TEXT NOT NULL,
    secret_key TEXT NOT NULL,
    event_types TEXT NOT NULL, -- JSON array of subscribed events
    is_active BOOLEAN DEFAULT TRUE,
    retry_config TEXT, -- JSON: max_retries, retry_intervals
    headers TEXT, -- JSON: custom headers
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_delivery_at DATETIME,
    total_deliveries INTEGER DEFAULT 0,
    successful_deliveries INTEGER DEFAULT 0,
    failed_deliveries INTEGER DEFAULT 0
);

-- Webhook Events (for tracking all events)
CREATE TABLE IF NOT EXISTS webhook_events (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL, -- bin.lookup, card.generated, payment.completed, etc.
    event_data TEXT NOT NULL, -- JSON payload
    user_id TEXT,
    source_ip TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE
);

-- Webhook Deliveries (tracking delivery attempts)
CREATE TABLE IF NOT EXISTS webhook_deliveries (
    id TEXT PRIMARY KEY,
    subscription_id TEXT NOT NULL,
    event_id TEXT NOT NULL,
    attempt_number INTEGER NOT NULL,
    status TEXT NOT NULL, -- pending, sent, failed, success
    response_code INTEGER,
    response_body TEXT,
    response_headers TEXT, -- JSON
    error_message TEXT,
    delivered_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subscription_id) REFERENCES webhook_subscriptions(id),
    FOREIGN KEY (event_id) REFERENCES webhook_events(id)
);

-- API Keys and Authentication
CREATE TABLE IF NOT EXISTS api_keys (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    key_name TEXT NOT NULL,
    api_key TEXT NOT NULL UNIQUE,
    api_secret TEXT NOT NULL,
    tier TEXT NOT NULL DEFAULT 'free', -- free, pro, enterprise
    rate_limit_per_minute INTEGER DEFAULT 60,
    rate_limit_per_day INTEGER DEFAULT 1000,
    permissions TEXT, -- JSON array of allowed endpoints
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
    request_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (api_key_id) REFERENCES api_keys(id)
);

-- Third-party API Configurations
CREATE TABLE IF NOT EXISTS external_apis (
    id TEXT PRIMARY KEY,
    provider_name TEXT NOT NULL, -- binlist.net, stripe, paypal, etc.
    api_name TEXT NOT NULL,
    base_url TEXT NOT NULL,
    api_key TEXT,
    secret_key TEXT,
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

-- Payment Integration Tables
CREATE TABLE IF NOT EXISTS payment_plans (
    id TEXT PRIMARY KEY,
    plan_name TEXT NOT NULL,
    plan_type TEXT NOT NULL, -- subscription, one-time
    price_cents INTEGER NOT NULL,
    currency TEXT DEFAULT 'USD',
    billing_interval TEXT, -- monthly, yearly, null for one-time
    features TEXT, -- JSON array of included features
    rate_limits TEXT, -- JSON: requests per minute/day
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_subscriptions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    plan_id TEXT NOT NULL,
    payment_provider TEXT NOT NULL, -- stripe, paypal, crypto
    subscription_id TEXT, -- Provider's subscription ID
    status TEXT NOT NULL, -- active, cancelled, expired, pending
    current_period_start DATETIME,
    current_period_end DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plan_id) REFERENCES payment_plans(id)
);

CREATE TABLE IF NOT EXISTS payment_transactions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    subscription_id TEXT,
    payment_provider TEXT NOT NULL,
    provider_transaction_id TEXT,
    amount_cents INTEGER NOT NULL,
    currency TEXT DEFAULT 'USD',
    status TEXT NOT NULL, -- pending, completed, failed, refunded
    payment_method TEXT, -- card, paypal, crypto
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    FOREIGN KEY (subscription_id) REFERENCES user_subscriptions(id)
);

-- Enhanced BIN Data Cache
CREATE TABLE IF NOT EXISTS enhanced_bin_data (
    bin_number TEXT PRIMARY KEY,
    issuer_name TEXT,
    issuer_website TEXT,
    issuer_phone TEXT,
    card_brand TEXT, -- visa, mastercard, amex, etc.
    card_type TEXT, -- debit, credit, prepaid
    card_category TEXT, -- classic, gold, platinum, business
    country_code TEXT,
    country_name TEXT,
    bank_name TEXT,
    bank_website TEXT,
    bank_phone TEXT,
    supported_currencies TEXT, -- JSON array
    card_features TEXT, -- JSON: contactless, chip, magnetic_stripe
    fraud_score INTEGER DEFAULT 0, -- 0-100 risk score
    is_commercial BOOLEAN DEFAULT FALSE,
    is_prepaid BOOLEAN DEFAULT FALSE,
    data_source TEXT, -- binlist, custom, manual
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    cache_expires_at DATETIME
);

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_webhook_subscriptions_user_id ON webhook_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_webhook_subscriptions_active ON webhook_subscriptions(is_active);
CREATE INDEX IF NOT EXISTS idx_webhook_events_type_created ON webhook_events(event_type, created_at);
CREATE INDEX IF NOT EXISTS idx_webhook_events_processed ON webhook_events(processed);
CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_subscription ON webhook_deliveries(subscription_id);
CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_event ON webhook_deliveries(event_id);
CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_status ON webhook_deliveries(status);

CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key ON api_keys(api_key);
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(is_active);
CREATE INDEX IF NOT EXISTS idx_api_usage_logs_key_timestamp ON api_usage_logs(api_key_id, request_timestamp);

CREATE INDEX IF NOT EXISTS idx_external_apis_provider ON external_apis(provider_name);
CREATE INDEX IF NOT EXISTS idx_external_apis_active ON external_apis(is_active);

CREATE INDEX IF NOT EXISTS idx_payment_plans_active ON payment_plans(is_active);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user ON user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_status ON user_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_user ON payment_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_status ON payment_transactions(status);

CREATE INDEX IF NOT EXISTS idx_enhanced_bin_data_source ON enhanced_bin_data(data_source);
CREATE INDEX IF NOT EXISTS idx_enhanced_bin_data_expires ON enhanced_bin_data(cache_expires_at);

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