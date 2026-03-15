-- Relax RLS for the applications table
DROP POLICY IF EXISTS "Allow all for authenticated users" ON applications;

CREATE POLICY "Allow anon full access for local MVP" ON applications
    FOR ALL USING (true) WITH CHECK (true);
