-- Security Tables Schema
-- Enterprise security features for BIN Search Pro

-- Rate limiting table
CREATE TABLE IF NOT EXISTS rate_limits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL,                    -- Rate limit key (ip:endpoint, user:endpoint, etc.)
    timestamp INTEGER NOT NULL,           -- Request timestamp in milliseconds
    created_at TEXT DEFAULT (datetime('now'))
);

-- Security logs table
CREATE TABLE IF NOT EXISTS security_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,             -- Event type: 'login_attempt', 'rate_limit_exceeded', etc.
    severity TEXT NOT NULL,               -- Severity: 'info', 'warning', 'error', 'critical'
    details TEXT,                         -- JSON details about the event
    ip_address TEXT,                      -- Client IP address
    user_agent TEXT,                      -- User agent string
    user_id TEXT,                         -- User ID if applicable
    endpoint TEXT,                        -- Affected endpoint
    resolved INTEGER DEFAULT 0,          -- 1 if resolved, 0 if active
    created_at TEXT DEFAULT (datetime('now'))
);

-- IP blocklist table
CREATE TABLE IF NOT EXISTS ip_blocklist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT UNIQUE NOT NULL,      -- Blocked IP address
    reason TEXT NOT NULL,                 -- Reason for blocking
    expires_at TEXT,                      -- Expiration time (NULL for permanent)
    is_active INTEGER DEFAULT 1,         -- 1 if active, 0 if disabled
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- API keys table for programmatic access
CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_hash TEXT UNIQUE NOT NULL,        -- SHA-256 hash of the API key
    user_id TEXT NOT NULL,                -- Owner user ID
    name TEXT NOT NULL,                   -- Human-readable name for the key
    permissions TEXT DEFAULT '[]',        -- JSON array of permissions
    rate_limit INTEGER DEFAULT 1000,     -- Requests per hour
    last_used_at TEXT,                    -- Last usage timestamp
    expires_at TEXT,                      -- Expiration time (NULL for no expiration)
    is_active INTEGER DEFAULT 1,         -- 1 if active, 0 if disabled
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Failed authentication attempts
CREATE TABLE IF NOT EXISTS failed_auth_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT NOT NULL,             -- Client IP
    email TEXT,                          -- Attempted email (if provided)
    user_agent TEXT,                     -- User agent
    attempt_type TEXT NOT NULL,          -- 'login', 'api_key', 'password_reset'
    failure_reason TEXT NOT NULL,        -- Reason for failure
    created_at TEXT DEFAULT (datetime('now'))
);

-- Security configuration table
CREATE TABLE IF NOT EXISTS security_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT UNIQUE NOT NULL,      -- Configuration key
    config_value TEXT NOT NULL,           -- Configuration value (JSON)
    description TEXT,                     -- Human-readable description
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Session management table
CREATE TABLE IF NOT EXISTS user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,      -- Session identifier
    user_id TEXT NOT NULL,                -- User ID
    ip_address TEXT NOT NULL,             -- Client IP
    user_agent TEXT,                      -- User agent
    expires_at TEXT NOT NULL,             -- Session expiration
    is_active INTEGER DEFAULT 1,         -- 1 if active, 0 if expired/logged out
    created_at TEXT DEFAULT (datetime('now')),
    last_activity TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Suspicious activity tracking
CREATE TABLE IF NOT EXISTS suspicious_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT NOT NULL,             -- Client IP
    user_id TEXT,                         -- User ID if authenticated
    activity_type TEXT NOT NULL,          -- Type of suspicious activity
    severity_score INTEGER NOT NULL,     -- Severity score (1-10)
    details TEXT,                        -- JSON details
    auto_blocked INTEGER DEFAULT 0,      -- 1 if automatically blocked
    reviewed INTEGER DEFAULT 0,          -- 1 if reviewed by admin
    created_at TEXT DEFAULT (datetime('now'))
);

-- GDPR compliance - data processing logs
CREATE TABLE IF NOT EXISTS data_processing_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,                        -- Affected user ID
    processing_type TEXT NOT NULL,       -- Type: 'collection', 'processing', 'sharing', 'deletion'
    data_types TEXT NOT NULL,            -- JSON array of data types processed
    legal_basis TEXT NOT NULL,           -- Legal basis for processing
    purpose TEXT NOT NULL,               -- Purpose of processing
    retention_period TEXT,               -- Data retention period
    processor_id TEXT,                   -- ID of the processor (system/admin)
    created_at TEXT DEFAULT (datetime('now'))
);

-- Indexes for security tables
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

-- Insert default security configuration
INSERT OR REPLACE INTO security_config (config_key, config_value, description) VALUES
('rate_limits', '{"global": {"limit": 1000, "window": 3600}, "api": {"limit": 10000, "window": 3600}, "auth": {"limit": 5, "window": 900}}', 'Rate limiting configuration'),
('password_policy', '{"min_length": 8, "require_uppercase": true, "require_lowercase": true, "require_numbers": true, "require_special": false, "max_age_days": 90}', 'Password policy requirements'),
('session_config', '{"timeout_minutes": 480, "extend_on_activity": true, "max_concurrent": 5}', 'Session management configuration'),
('ip_blocking', '{"auto_block_threshold": 100, "auto_block_duration": 3600, "permanent_block_threshold": 1000}', 'IP blocking thresholds'),
('api_security', '{"require_https": true, "allowed_origins": ["https://main.bin-search-pro.pages.dev"], "max_request_size": 1048576}', 'API security settings'),
('monitoring', '{"alert_thresholds": {"error_rate": 0.05, "response_time": 2000, "failed_auth": 10}, "retention_days": 90}', 'Security monitoring thresholds');

-- Cleanup old rate limit entries (run periodically)
-- DELETE FROM rate_limits WHERE timestamp < (strftime('%s', 'now') - 86400) * 1000;

-- Cleanup old security logs (run periodically) 
-- DELETE FROM security_logs WHERE created_at < datetime('now', '-90 days');

-- Cleanup expired sessions
-- DELETE FROM user_sessions WHERE expires_at < datetime('now') OR is_active = 0;

-- Cleanup expired IP blocks
-- UPDATE ip_blocklist SET is_active = 0 WHERE expires_at IS NOT NULL AND expires_at < datetime('now');