-- Create optimized BIN table for D1
CREATE TABLE bins (
    bin TEXT PRIMARY KEY,
    brand TEXT,
    type TEXT,
    category TEXT,
    issuer TEXT,
    country TEXT,
    bank_phone TEXT,
    bank_url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for fast lookups
CREATE INDEX idx_bin_prefix ON bins(substr(bin, 1, 6));
CREATE INDEX idx_brand ON bins(brand);
CREATE INDEX idx_country ON bins(country);
CREATE INDEX idx_issuer ON bins(issuer);
CREATE INDEX idx_type ON bins(type);

-- Create a view for common queries
CREATE VIEW bin_summary AS
SELECT 
    substr(bin, 1, 6) as bin_prefix,
    brand,
    type,
    country,
    COUNT(*) as count
FROM bins 
GROUP BY substr(bin, 1, 6), brand, type, country;
