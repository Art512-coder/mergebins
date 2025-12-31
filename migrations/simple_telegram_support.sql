-- Simple migration to add Telegram support columns
-- Add telegram_id column (without UNIQUE constraint initially)
ALTER TABLE users ADD COLUMN telegram_id INTEGER;

-- Add username column 
ALTER TABLE users ADD COLUMN username TEXT;

-- Update username for existing users based on email
UPDATE users SET username = COALESCE(
  name, 
  CASE 
    WHEN email IS NOT NULL THEN SUBSTR(email, 1, INSTR(email, '@') - 1)
    ELSE 'user' || id
  END
) WHERE username IS NULL;