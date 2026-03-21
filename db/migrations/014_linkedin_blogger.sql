-- Migration 014: LinkedIn engagement log, blog posts, recruiter_engaged status, contacts source
-- Part of Artemis v2: sync layer + new skills (inbox, linkedin, blogger)

-- ─── Add recruiter_engaged to job_status enum ──────────────────
ALTER TYPE job_status ADD VALUE IF NOT EXISTS 'recruiter_engaged' AFTER 'applied';

-- ─── Add source column to contacts ─────────────────────────────
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT 'manual';
-- Valid values: 'manual', 'linkedin', 'gmail', 'referral'

-- ─── Engagement Log ────────────────────────────────────────────
-- Tracks LinkedIn and blog engagement actions with approval workflow
CREATE TABLE engagement_log (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    platform        TEXT NOT NULL DEFAULT 'linkedin',   -- 'linkedin', 'medium', 'personal_blog'
    action_type     TEXT NOT NULL,                       -- 'like', 'comment', 'share', 'connection_request', 'blog_post'
    target_url      TEXT,
    target_person   TEXT,
    content         TEXT,                                -- the comment text, share note, etc.
    status          TEXT NOT NULL DEFAULT 'drafted',     -- 'drafted', 'approved', 'posted', 'skipped'
    posted_at       TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_engagement_log_platform ON engagement_log(platform);
CREATE INDEX idx_engagement_log_status ON engagement_log(status);
CREATE INDEX idx_engagement_log_created ON engagement_log(created_at DESC);

-- ─── Blog Posts ────────────────────────────────────────────────
-- Content lifecycle: idea -> draft -> review -> published
CREATE TABLE blog_posts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title           TEXT NOT NULL,
    slug            TEXT UNIQUE NOT NULL,
    status          TEXT NOT NULL DEFAULT 'idea',        -- 'idea', 'draft', 'review', 'published'
    platform        TEXT,                                -- 'linkedin', 'medium', 'personal', null
    tags            TEXT[] DEFAULT '{}',
    summary         TEXT,                                -- brief description of the post angle
    published_url   TEXT,
    published_at    TIMESTAMPTZ,
    draft_path      TEXT,                                -- local file path to draft markdown
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_blog_posts_status ON blog_posts(status);
CREATE INDEX idx_blog_posts_slug ON blog_posts(slug);
CREATE INDEX idx_blog_posts_tags ON blog_posts USING GIN(tags);

-- ─── Auto-update triggers ──────────────────────────────────────
CREATE TRIGGER update_engagement_log_updated_at
    BEFORE UPDATE ON engagement_log
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_blog_posts_updated_at
    BEFORE UPDATE ON blog_posts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ─── RLS ───────────────────────────────────────────────────────
ALTER TABLE engagement_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE blog_posts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_all" ON engagement_log
    FOR ALL TO anon USING (true) WITH CHECK (true);

CREATE POLICY "anon_all" ON blog_posts
    FOR ALL TO anon USING (true) WITH CHECK (true);
