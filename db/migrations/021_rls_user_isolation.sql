-- Multi-tenant RLS: enforce user isolation via auth.uid()
-- Run AFTER backfill_user_id.py to ensure all rows have user_id set

-- ─── Make user_id NOT NULL on all tables ─────────────────────────────────────
ALTER TABLE companies ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE jobs ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE contacts ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE contact_job_links ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE contact_interactions ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE anecdotes ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE applications ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE cost_log ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE engagement_log ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE blog_posts ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE scheduled_jobs ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE task_queue ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE user_state ALTER COLUMN user_id SET NOT NULL;

-- ─── Drop permissive (USING true) policies ────────────────────────────────────
DROP POLICY IF EXISTS "anon_all" ON companies;
DROP POLICY IF EXISTS "anon_all" ON jobs;
DROP POLICY IF EXISTS "anon_all" ON contacts;
DROP POLICY IF EXISTS "anon_all" ON contact_job_links;
DROP POLICY IF EXISTS "anon_all" ON contact_interactions;
DROP POLICY IF EXISTS "anon_all" ON anecdotes;
DROP POLICY IF EXISTS "anon_all" ON applications;
DROP POLICY IF EXISTS "anon_all" ON cost_log;
DROP POLICY IF EXISTS "anon_all" ON engagement_log;
DROP POLICY IF EXISTS "anon_all" ON blog_posts;
DROP POLICY IF EXISTS "anon_all" ON scheduled_jobs;
DROP POLICY IF EXISTS "anon_all" ON task_queue;
DROP POLICY IF EXISTS "anon_all" ON user_state;

-- ─── Create user-isolation policies (auth.uid() = user_id) ────────────────────
CREATE POLICY "user_isolation" ON companies FOR ALL TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "user_isolation" ON jobs FOR ALL TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "user_isolation" ON contacts FOR ALL TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "user_isolation" ON contact_job_links FOR ALL TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "user_isolation" ON contact_interactions FOR ALL TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "user_isolation" ON anecdotes FOR ALL TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "user_isolation" ON applications FOR ALL TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "user_isolation" ON cost_log FOR ALL TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "user_isolation" ON engagement_log FOR ALL TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "user_isolation" ON blog_posts FOR ALL TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "user_isolation" ON scheduled_jobs FOR ALL TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "user_isolation" ON task_queue FOR ALL TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "user_isolation" ON user_state FOR ALL TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Enable RLS on task_queue (wasn't enabled before)
ALTER TABLE task_queue ENABLE ROW LEVEL SECURITY;
