-- Add 'not_interested' and 'deleted' to the job_status enum
-- Add a rejection_reason column to store why the user passed on a job

ALTER TYPE job_status ADD VALUE IF NOT EXISTS 'not_interested';
ALTER TYPE job_status ADD VALUE IF NOT EXISTS 'deleted';

ALTER TABLE jobs ADD COLUMN IF NOT EXISTS rejection_reason TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS notes TEXT;
