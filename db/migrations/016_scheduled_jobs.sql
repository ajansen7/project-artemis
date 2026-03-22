-- Migration 016: Scheduled jobs for recurring automation
-- Stores user-configurable schedules that APScheduler executes via the Artemis skill runner

CREATE TABLE scheduled_jobs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,                   -- user-facing display name
    skill           TEXT NOT NULL,                   -- skill command to invoke (e.g. '/scout', '/inbox')
    skill_args      TEXT,                            -- optional args passed to the skill
    cron_expr       TEXT NOT NULL,                   -- cron expression (e.g. '0 8 * * 1-5')
    enabled         BOOLEAN NOT NULL DEFAULT false,  -- default disabled so user opts in
    last_run_at     TIMESTAMPTZ,
    last_status     TEXT,                            -- 'success', 'failed', 'running'
    last_error      TEXT,                            -- error message if failed
    notes           TEXT,                            -- user description of what this does
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_scheduled_jobs_enabled ON scheduled_jobs(enabled);

CREATE TRIGGER update_scheduled_jobs_updated_at
    BEFORE UPDATE ON scheduled_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

ALTER TABLE scheduled_jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_all" ON scheduled_jobs
    FOR ALL TO anon USING (true) WITH CHECK (true);

-- ─── Seed default schedules (all disabled) ──────────────────────
INSERT INTO scheduled_jobs (name, skill, cron_expr, enabled, notes) VALUES
    ('Daily Inbox Check',           '/inbox',       '0 8 * * 1-5',   false, 'Scan Gmail for recruiter emails and interview scheduling'),
    ('Daily LinkedIn Engagement',   '/linkedin',    '0 9 * * 1-5',   false, 'Find posts to engage with, draft comments'),
    ('Daily Job Scout',             '/scout',       '0 7 * * 1-5',   false, 'Search for new job postings matching preferences'),
    ('Networking Follow-ups',       '/network',     '0 10 * * 1,4',  false, 'Surface stale contacts needing follow-up'),
    ('Interview Prep Reminder',     '/prep',        '0 18 * * *',    false, 'Check upcoming interview loops, nudge to practice'),
    ('Weekly Blog Ideas',           '/blog-ideas',  '0 10 * * 1',    false, 'Propose blog topics from recent activity'),
    ('Draft Publish Reminder',      '/blog-status', '0 9 * * 5',     false, 'Remind about drafts ready to publish');
