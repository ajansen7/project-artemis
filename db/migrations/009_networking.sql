-- Migration 009: Networking — Outreach tracking, contact-job links, interaction log

-- ─── New Enums ──────────────────────────────────────────────────
CREATE TYPE outreach_status AS ENUM (
    'identified',
    'draft_ready',
    'sent',
    'connected',
    'responded',
    'meeting_scheduled',
    'warm'
);

CREATE TYPE contact_priority AS ENUM (
    'high',
    'medium',
    'low'
);

CREATE TYPE interaction_type AS ENUM (
    'connection_request',
    'message_sent',
    'response_received',
    'meeting_scheduled',
    'referral_requested',
    'referral_given',
    'note'
);

-- ─── Enhance contacts table ──────────────────────────────────────
ALTER TABLE contacts
    ADD COLUMN outreach_status        outreach_status NOT NULL DEFAULT 'identified',
    ADD COLUMN priority               contact_priority,
    ADD COLUMN outreach_message_md    TEXT,
    ADD COLUMN is_personal_connection BOOLEAN NOT NULL DEFAULT false,
    ADD COLUMN mutual_connection_notes TEXT;

CREATE INDEX idx_contacts_outreach_status ON contacts(outreach_status);
CREATE INDEX idx_contacts_priority ON contacts(priority);

-- ─── Contact-Job links (many-to-many) ───────────────────────────
CREATE TABLE contact_job_links (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id  UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    job_id      UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    notes       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (contact_id, job_id)
);

CREATE INDEX idx_contact_job_links_contact ON contact_job_links(contact_id);
CREATE INDEX idx_contact_job_links_job ON contact_job_links(job_id);

-- ─── Contact Interaction Log ─────────────────────────────────────
CREATE TABLE contact_interactions (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id        UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    interaction_type  interaction_type NOT NULL,
    notes             TEXT,
    occurred_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_contact_interactions_contact ON contact_interactions(contact_id);
CREATE INDEX idx_contact_interactions_occurred ON contact_interactions(occurred_at DESC);

-- ─── RLS ─────────────────────────────────────────────────────────
ALTER TABLE contact_job_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE contact_interactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_all" ON contact_job_links
    FOR ALL TO anon USING (true) WITH CHECK (true);

CREATE POLICY "anon_all" ON contact_interactions
    FOR ALL TO anon USING (true) WITH CHECK (true);
