-- Migration 015: Add content column to blog_posts
-- Stores the full markdown body of a post directly in the DB,
-- so the UI can read it without requiring disk access.

ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS content TEXT;
