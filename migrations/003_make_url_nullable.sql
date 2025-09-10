-- Migration: Make article URL field nullable
-- Date: 2025-01-10
-- Description: Allow articles to be created without URL

-- Modify the articles table to make url column nullable
ALTER TABLE articles ALTER COLUMN url DROP NOT NULL;

-- Add comment to the column
COMMENT ON COLUMN articles.url IS 'Article URL (optional) - can be NULL for manually created articles';