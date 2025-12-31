-- Supplemental migration: Add remaining security tables
-- Phase 1: Technical Excellence Foundation - Security Tables
-- Run date: 2024-12-28

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
    last_activity TEXT DEFAULT (datetime('now'))
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
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Create additional indexes
CREATE INDEX IF NOT EXISTS idx_failed_auth_ip ON failed_auth_attempts(ip_address);
CREATE INDEX IF NOT EXISTS idx_failed_auth_created ON failed_auth_attempts(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_id ON user_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_suspicious_ip ON suspicious_activity(ip_address);
CREATE INDEX IF NOT EXISTS idx_suspicious_created ON suspicious_activity(created_at);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);

-- Insert default security configuration
INSERT OR REPLACE INTO security_config (config_key, config_value, description) VALUES
('rate_limits', '{"global": {"limit": 1000, "window": 3600}, "api": {"limit": 10000, "window": 3600}, "auth": {"limit": 5, "window": 900}}', 'Rate limiting configuration'),
('password_policy', '{"min_length": 8, "require_uppercase": true, "require_lowercase": true, "require_numbers": true, "require_special": false, "max_age_days": 90}', 'Password policy requirements'),
('session_config', '{"timeout_minutes": 480, "extend_on_activity": true, "max_concurrent": 5}', 'Session management configuration'),
('ip_blocking', '{"auto_block_threshold": 100, "auto_block_duration": 3600, "permanent_block_threshold": 1000}', 'IP blocking thresholds'),
('api_security', '{"require_https": true, "allowed_origins": ["https://main.bin-search-pro.pages.dev"], "max_request_size": 1048576}', 'API security settings'),
('monitoring', '{"alert_thresholds": {"error_rate": 0.05, "response_time": 2000, "failed_auth": 10}, "retention_days": 90}', 'Security monitoring thresholds');