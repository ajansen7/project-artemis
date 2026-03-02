-- Make company_id optional for jobs
-- This allows our frontend to insert a placeholder "Analyzing..." job
-- before the Agent has scraped the JD and determined the company.

ALTER TABLE jobs ALTER COLUMN company_id DROP NOT NULL;
