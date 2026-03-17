-- Ensure anon has full access to the applications table.
-- Safe to re-run — drops the existing policy first if present.
-- Covers all columns including resume_pdf_path (added in 011) and submitted_at.

DROP POLICY IF EXISTS "Allow anon full access for local MVP" ON applications;
DROP POLICY IF EXISTS "Allow all for authenticated users" ON applications;

CREATE POLICY "Allow anon full access for local MVP" ON applications
    FOR ALL USING (true) WITH CHECK (true);
