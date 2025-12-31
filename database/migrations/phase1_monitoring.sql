-- Migration: Add monitoring and security tables
-- Phase 1: Technical Excellence Foundation
-- Run date: 2024-12-28

-- Create monitoring tables
CREATE TABLE IF NOT EXISTS monitoring_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    start_time INTEGER NOT NULL,
    end_time INTEGER NOT NULL,
    duration REAL NOT NULL,
    status INTEGER NOT NULL,
    success INTEGER NOT NULL,
    method TEXT NOT NULL,
    url TEXT NOT NULL,
    user_agent TEXT,
    ip TEXT,
    country TEXT,
    error_count INTEGER DEFAULT 0,
    db_query_count INTEGER DEFAULT 0,
    api_call_count INTEGER DEFAULT 0,
    metadata TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS monitoring_spans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    span_id TEXT UNIQUE NOT NULL,
    transaction_id TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    start_time INTEGER NOT NULL,
    end_time INTEGER NOT NULL,
    duration REAL NOT NULL,
    success INTEGER NOT NULL,
    error_message TEXT,
    metadata TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (transaction_id) REFERENCES monitoring_transactions(transaction_id)
);

CREATE TABLE IF NOT EXISTS monitoring_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_hour TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    avg_response_time REAL DEFAULT 0,
    p95_response_time REAL DEFAULT 0,
    error_rate REAL DEFAULT 0,
    throughput REAL DEFAULT 0,
    avg_db_time REAL DEFAULT 0,
    total_db_queries INTEGER DEFAULT 0,
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(metric_hour, endpoint)
);

CREATE TABLE IF NOT EXISTS monitoring_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    transaction_id TEXT,
    resolved INTEGER DEFAULT 0,
    resolved_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (transaction_id) REFERENCES monitoring_transactions(transaction_id)
);

CREATE TABLE IF NOT EXISTS monitoring_health (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status TEXT NOT NULL,
    uptime INTEGER NOT NULL,
    database_status TEXT NOT NULL,
    database_latency REAL NOT NULL,
    memory_usage REAL,
    cpu_usage REAL,
    error_rate REAL DEFAULT 0,
    response_time REAL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS monitoring_baselines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    endpoint TEXT NOT NULL,
    metric_type TEXT NOT NULL,
    baseline_value REAL NOT NULL,
    warning_threshold REAL NOT NULL,
    critical_threshold REAL NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(endpoint, metric_type)
);

CREATE TABLE IF NOT EXISTS monitoring_user_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    session_id TEXT,
    ip_address TEXT NOT NULL,
    user_agent TEXT,
    country TEXT,
    endpoint TEXT NOT NULL,
    request_size INTEGER,
    response_size INTEGER,
    response_time REAL NOT NULL,
    status_code INTEGER NOT NULL,
    referrer TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Create security tables
CREATE TABLE IF NOT EXISTS rate_limits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS security_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    details TEXT,
    ip_address TEXT,
    user_agent TEXT,
    user_id TEXT,
    endpoint TEXT,
    resolved INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ip_blocklist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT UNIQUE NOT NULL,
    reason TEXT NOT NULL,
    expires_at TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_hash TEXT UNIQUE NOT NULL,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    permissions TEXT DEFAULT '[]',
    rate_limit INTEGER DEFAULT 1000,
    last_used_at TEXT,
    expires_at TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS failed_auth_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT NOT NULL,
    email TEXT,
    user_agent TEXT,
    attempt_type TEXT NOT NULL,
    failure_reason TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS security_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    description TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    user_id TEXT NOT NULL,
    ip_address TEXT NOT NULL,
    user_agent TEXT,
    expires_at TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    last_activity TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS suspicious_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT NOT NULL,
    user_id TEXT,
    activity_type TEXT NOT NULL,
    severity_score INTEGER NOT NULL,
    details TEXT,
    auto_blocked INTEGER DEFAULT 0,
    reviewed INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS data_processing_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    processing_type TEXT NOT NULL,
    data_types TEXT NOT NULL,
    legal_basis TEXT NOT NULL,
    purpose TEXT NOT NULL,
    retention_period TEXT,
    processor_id TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Create indexes for performance
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
CREATE INDEX IF NOT EXISTS idx_rate_limits_key ON rate_limits(key);
CREATE INDEX IF NOT EXISTS idx_rate_limits_timestamp ON rate_limits(timestamp);
CREATE INDEX IF NOT EXISTS idx_security_logs_type ON security_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_security_logs_severity ON security_logs(severity);
CREATE INDEX IF NOT EXISTS idx_security_logs_created ON security_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_security_logs_ip ON security_logs(ip_address);
CREATE INDEX IF NOT EXISTS idx_ip_blocklist_ip ON ip_blocklist(ip_address);
CREATE INDEX IF NOT EXISTS idx_ip_blocklist_active ON ip_blocklist(is_active);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_failed_auth_ip ON failed_auth_attempts(ip_address);
CREATE INDEX IF NOT EXISTS idx_failed_auth_created ON failed_auth_attempts(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_id ON user_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_suspicious_ip ON suspicious_activity(ip_address);
CREATE INDEX IF NOT EXISTS idx_suspicious_created ON suspicious_activity(created_at);
CREATE INDEX IF NOT EXISTS idx_data_logs_user ON data_processing_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_data_logs_type ON data_processing_logs(processing_type);

-- Optimize existing tables with additional indexes
CREATE INDEX IF NOT EXISTS idx_search_history_user_date ON search_history(user_id, search_date DESC);
CREATE INDEX IF NOT EXISTS idx_search_history_bin_date ON search_history(bin_number, search_date DESC);
CREATE INDEX IF NOT EXISTS idx_users_created_plan ON users(created_at, plan_type);
CREATE INDEX IF NOT EXISTS idx_users_email_active ON users(email, is_active);
CREATE INDEX IF NOT EXISTS idx_payments_user_status ON payments(user_id, status);
CREATE INDEX IF NOT EXISTS idx_payments_date_amount ON payments(created_at, amount);
CREATE INDEX IF NOT EXISTS idx_bins_range_bank ON bins(bin_start, bin_end, bank);
CREATE INDEX IF NOT EXISTS idx_bins_country_type ON bins(country, type);

-- Insert default baselines
INSERT OR REPLACE INTO monitoring_baselines (endpoint, metric_type, baseline_value, warning_threshold, critical_threshold) VALUES
('bin_lookup', 'response_time', 500, 1000, 2000),
('bin_lookup', 'error_rate', 0.01, 0.05, 0.1),
('generate_cards', 'response_time', 1000, 2000, 5000),
('generate_cards', 'error_rate', 0.01, 0.05, 0.1),
('auth_login', 'response_time', 300, 800, 1500),
('auth_login', 'error_rate', 0.02, 0.1, 0.2),
('payment_webhook', 'response_time', 200, 500, 1000),
('payment_webhook', 'error_rate', 0.01, 0.03, 0.05);

-- Insert default security configuration
INSERT OR REPLACE INTO security_config (config_key, config_value, description) VALUES
('rate_limits', '{"global": {"limit": 1000, "window": 3600}, "api": {"limit": 10000, "window": 3600}, "auth": {"limit": 5, "window": 900}}', 'Rate limiting configuration'),
('password_policy', '{"min_length": 8, "require_uppercase": true, "require_lowercase": true, "require_numbers": true, "require_special": false, "max_age_days": 90}', 'Password policy requirements'),
('session_config', '{"timeout_minutes": 480, "extend_on_activity": true, "max_concurrent": 5}', 'Session management configuration'),
('ip_blocking', '{"auto_block_threshold": 100, "auto_block_duration": 3600, "permanent_block_threshold": 1000}', 'IP blocking thresholds'),
('api_security', '{"require_https": true, "allowed_origins": ["https://main.bin-search-pro.pages.dev"], "max_request_size": 1048576}', 'API security settings'),
('monitoring', '{"alert_thresholds": {"error_rate": 0.05, "response_time": 2000, "failed_auth": 10}, "retention_days": 90}', 'Security monitoring thresholds');

-- Migration complete
-- Phase 1.1: APM Monitoring Infrastructure - COMPLETE