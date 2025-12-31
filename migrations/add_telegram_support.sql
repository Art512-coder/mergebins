-- Add Telegram support columns to existing users table
-- This migration adds telegram_id and username columns for cross-platform user linking

-- Add telegram_id column (for Telegram user authentication)
ALTER TABLE users ADD COLUMN telegram_id INTEGER UNIQUE;

-- Add username column (for both web and Telegram users)
ALTER TABLE users ADD COLUMN username TEXT;

-- Make email nullable for Telegram-only users (requires recreating table due to SQLite limitations)
-- Create temporary table with new schema
CREATE TABLE users_new (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT,  -- Made nullable for Telegram-only users
  password_hash TEXT,  -- Made nullable for Telegram-only users
  telegram_id INTEGER UNIQUE,
  username TEXT,
  name TEXT,
  premium_until DATETIME,
  credits INTEGER DEFAULT 10,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  last_login DATETIME,
  email_verified BOOLEAN DEFAULT FALSE,
  verification_token TEXT,
  reset_token TEXT,
  reset_expires DATETIME
);

-- Copy existing data to new table
INSERT INTO users_new (
  id, email, password_hash, name, premium_until, credits, 
  created_at, last_login, email_verified, verification_token, 
  reset_token, reset_expires
)
SELECT 
  id, email, password_hash, name, premium_until, credits, 
  created_at, last_login, email_verified, verification_token, 
  reset_token, reset_expires
FROM users;

-- Update username for existing users based on email
UPDATE users_new SET username = COALESCE(
  name, 
  CASE 
    WHEN email IS NOT NULL THEN SUBSTR(email, 1, INSTR(email, '@') - 1)
    ELSE 'user' || id
  END
) WHERE username IS NULL;

-- Drop old table and rename new table
DROP TABLE users;
ALTER TABLE users_new RENAME TO users;

-- Recreate indexes
CREATE UNIQUE INDEX idx_users_email ON users(email) WHERE email IS NOT NULL;
CREATE UNIQUE INDEX idx_users_telegram_id ON users(telegram_id) WHERE telegram_id IS NOT NULL;
CREATE INDEX idx_users_username ON users(username);