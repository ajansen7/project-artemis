-- Add form_fills_md to store pre-written answers to common application form questions.
-- The existing anon full-access policy on applications (from 012) covers this column automatically.
ALTER TABLE applications ADD COLUMN IF NOT EXISTS form_fills_md TEXT;
