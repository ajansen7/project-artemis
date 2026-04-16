-- Migration 018: Add multi-user support with user_id scoping

-- Add user_id columns to user-scoped tables
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE applications ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE anecdotes ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

-- Create indexes for efficient filtering by user
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_companies_user_id ON companies(user_id);
CREATE INDEX IF NOT EXISTS idx_contacts_user_id ON contacts(user_id);
CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id);
CREATE INDEX IF NOT EXISTS idx_anecdotes_user_id ON anecdotes(user_id);

-- Update RLS policies to scope by user_id
DROP POLICY IF EXISTS "Allow anon full access for local MVP" ON jobs;
DROP POLICY IF EXISTS "Allow all for authenticated users" ON jobs;
CREATE POLICY "User can see own jobs" ON jobs
    FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "User can insert own jobs" ON jobs
    FOR INSERT WITH CHECK (user_id = auth.uid());
CREATE POLICY "User can update own jobs" ON jobs
    FOR UPDATE USING (user_id = auth.uid());
CREATE POLICY "User can delete own jobs" ON jobs
    FOR DELETE USING (user_id = auth.uid());

DROP POLICY IF EXISTS "Allow anon full access for local MVP" ON companies;
DROP POLICY IF EXISTS "Allow all for authenticated users" ON companies;
CREATE POLICY "User can see own companies" ON companies
    FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "User can insert own companies" ON companies
    FOR INSERT WITH CHECK (user_id = auth.uid());
CREATE POLICY "User can update own companies" ON companies
    FOR UPDATE USING (user_id = auth.uid());
CREATE POLICY "User can delete own companies" ON companies
    FOR DELETE USING (user_id = auth.uid());

DROP POLICY IF EXISTS "Allow anon full access for local MVP" ON contacts;
DROP POLICY IF EXISTS "Allow all for authenticated users" ON contacts;
CREATE POLICY "User can see own contacts" ON contacts
    FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "User can insert own contacts" ON contacts
    FOR INSERT WITH CHECK (user_id = auth.uid());
CREATE POLICY "User can update own contacts" ON contacts
    FOR UPDATE USING (user_id = auth.uid());
CREATE POLICY "User can delete own contacts" ON contacts
    FOR DELETE USING (user_id = auth.uid());

DROP POLICY IF EXISTS "Allow anon full access for local MVP" ON applications;
DROP POLICY IF EXISTS "Allow all for authenticated users" ON applications;
CREATE POLICY "User can see own applications" ON applications
    FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "User can insert own applications" ON applications
    FOR INSERT WITH CHECK (user_id = auth.uid());
CREATE POLICY "User can update own applications" ON applications
    FOR UPDATE USING (user_id = auth.uid());
CREATE POLICY "User can delete own applications" ON applications
    FOR DELETE USING (user_id = auth.uid());

DROP POLICY IF EXISTS "Allow anon full access for local MVP" ON anecdotes;
DROP POLICY IF EXISTS "Allow all for authenticated users" ON anecdotes;
CREATE POLICY "User can see own anecdotes" ON anecdotes
    FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "User can insert own anecdotes" ON anecdotes
    FOR INSERT WITH CHECK (user_id = auth.uid());
CREATE POLICY "User can update own anecdotes" ON anecdotes
    FOR UPDATE USING (user_id = auth.uid());
CREATE POLICY "User can delete own anecdotes" ON anecdotes
    FOR DELETE USING (user_id = auth.uid());

-- Note: contact_job_links and contact_interactions will inherit through CASCADE 
-- and their RLS should be updated to join through contacts
DROP POLICY IF EXISTS "Allow anon full access for local MVP" ON contact_job_links;
DROP POLICY IF EXISTS "anon_all" ON contact_job_links;
CREATE POLICY "User can see own contact job links" ON contact_job_links
    FOR ALL USING (contact_id IN (SELECT id FROM contacts WHERE user_id = auth.uid()));

DROP POLICY IF EXISTS "Allow anon full access for local MVP" ON contact_interactions;
DROP POLICY IF EXISTS "anon_all" ON contact_interactions;
CREATE POLICY "User can see own contact interactions" ON contact_interactions
    FOR ALL USING (contact_id IN (SELECT id FROM contacts WHERE user_id = auth.uid()));
