-- Migration 022: RLS cleanup — drop all legacy allow-all policies, enforce user isolation everywhere
--
-- Fixes: "Allow anon full access for local MVP" policies missed by migration 021.
-- These policies were not dropped in 021 because they had a different name than "anon_all".
--
-- Impact: Removes all remaining weak/allow-all policies, replacing them with strict
--         user_isolation policies. All tables now enforce auth.uid() = user_id.

BEGIN;

-- Drop all remaining legacy allow-all policies by name
DROP POLICY IF EXISTS "Allow anon full access for local MVP" ON companies;
DROP POLICY IF EXISTS "Allow anon full access for local MVP" ON jobs;
DROP POLICY IF EXISTS "Allow anon full access for local MVP" ON contacts;
DROP POLICY IF EXISTS "Allow anon full access for local MVP" ON applications;
DROP POLICY IF EXISTS "Allow anon full access for local MVP" ON anecdotes;

-- Drop any other legacy broad-access policies that may exist
DROP POLICY IF EXISTS "Allow authenticated full access" ON cost_log;
DROP POLICY IF EXISTS "Allow all for authenticated users" ON companies;
DROP POLICY IF EXISTS "Allow all for authenticated users" ON jobs;
DROP POLICY IF EXISTS "Allow all for authenticated users" ON contacts;
DROP POLICY IF EXISTS "Allow all for authenticated users" ON anecdotes;
DROP POLICY IF EXISTS "Allow all for authenticated users" ON applications;
DROP POLICY IF EXISTS "Allow all for authenticated users" ON cost_log;

-- Ensure user_isolation policy exists on cost_log with correct WITH CHECK
-- Drop and re-create to ensure correct definition
DROP POLICY IF EXISTS "user_isolation" ON cost_log;
CREATE POLICY "user_isolation" ON cost_log
  FOR ALL TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Confirm RLS is enabled on all tables (idempotent)
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE anecdotes ENABLE ROW LEVEL SECURITY;
ALTER TABLE cost_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE contact_job_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE contact_interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE engagement_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE blog_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE scheduled_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_state ENABLE ROW LEVEL SECURITY;

COMMIT;
