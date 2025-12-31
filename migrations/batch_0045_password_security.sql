-- Password Security Migration
-- This migration adds columns to handle the transition from insecure to secure password hashing

-- Add columns to track password migration status
ALTER TABLE users ADD COLUMN password_migration_required INTEGER DEFAULT 1;
ALTER TABLE users ADD COLUMN password_updated_at TEXT DEFAULT '2025-01-01 00:00:00';
ALTER TABLE users ADD COLUMN password_reset_token TEXT DEFAULT NULL;

-- Create index for password reset tokens
CREATE INDEX IF NOT EXISTS idx_users_reset_token ON users(password_reset_token);

-- Mark all existing users as requiring password migration
UPDATE users SET 
  password_migration_required = 1,
  password_updated_at = datetime('now')
WHERE password_migration_required IS NULL;