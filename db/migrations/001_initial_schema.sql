-- Project Artemis — Initial Supabase Schema
-- Run this via the Supabase SQL Editor or `supabase db push`

-- ─── Enable extensions ─────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── Companies ─────────────────────────────────────────────────
CREATE TABLE companies (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        TEXT NOT NULL UNIQUE,
    domain      TEXT,
    careers_url TEXT,
    notes       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── Jobs ──────────────────────────────────────────────────────
CREATE TYPE job_status AS ENUM (
    'scouted',
    'to_review',
    'applied',
    'interviewing',
    'rejected',
    'offer'
);

CREATE TABLE jobs (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id          UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    title               TEXT NOT NULL,
    url                 TEXT UNIQUE,
    description_md      TEXT,
    status              job_status NOT NULL DEFAULT 'scouted',
    match_score         INTEGER CHECK (match_score >= 0 AND match_score <= 100),
    gap_analysis_json   JSONB,
    source              TEXT,           -- e.g., 'scout', 'manual', 'check_command'
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_company ON jobs(company_id);
CREATE INDEX idx_jobs_match_score ON jobs(match_score DESC);

-- ─── Contacts ──────────────────────────────────────────────────
CREATE TABLE contacts (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id          UUID REFERENCES companies(id) ON DELETE SET NULL,
    name                TEXT NOT NULL,
    title               TEXT,
    linkedin_url        TEXT UNIQUE,
    email               TEXT,
    relationship_type   TEXT DEFAULT 'unknown', -- alumni, recruiter, hiring_manager, referral
    notes               TEXT,
    last_contacted_at   TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_contacts_company ON contacts(company_id);

-- ─── Anecdotes (STAR format) ───────────────────────────────────
CREATE TABLE anecdotes (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title       TEXT NOT NULL,
    situation   TEXT,
    task        TEXT,
    action      TEXT,
    result      TEXT,
    tags        TEXT[] DEFAULT '{}',
    source      TEXT DEFAULT 'user_input',   -- user_input, drive, claude_coach
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_anecdotes_tags ON anecdotes USING GIN(tags);

-- ─── Applications ──────────────────────────────────────────────
CREATE TABLE applications (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id          UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    resume_url      TEXT,
    cover_letter_url TEXT,
    submitted_at    TIMESTAMPTZ,
    follow_up_at    TIMESTAMPTZ,
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_applications_job ON applications(job_id);
CREATE INDEX idx_applications_follow_up ON applications(follow_up_at)
    WHERE follow_up_at IS NOT NULL;

-- ─── Cost Tracking ─────────────────────────────────────────────
CREATE TABLE cost_log (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service     TEXT NOT NULL,      -- 'gemini', 'proxycurl', 'firecrawl'
    operation   TEXT,               -- 'analyze_job', 'scrape', 'lookup'
    cost_usd    NUMERIC(10, 6),
    tokens_in   INTEGER,
    tokens_out  INTEGER,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cost_log_service ON cost_log(service, created_at);

-- ─── Auto-update updated_at ────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_companies_updated_at
    BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_contacts_updated_at
    BEFORE UPDATE ON contacts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_anecdotes_updated_at
    BEFORE UPDATE ON anecdotes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_applications_updated_at
    BEFORE UPDATE ON applications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ─── Row-Level Security ────────────────────────────────────────
-- Enable RLS on all tables (single-user system, but good practice)
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE anecdotes ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE cost_log ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users full access (single-user system)
CREATE POLICY "Allow all for authenticated users" ON companies
    FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "Allow all for authenticated users" ON jobs
    FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "Allow all for authenticated users" ON contacts
    FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "Allow all for authenticated users" ON anecdotes
    FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "Allow all for authenticated users" ON applications
    FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "Allow all for authenticated users" ON cost_log
    FOR ALL USING (auth.role() = 'authenticated');
