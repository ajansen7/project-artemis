-- Relax RLS for the single-user local MVP front-end
-- This allows the Next.js client to read/write jobs transparently via the anon key

DROP POLICY IF EXISTS "Allow all for authenticated users" ON jobs;

CREATE POLICY "Allow anon full access for local MVP" ON jobs
    FOR ALL USING (true) WITH CHECK (true);
