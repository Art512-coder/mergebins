-- Migration: Add monitoring and security tables only
-- Phase 1: Technical Excellence Foundation - Simplified
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
    created_at TEXT DEFAULT (datetime('now'))
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
    created_at TEXT DEFAULT (datetime('now'))
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

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_transactions_time ON monitoring_transactions(start_time);
CREATE INDEX IF NOT EXISTS idx_transactions_name ON monitoring_transactions(name);
CREATE INDEX IF NOT EXISTS idx_spans_transaction ON monitoring_spans(transaction_id);
CREATE INDEX IF NOT EXISTS idx_metrics_hour ON monitoring_metrics(metric_hour);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON monitoring_alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_health_created ON monitoring_health(created_at);
CREATE INDEX IF NOT EXISTS idx_rate_limits_key ON rate_limits(key);
CREATE INDEX IF NOT EXISTS idx_rate_limits_timestamp ON rate_limits(timestamp);
CREATE INDEX IF NOT EXISTS idx_security_logs_ip ON security_logs(ip_address);
CREATE INDEX IF NOT EXISTS idx_ip_blocklist_ip ON ip_blocklist(ip_address);

-- Insert default baselines
INSERT OR REPLACE INTO monitoring_baselines (endpoint, metric_type, baseline_value, warning_threshold, critical_threshold) VALUES
('bin_lookup', 'response_time', 500, 1000, 2000),
('bin_lookup', 'error_rate', 0.01, 0.05, 0.1),
('generate_cards', 'response_time', 1000, 2000, 5000),
('generate_cards', 'error_rate', 0.01, 0.05, 0.1),
('auth_login', 'response_time', 300, 800, 1500),
('auth_login', 'error_rate', 0.02, 0.1, 0.2);