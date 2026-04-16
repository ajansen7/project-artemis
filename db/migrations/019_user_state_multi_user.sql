-- Add user_id to user_state for per-user state isolation

ALTER TABLE user_state ADD COLUMN IF NOT EXISTS user_id UUID
    REFERENCES auth.users(id) ON DELETE CASCADE;

-- Drop old single-key unique constraint (blocks multi-user)
ALTER TABLE user_state DROP CONSTRAINT IF EXISTS user_state_key_key;

-- New compound unique index: same key allowed per user, but not duplicated per user
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_state_user_key
    ON user_state(user_id, key) WHERE user_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_user_state_user_id ON user_state(user_id);

-- Replace open anon_all with user-scoped RLS
DROP POLICY IF EXISTS "anon_all" ON user_state;
CREATE POLICY "User can read own state"   ON user_state FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "User can insert own state" ON user_state FOR INSERT WITH CHECK (user_id = auth.uid());
CREATE POLICY "User can update own state" ON user_state FOR UPDATE USING (user_id = auth.uid());
CREATE POLICY "User can delete own state" ON user_state FOR DELETE USING (user_id = auth.uid());
-- Note: state_sync.py uses service_role_key so it bypasses RLS — explicit filtering is added in the tool
