-- Scout Agent — Target company watchlist support
-- Adds fields to the companies table for the Scout's company discovery

ALTER TABLE companies ADD COLUMN IF NOT EXISTS is_target BOOLEAN DEFAULT false;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS why_target TEXT;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS last_scouted_at TIMESTAMPTZ;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS scout_priority TEXT DEFAULT 'medium';  -- high, medium, low

-- Make company_id nullable on jobs so Scout can insert jobs without a company initially
ALTER TABLE jobs ALTER COLUMN company_id DROP NOT NULL;

-- Index for quick target company lookups
CREATE INDEX IF NOT EXISTS idx_companies_is_target ON companies(is_target) WHERE is_target = true;
