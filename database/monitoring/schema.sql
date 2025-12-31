-- Monitoring Tables Schema
-- APM and Performance Monitoring for BIN Search Pro

-- Transactions table for storing request performance data
CREATE TABLE IF NOT EXISTS monitoring_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,                    -- Endpoint name (e.g., 'bin_lookup', 'generate_cards')
    start_time INTEGER NOT NULL,           -- Timestamp in milliseconds
    end_time INTEGER NOT NULL,             -- Timestamp in milliseconds
    duration REAL NOT NULL,                -- Duration in milliseconds
    status INTEGER NOT NULL,               -- HTTP status code
    success INTEGER NOT NULL,              -- 1 for success, 0 for failure
    method TEXT NOT NULL,                  -- HTTP method
    url TEXT NOT NULL,                     -- Request URL
    user_agent TEXT,                       -- User agent string
    ip TEXT,                              -- Client IP address
    country TEXT,                         -- Country from Cloudflare
    error_count INTEGER DEFAULT 0,        -- Number of errors in transaction
    db_query_count INTEGER DEFAULT 0,     -- Number of database queries
    api_call_count INTEGER DEFAULT 0,     -- Number of external API calls
    metadata TEXT,                        -- JSON metadata (spans, errors, custom metrics)
    created_at TEXT DEFAULT (datetime('now'))
);

-- Spans table for detailed operation tracking within transactions
CREATE TABLE IF NOT EXISTS monitoring_spans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    span_id TEXT UNIQUE NOT NULL,
    transaction_id TEXT NOT NULL,
    name TEXT NOT NULL,                   -- Operation name (e.g., 'db.select', 'api.payment')
    type TEXT NOT NULL,                   -- Type: 'database', 'http', 'custom'
    start_time INTEGER NOT NULL,          -- Timestamp in milliseconds
    end_time INTEGER NOT NULL,            -- Timestamp in milliseconds
    duration REAL NOT NULL,               -- Duration in milliseconds
    success INTEGER NOT NULL,             -- 1 for success, 0 for failure
    error_message TEXT,                   -- Error message if failed
    metadata TEXT,                        -- JSON metadata specific to span
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (transaction_id) REFERENCES monitoring_transactions(transaction_id)
);

-- Aggregate metrics table for hourly performance summaries
CREATE TABLE IF NOT EXISTS monitoring_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_hour TEXT NOT NULL,            -- Hour in ISO format (YYYY-MM-DD HH:00:00)
    endpoint TEXT NOT NULL,               -- Endpoint name
    total_requests INTEGER DEFAULT 0,    -- Total number of requests
    successful_requests INTEGER DEFAULT 0, -- Number of successful requests
    failed_requests INTEGER DEFAULT 0,   -- Number of failed requests
    avg_response_time REAL DEFAULT 0,    -- Average response time in ms
    p95_response_time REAL DEFAULT 0,    -- 95th percentile response time
    error_rate REAL DEFAULT 0,           -- Error rate (0.0 to 1.0)
    throughput REAL DEFAULT 0,           -- Requests per second
    avg_db_time REAL DEFAULT 0,          -- Average database time per request
    total_db_queries INTEGER DEFAULT 0,  -- Total database queries
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(metric_hour, endpoint)
);

-- Alerts table for storing performance and error alerts
CREATE TABLE IF NOT EXISTS monitoring_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,                   -- Alert type: 'high_response_time', 'error', 'high_database_time'
    severity TEXT NOT NULL,               -- Severity: 'info', 'warning', 'error', 'critical'
    message TEXT NOT NULL,                -- Human-readable alert message
    transaction_id TEXT,                  -- Related transaction ID
    resolved INTEGER DEFAULT 0,          -- 1 if resolved, 0 if active
    resolved_at TEXT,                     -- When alert was resolved
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (transaction_id) REFERENCES monitoring_transactions(transaction_id)
);

-- System health table for storing health check results
CREATE TABLE IF NOT EXISTS monitoring_health (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status TEXT NOT NULL,                 -- Overall system status: 'healthy', 'degraded', 'unhealthy'
    uptime INTEGER NOT NULL,              -- System uptime in milliseconds
    database_status TEXT NOT NULL,       -- Database health: 'healthy', 'slow', 'unhealthy'
    database_latency REAL NOT NULL,      -- Database response time in ms
    memory_usage REAL,                   -- Memory usage if available
    cpu_usage REAL,                      -- CPU usage if available
    error_rate REAL DEFAULT 0,           -- Current error rate
    response_time REAL DEFAULT 0,        -- Current average response time
    created_at TEXT DEFAULT (datetime('now'))
);

-- Performance baselines table for storing expected performance metrics
CREATE TABLE IF NOT EXISTS monitoring_baselines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    endpoint TEXT NOT NULL,
    metric_type TEXT NOT NULL,            -- 'response_time', 'error_rate', 'throughput'
    baseline_value REAL NOT NULL,        -- Expected baseline value
    warning_threshold REAL NOT NULL,     -- Warning threshold
    critical_threshold REAL NOT NULL,    -- Critical threshold
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(endpoint, metric_type)
);

-- User activity tracking for detailed analytics
CREATE TABLE IF NOT EXISTS monitoring_user_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,                        -- User ID if authenticated
    session_id TEXT,                     -- Session identifier
    ip_address TEXT NOT NULL,            -- Client IP
    user_agent TEXT,                     -- User agent
    country TEXT,                        -- Country from Cloudflare
    endpoint TEXT NOT NULL,              -- Accessed endpoint
    request_size INTEGER,                -- Request size in bytes
    response_size INTEGER,               -- Response size in bytes
    response_time REAL NOT NULL,         -- Response time in ms
    status_code INTEGER NOT NULL,        -- HTTP status code
    referrer TEXT,                       -- HTTP referrer
    created_at TEXT DEFAULT (datetime('now'))
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_transactions_time ON monitoring_transactions(start_time);
CREATE INDEX IF NOT EXISTS idx_transactions_name ON monitoring_transactions(name);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON monitoring_transactions(status);
CREATE INDEX IF NOT EXISTS idx_spans_transaction ON monitoring_spans(transaction_id);
CREATE INDEX IF NOT EXISTS idx_spans_type ON monitoring_spans(type);
CREATE INDEX IF NOT EXISTS idx_metrics_hour ON monitoring_metrics(metric_hour);
CREATE INDEX IF NOT EXISTS idx_metrics_endpoint ON monitoring_metrics(endpoint);
CREATE INDEX IF NOT EXISTS idx_alerts_type ON monitoring_alerts(type);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON monitoring_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON monitoring_alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_health_created ON monitoring_health(created_at);
CREATE INDEX IF NOT EXISTS idx_user_activity_time ON monitoring_user_activity(created_at);
CREATE INDEX IF NOT EXISTS idx_user_activity_endpoint ON monitoring_user_activity(endpoint);

-- Insert default baselines for key endpoints
INSERT OR REPLACE INTO monitoring_baselines (endpoint, metric_type, baseline_value, warning_threshold, critical_threshold) VALUES
('bin_lookup', 'response_time', 500, 1000, 2000),
('bin_lookup', 'error_rate', 0.01, 0.05, 0.1),
('generate_cards', 'response_time', 1000, 2000, 5000),
('generate_cards', 'error_rate', 0.01, 0.05, 0.1),
('auth_login', 'response_time', 300, 800, 1500),
('auth_login', 'error_rate', 0.02, 0.1, 0.2),
('payment_webhook', 'response_time', 200, 500, 1000),
('payment_webhook', 'error_rate', 0.01, 0.03, 0.05);