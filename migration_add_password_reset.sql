-- Migration: Add Password Reset Columns to Users Table
-- Date: 2025-11-10
-- Purpose: Add support for password reset functionality

-- Add password_reset_token column
ALTER TABLE users
ADD COLUMN password_reset_token VARCHAR(255) UNIQUE NULL DEFAULT NULL;

-- Add password_reset_expires_at column
ALTER TABLE users
ADD COLUMN password_reset_expires_at TIMESTAMP NULL DEFAULT NULL;

-- Create indexes for better query performance
CREATE INDEX idx_password_reset_token ON users(password_reset_token);
CREATE INDEX idx_password_reset_expires_at ON users(password_reset_expires_at);

-- Optionally: Create an index for cleanup queries
-- This helps efficiently find expired reset tokens for cleanup
CREATE INDEX idx_password_reset_not_expired ON users(password_reset_expires_at)
WHERE password_reset_expires_at IS NOT NULL;
