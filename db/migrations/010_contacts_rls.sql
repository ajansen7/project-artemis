-- Migration 010: Relax RLS on contacts (and new networking tables) for local MVP anon access

DROP POLICY IF EXISTS "Allow all for authenticated users" ON contacts;
CREATE POLICY "Allow anon full access for local MVP" ON contacts
    FOR ALL USING (true) WITH CHECK (true);

-- contact_job_links and contact_interactions were created in 009 with TO anon syntax.
-- Re-create them using the same USING (true) pattern for consistency.
DROP POLICY IF EXISTS "anon_all" ON contact_job_links;
CREATE POLICY "Allow anon full access for local MVP" ON contact_job_links
    FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "anon_all" ON contact_interactions;
CREATE POLICY "Allow anon full access for local MVP" ON contact_interactions
    FOR ALL USING (true) WITH CHECK (true);
