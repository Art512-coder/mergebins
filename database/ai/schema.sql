-- Phase 4: AI-Powered Automation Database Schema
-- Machine Learning and AI Features

-- AI Models Registry
CREATE TABLE IF NOT EXISTS ai_models (
    id TEXT PRIMARY KEY,
    model_name TEXT NOT NULL,
    model_type TEXT NOT NULL, -- fraud_detection, bin_prediction, optimization
    model_version TEXT NOT NULL,
    model_status TEXT NOT NULL DEFAULT 'training', -- training, active, deprecated
    accuracy_score REAL DEFAULT 0.0,
    precision_score REAL DEFAULT 0.0,
    recall_score REAL DEFAULT 0.0,
    f1_score REAL DEFAULT 0.0,
    training_data_size INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    deployed_at DATETIME,
    last_retrained_at DATETIME,
    model_config TEXT, -- JSON configuration
    performance_metrics TEXT -- JSON metrics
);

-- Fraud Detection Features
CREATE TABLE IF NOT EXISTS fraud_patterns (
    id TEXT PRIMARY KEY,
    pattern_type TEXT NOT NULL, -- velocity, geographic, behavioral, technical
    pattern_name TEXT NOT NULL,
    pattern_rules TEXT NOT NULL, -- JSON rules and conditions
    risk_score INTEGER NOT NULL, -- 1-100
    detection_count INTEGER DEFAULT 0,
    true_positive_count INTEGER DEFAULT 0,
    false_positive_count INTEGER DEFAULT 0,
    accuracy_rate REAL DEFAULT 0.0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Fraud Detection Results
CREATE TABLE IF NOT EXISTS fraud_detections (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    user_id TEXT,
    bin_number TEXT,
    detection_type TEXT NOT NULL,
    risk_score INTEGER NOT NULL, -- 0-100
    confidence_score REAL NOT NULL, -- 0.0-1.0
    patterns_matched TEXT, -- JSON array of matched pattern IDs
    features_analyzed TEXT, -- JSON object of analyzed features
    is_flagged BOOLEAN DEFAULT FALSE,
    is_reviewed BOOLEAN DEFAULT FALSE,
    reviewer_decision TEXT, -- approved, rejected, pending
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    reviewed_at DATETIME
);

-- Predictive Analytics Features
CREATE TABLE IF NOT EXISTS bin_predictions (
    id TEXT PRIMARY KEY,
    bin_number TEXT NOT NULL,
    prediction_type TEXT NOT NULL, -- issuer, card_type, country, validity
    predicted_value TEXT NOT NULL,
    confidence_score REAL NOT NULL, -- 0.0-1.0
    actual_value TEXT,
    is_correct BOOLEAN,
    model_used TEXT,
    features_used TEXT, -- JSON array of feature names
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    validated_at DATETIME
);

-- Machine Learning Training Data
CREATE TABLE IF NOT EXISTS ml_training_data (
    id TEXT PRIMARY KEY,
    data_type TEXT NOT NULL, -- fraud, bin_prediction, user_behavior
    features TEXT NOT NULL, -- JSON object with feature vector
    labels TEXT NOT NULL, -- JSON object with target labels
    data_source TEXT NOT NULL, -- user_session, api_request, manual
    is_validated BOOLEAN DEFAULT FALSE,
    used_for_training BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Performance Optimization Metrics
CREATE TABLE IF NOT EXISTS optimization_metrics (
    id TEXT PRIMARY KEY,
    metric_type TEXT NOT NULL, -- database, cache, api, network
    metric_name TEXT NOT NULL,
    current_value REAL NOT NULL,
    target_value REAL,
    threshold_min REAL,
    threshold_max REAL,
    optimization_applied TEXT, -- JSON description of optimization
    improvement_percentage REAL DEFAULT 0.0,
    measured_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- AI-Powered Insights and Recommendations
CREATE TABLE IF NOT EXISTS ai_insights (
    id TEXT PRIMARY KEY,
    insight_type TEXT NOT NULL, -- business, technical, security, performance
    insight_category TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    confidence_score REAL NOT NULL, -- 0.0-1.0
    impact_score INTEGER NOT NULL, -- 1-10
    data_points TEXT, -- JSON array of supporting data
    recommendations TEXT, -- JSON array of recommended actions
    status TEXT DEFAULT 'new', -- new, reviewed, implemented, dismissed
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    reviewed_at DATETIME,
    implemented_at DATETIME
);

-- Automated System Actions Log
CREATE TABLE IF NOT EXISTS automation_logs (
    id TEXT PRIMARY KEY,
    action_type TEXT NOT NULL, -- optimization, scaling, security, maintenance
    action_name TEXT NOT NULL,
    trigger_condition TEXT NOT NULL,
    action_taken TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    metrics_before TEXT, -- JSON snapshot before action
    metrics_after TEXT, -- JSON snapshot after action
    execution_time_ms INTEGER,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- User Behavior Analytics for AI
CREATE TABLE IF NOT EXISTS user_behavior_patterns (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    session_id TEXT NOT NULL,
    behavior_type TEXT NOT NULL, -- navigation, api_usage, search_pattern
    pattern_data TEXT NOT NULL, -- JSON behavior data
    anomaly_score REAL DEFAULT 0.0, -- 0.0-1.0 (higher = more anomalous)
    cluster_id TEXT, -- ML clustering assignment
    is_suspicious BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Real-time Feature Store
CREATE TABLE IF NOT EXISTS feature_store (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL, -- user, session, bin, transaction
    entity_id TEXT NOT NULL,
    feature_name TEXT NOT NULL,
    feature_value REAL NOT NULL,
    feature_metadata TEXT, -- JSON metadata
    computed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    UNIQUE(entity_type, entity_id, feature_name)
);

-- AI Model Performance Tracking
CREATE TABLE IF NOT EXISTS model_performance_logs (
    id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL,
    prediction_id TEXT,
    input_features TEXT NOT NULL, -- JSON
    predicted_output TEXT NOT NULL, -- JSON
    actual_output TEXT, -- JSON (when available)
    prediction_time_ms INTEGER,
    confidence_score REAL,
    is_correct BOOLEAN,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES ai_models(id)
);

-- Indexes for AI/ML Performance
CREATE INDEX IF NOT EXISTS idx_fraud_patterns_type_active ON fraud_patterns(pattern_type, is_active);
CREATE INDEX IF NOT EXISTS idx_fraud_detections_session ON fraud_detections(session_id);
CREATE INDEX IF NOT EXISTS idx_fraud_detections_risk_score ON fraud_detections(risk_score DESC);
CREATE INDEX IF NOT EXISTS idx_fraud_detections_created ON fraud_detections(created_at);

CREATE INDEX IF NOT EXISTS idx_bin_predictions_bin ON bin_predictions(bin_number);
CREATE INDEX IF NOT EXISTS idx_bin_predictions_type ON bin_predictions(prediction_type);
CREATE INDEX IF NOT EXISTS idx_bin_predictions_confidence ON bin_predictions(confidence_score DESC);

CREATE INDEX IF NOT EXISTS idx_ml_training_data_type ON ml_training_data(data_type);
CREATE INDEX IF NOT EXISTS idx_ml_training_data_validated ON ml_training_data(is_validated);

CREATE INDEX IF NOT EXISTS idx_optimization_metrics_type_name ON optimization_metrics(metric_type, metric_name);
CREATE INDEX IF NOT EXISTS idx_optimization_metrics_measured ON optimization_metrics(measured_at);

CREATE INDEX IF NOT EXISTS idx_ai_insights_type_status ON ai_insights(insight_type, status);
CREATE INDEX IF NOT EXISTS idx_ai_insights_impact ON ai_insights(impact_score DESC);

CREATE INDEX IF NOT EXISTS idx_automation_logs_type_created ON automation_logs(action_type, created_at);
CREATE INDEX IF NOT EXISTS idx_automation_logs_success ON automation_logs(success);

CREATE INDEX IF NOT EXISTS idx_behavior_patterns_user ON user_behavior_patterns(user_id);
CREATE INDEX IF NOT EXISTS idx_behavior_patterns_session ON user_behavior_patterns(session_id);
CREATE INDEX IF NOT EXISTS idx_behavior_patterns_anomaly ON user_behavior_patterns(anomaly_score DESC);

CREATE INDEX IF NOT EXISTS idx_feature_store_entity ON feature_store(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_feature_store_expires ON feature_store(expires_at);

CREATE INDEX IF NOT EXISTS idx_model_performance_model ON model_performance_logs(model_id);
CREATE INDEX IF NOT EXISTS idx_model_performance_created ON model_performance_logs(created_at);

-- Insert Initial AI Models
INSERT OR REPLACE INTO ai_models (id, model_name, model_type, model_version, model_status, model_config) VALUES
('fraud_v1', 'Fraud Detection Engine v1.0', 'fraud_detection', '1.0.0', 'active', 
 '{"algorithm": "ensemble", "features": ["velocity", "geographic", "behavioral"], "threshold": 0.7}'),
 
('bin_predictor_v1', 'BIN Prediction Model v1.0', 'bin_prediction', '1.0.0', 'active',
 '{"algorithm": "random_forest", "features": ["bin_pattern", "historical_data", "issuer_patterns"], "confidence_threshold": 0.8}'),
 
('optimizer_v1', 'Performance Optimizer v1.0', 'optimization', '1.0.0', 'active',
 '{"algorithm": "reinforcement_learning", "metrics": ["response_time", "throughput", "error_rate"], "optimization_interval": 3600}');

-- Insert Initial Fraud Patterns
INSERT OR REPLACE INTO fraud_patterns (id, pattern_type, pattern_name, pattern_rules, risk_score) VALUES
('vel_001', 'velocity', 'High Frequency BIN Lookups', 
 '{"condition": "lookups_per_minute > 100", "window": 60, "threshold": 100}', 85),
 
('geo_001', 'geographic', 'Suspicious Geographic Pattern', 
 '{"condition": "country_changes > 3", "window": 3600, "threshold": 3}', 75),
 
('beh_001', 'behavioral', 'Automated Bot Behavior', 
 '{"condition": "consistent_timing < 100ms", "requests": 10, "threshold": 0.9}', 90),
 
('tech_001', 'technical', 'Known Test BIN Pattern', 
 '{"condition": "bin_matches_test_patterns", "patterns": ["4111", "4000", "5555"]}', 95);

-- Insert Initial Optimization Metrics
INSERT OR REPLACE INTO optimization_metrics (id, metric_type, metric_name, current_value, target_value, threshold_min, threshold_max) VALUES
('db_001', 'database', 'Average Query Time (ms)', 50.0, 25.0, 10.0, 100.0),
('cache_001', 'cache', 'Cache Hit Rate (%)', 85.0, 95.0, 80.0, 99.0),
('api_001', 'api', 'Average Response Time (ms)', 120.0, 80.0, 50.0, 200.0),
('net_001', 'network', 'Throughput (req/sec)', 500.0, 1000.0, 100.0, 2000.0);