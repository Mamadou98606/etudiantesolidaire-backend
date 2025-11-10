-- Migration: Add email verification columns to users table
-- Date: 2025-11-10
-- Description: Add email_verified, email_verification_token, and email_token_expires_at columns

ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verification_token VARCHAR(255) UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_token_expires_at TIMESTAMP;

-- Create index on email_verification_token for faster lookups
CREATE INDEX IF NOT EXISTS idx_email_verification_token ON users(email_verification_token);
