-- Cloud sync: key-value store for state files (identity.md, voice.md, etc.)
-- Enables multi-machine sync by backing state/ files with Supabase.

CREATE TABLE user_state (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key        TEXT NOT NULL UNIQUE,
    content    TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER update_user_state_updated_at
    BEFORE UPDATE ON user_state
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

ALTER TABLE user_state ENABLE ROW LEVEL SECURITY;
CREATE POLICY "anon_all" ON user_state
    FOR ALL TO anon USING (true) WITH CHECK (true);
