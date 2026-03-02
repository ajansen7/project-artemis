-- Relax RLS for anecdotes table so the frontend can insert HITL anecdotes
-- Also relax for companies table

DROP POLICY IF EXISTS "Allow all for authenticated users" ON anecdotes;
CREATE POLICY "Allow anon full access for local MVP" ON anecdotes
    FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow all for authenticated users" ON companies;
CREATE POLICY "Allow anon full access for local MVP" ON companies
    FOR ALL USING (true) WITH CHECK (true);
