CREATE DATABASE bin_database;
\c bin_database
CREATE TABLE bins (
    bin VARCHAR(8),
    brand VARCHAR(50),
    type VARCHAR(50),
    category VARCHAR(50),
    issuer VARCHAR(100),
    country VARCHAR(50),
    bank_phone VARCHAR(50),
    bank_url VARCHAR(100)
);
CREATE INDEX idx_bin ON bins(bin);
