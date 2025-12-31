-- Business Intelligence & Analytics Schema
-- Phase 2: Comprehensive Business Analytics Database
-- BIN Search Pro Enterprise

-- User behavior and session tracking
CREATE TABLE IF NOT EXISTS analytics_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    user_id TEXT,                         -- NULL for anonymous users
    ip_address TEXT NOT NULL,
    user_agent TEXT,
    country TEXT,
    city TEXT,
    referrer TEXT,                        -- How they found us
    landing_page TEXT NOT NULL,           -- First page visited
    utm_source TEXT,                      -- Marketing attribution
    utm_medium TEXT,
    utm_campaign TEXT,
    utm_content TEXT,
    device_type TEXT,                     -- mobile, desktop, tablet
    browser_name TEXT,
    browser_version TEXT,
    os_name TEXT,
    os_version TEXT,
    screen_resolution TEXT,
    is_mobile INTEGER DEFAULT 0,
    is_bot INTEGER DEFAULT 0,
    session_start TEXT DEFAULT (datetime('now')),
    session_end TEXT,
    session_duration INTEGER DEFAULT 0,  -- Duration in seconds
    page_views INTEGER DEFAULT 0,
    events_count INTEGER DEFAULT 0,
    conversion_events INTEGER DEFAULT 0,
    revenue_generated REAL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Page views and navigation tracking
CREATE TABLE IF NOT EXISTS analytics_page_views (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_id TEXT,
    page_url TEXT NOT NULL,
    page_title TEXT,
    page_type TEXT,                       -- home, search, results, pricing, etc.
    referrer TEXT,
    time_on_page INTEGER DEFAULT 0,      -- Seconds spent on page
    scroll_depth REAL DEFAULT 0,         -- Percentage scrolled (0-100)
    exit_page INTEGER DEFAULT 0,         -- 1 if user left site from this page
    bounce INTEGER DEFAULT 0,            -- 1 if single page visit
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (session_id) REFERENCES analytics_sessions(session_id)
);

-- User events and interactions
CREATE TABLE IF NOT EXISTS analytics_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_id TEXT,
    event_type TEXT NOT NULL,             -- search, card_generation, login, signup, payment
    event_category TEXT NOT NULL,        -- engagement, conversion, error, etc.
    event_action TEXT NOT NULL,          -- specific action taken
    event_label TEXT,                    -- additional context
    event_value REAL,                    -- numeric value (amount, quantity, etc.)
    page_url TEXT NOT NULL,
    bin_number TEXT,                     -- For BIN-related events
    search_query TEXT,                   -- For search events
    result_count INTEGER,                -- Number of results returned
    error_message TEXT,                  -- For error events
    conversion_funnel_step TEXT,         -- Which step in conversion process
    ab_test_variant TEXT,                -- A/B test variant
    custom_properties TEXT,              -- JSON for additional data
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (session_id) REFERENCES analytics_sessions(session_id)
);

-- Business metrics and KPIs
CREATE TABLE IF NOT EXISTS analytics_business_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_date TEXT NOT NULL,           -- Date in YYYY-MM-DD format
    metric_hour TEXT,                    -- Hour in YYYY-MM-DD HH:00:00 format (for hourly)
    
    -- User metrics
    daily_active_users INTEGER DEFAULT 0,
    new_users INTEGER DEFAULT 0,
    returning_users INTEGER DEFAULT 0,
    anonymous_users INTEGER DEFAULT 0,
    
    -- Engagement metrics
    total_sessions INTEGER DEFAULT 0,
    avg_session_duration REAL DEFAULT 0,
    bounce_rate REAL DEFAULT 0,
    pages_per_session REAL DEFAULT 0,
    
    -- Feature usage metrics
    bin_lookups INTEGER DEFAULT 0,
    successful_lookups INTEGER DEFAULT 0,
    failed_lookups INTEGER DEFAULT 0,
    card_generations INTEGER DEFAULT 0,
    cards_generated_total INTEGER DEFAULT 0,
    search_queries INTEGER DEFAULT 0,
    
    -- Conversion metrics
    signups INTEGER DEFAULT 0,
    login_attempts INTEGER DEFAULT 0,
    successful_logins INTEGER DEFAULT 0,
    payment_attempts INTEGER DEFAULT 0,
    successful_payments INTEGER DEFAULT 0,
    subscription_upgrades INTEGER DEFAULT 0,
    
    -- Revenue metrics
    total_revenue REAL DEFAULT 0,
    subscription_revenue REAL DEFAULT 0,
    one_time_revenue REAL DEFAULT 0,
    refunds REAL DEFAULT 0,
    
    -- Performance metrics
    avg_response_time REAL DEFAULT 0,
    error_rate REAL DEFAULT 0,
    uptime_percentage REAL DEFAULT 100,
    
    -- Content metrics
    most_searched_bins TEXT,             -- JSON array of popular BINs
    top_countries TEXT,                  -- JSON array of top countries
    popular_features TEXT,               -- JSON array of most used features
    
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(metric_date, metric_hour)
);

-- Revenue and financial analytics
CREATE TABLE IF NOT EXISTS analytics_revenue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT UNIQUE NOT NULL,
    session_id TEXT,
    user_id TEXT NOT NULL,
    payment_method TEXT NOT NULL,        -- crypto, stripe, etc.
    currency TEXT NOT NULL,
    amount REAL NOT NULL,
    amount_usd REAL NOT NULL,           -- Converted to USD
    transaction_type TEXT NOT NULL,      -- subscription, one_time, refund
    product_type TEXT,                   -- premium_plan, api_access, etc.
    subscription_period TEXT,            -- monthly, yearly, lifetime
    discount_code TEXT,
    discount_amount REAL DEFAULT 0,
    fees REAL DEFAULT 0,                -- Payment processing fees
    net_amount REAL NOT NULL,           -- Amount after fees
    mrr_contribution REAL DEFAULT 0,    -- Monthly Recurring Revenue impact
    ltv_impact REAL DEFAULT 0,          -- Customer Lifetime Value impact
    refund_reason TEXT,
    churn_risk_score REAL,             -- Predicted churn probability (0-1)
    created_at TEXT DEFAULT (datetime('now')),
    processed_at TEXT,
    FOREIGN KEY (session_id) REFERENCES analytics_sessions(session_id)
);

-- User journey and funnel analysis
CREATE TABLE IF NOT EXISTS analytics_funnels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_id TEXT,
    funnel_name TEXT NOT NULL,          -- signup, purchase, onboarding
    step_name TEXT NOT NULL,            -- step1_landing, step2_signup, etc.
    step_order INTEGER NOT NULL,
    completed INTEGER DEFAULT 0,        -- 1 if step completed
    drop_off INTEGER DEFAULT 0,         -- 1 if user dropped off at this step
    time_spent INTEGER DEFAULT 0,       -- Seconds spent in this step
    conversion_value REAL DEFAULT 0,    -- Value if converted
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (session_id) REFERENCES analytics_sessions(session_id)
);

-- Cohort analysis for user retention
CREATE TABLE IF NOT EXISTS analytics_cohorts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cohort_month TEXT NOT NULL,         -- YYYY-MM format
    user_id TEXT NOT NULL,
    signup_date TEXT NOT NULL,
    first_purchase_date TEXT,
    last_activity_date TEXT,
    total_revenue REAL DEFAULT 0,
    total_sessions INTEGER DEFAULT 0,
    total_events INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,        -- Still active user
    churn_date TEXT,                    -- When they churned
    churn_reason TEXT,                  -- Why they churned
    retention_day_1 INTEGER DEFAULT 0,  -- Returned day 1
    retention_day_7 INTEGER DEFAULT 0,  -- Returned day 7
    retention_day_30 INTEGER DEFAULT 0, -- Returned day 30
    retention_day_90 INTEGER DEFAULT 0, -- Returned day 90
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(cohort_month, user_id)
);

-- A/B testing and experiments
CREATE TABLE IF NOT EXISTS analytics_experiments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id TEXT UNIQUE NOT NULL,
    experiment_name TEXT NOT NULL,
    description TEXT,
    hypothesis TEXT,
    start_date TEXT NOT NULL,
    end_date TEXT,
    status TEXT DEFAULT 'active',       -- active, paused, completed
    traffic_allocation REAL DEFAULT 0.5, -- Percentage of traffic (0-1)
    primary_metric TEXT NOT NULL,       -- What we're measuring
    secondary_metrics TEXT,             -- JSON array of secondary metrics
    control_variant TEXT DEFAULT 'control',
    test_variants TEXT NOT NULL,        -- JSON array of variants
    statistical_significance REAL,      -- P-value
    confidence_interval TEXT,           -- JSON with lower/upper bounds
    winner TEXT,                        -- Winning variant
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- A/B test variant assignments
CREATE TABLE IF NOT EXISTS analytics_experiment_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    user_id TEXT,
    variant TEXT NOT NULL,
    assigned_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (experiment_id) REFERENCES analytics_experiments(experiment_id),
    FOREIGN KEY (session_id) REFERENCES analytics_sessions(session_id)
);

-- Geographic analytics
CREATE TABLE IF NOT EXISTS analytics_geography (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,                 -- YYYY-MM-DD
    country_code TEXT NOT NULL,
    country_name TEXT NOT NULL,
    city TEXT,
    region TEXT,
    timezone TEXT,
    
    -- Metrics by location
    users INTEGER DEFAULT 0,
    sessions INTEGER DEFAULT 0,
    page_views INTEGER DEFAULT 0,
    bounce_rate REAL DEFAULT 0,
    avg_session_duration REAL DEFAULT 0,
    conversion_rate REAL DEFAULT 0,
    revenue REAL DEFAULT 0,
    
    -- Feature usage by location  
    bin_lookups INTEGER DEFAULT 0,
    card_generations INTEGER DEFAULT 0,
    signups INTEGER DEFAULT 0,
    
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(date, country_code, city)
);

-- Technology analytics (devices, browsers, etc.)
CREATE TABLE IF NOT EXISTS analytics_technology (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,                 -- YYYY-MM-DD
    
    -- Technology details
    device_type TEXT NOT NULL,          -- mobile, desktop, tablet
    browser_name TEXT NOT NULL,
    browser_version TEXT,
    os_name TEXT NOT NULL,
    os_version TEXT,
    screen_resolution TEXT,
    
    -- Metrics by technology
    users INTEGER DEFAULT 0,
    sessions INTEGER DEFAULT 0,
    bounce_rate REAL DEFAULT 0,
    conversion_rate REAL DEFAULT 0,
    avg_response_time REAL DEFAULT 0,
    error_rate REAL DEFAULT 0,
    
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(date, device_type, browser_name, os_name)
);

-- Real-time analytics for live dashboard
CREATE TABLE IF NOT EXISTS analytics_realtime (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    metric_type TEXT NOT NULL,          -- counter, gauge, histogram
    tags TEXT,                          -- JSON object with additional tags
    timestamp INTEGER NOT NULL,         -- Unix timestamp in milliseconds
    created_at TEXT DEFAULT (datetime('now'))
);

-- Performance indexes for analytics queries
CREATE INDEX IF NOT EXISTS idx_sessions_user_date ON analytics_sessions(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_date ON analytics_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_country ON analytics_sessions(country);
CREATE INDEX IF NOT EXISTS idx_page_views_session ON analytics_page_views(session_id);
CREATE INDEX IF NOT EXISTS idx_page_views_date ON analytics_page_views(created_at);
CREATE INDEX IF NOT EXISTS idx_events_session ON analytics_events(session_id);
CREATE INDEX IF NOT EXISTS idx_events_type_date ON analytics_events(event_type, created_at);
CREATE INDEX IF NOT EXISTS idx_events_user_date ON analytics_events(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_business_metrics_date ON analytics_business_metrics(metric_date);
CREATE INDEX IF NOT EXISTS idx_business_metrics_hour ON analytics_business_metrics(metric_hour);
CREATE INDEX IF NOT EXISTS idx_revenue_user_date ON analytics_revenue(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_revenue_date ON analytics_revenue(created_at);
CREATE INDEX IF NOT EXISTS idx_funnels_session ON analytics_funnels(session_id);
CREATE INDEX IF NOT EXISTS idx_funnels_name_step ON analytics_funnels(funnel_name, step_order);
CREATE INDEX IF NOT EXISTS idx_cohorts_month ON analytics_cohorts(cohort_month);
CREATE INDEX IF NOT EXISTS idx_geography_date_country ON analytics_geography(date, country_code);
CREATE INDEX IF NOT EXISTS idx_technology_date_device ON analytics_technology(date, device_type);
CREATE INDEX IF NOT EXISTS idx_realtime_timestamp ON analytics_realtime(timestamp);
CREATE INDEX IF NOT EXISTS idx_realtime_metric ON analytics_realtime(metric_name, timestamp);

-- Insert initial business metrics baseline
INSERT OR REPLACE INTO analytics_business_metrics (
    metric_date, 
    daily_active_users, 
    total_sessions, 
    bin_lookups, 
    uptime_percentage
) VALUES (
    date('now'), 
    0, 
    0, 
    0, 
    100.0
);