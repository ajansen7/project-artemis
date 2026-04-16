-- 023_user_profiles.sql
-- Admin-approved account creation: profile table + auto-create trigger

-- ─── Table ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_profiles (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    email       TEXT NOT NULL,
    role        TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'user')),
    status      TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'blocked')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index for fast lookup by user_id (used on every request)
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);

-- ─── Auto-create profile on signup ──────────────────────────────
-- If this is the FIRST user ever, auto-approve as admin.
-- Otherwise, status = 'pending'.
CREATE OR REPLACE FUNCTION handle_new_user_profile()
RETURNS TRIGGER AS $$
DECLARE
    user_count INT;
    new_role TEXT := 'user';
    new_status TEXT := 'pending';
BEGIN
    SELECT COUNT(*) INTO user_count FROM user_profiles;
    IF user_count = 0 THEN
        new_role := 'admin';
        new_status := 'approved';
    END IF;

    INSERT INTO user_profiles (user_id, email, role, status)
    VALUES (NEW.id, COALESCE(NEW.email, ''), new_role, new_status)
    ON CONFLICT (user_id) DO NOTHING;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Fire after insert on auth.users
DROP TRIGGER IF EXISTS on_auth_user_created_profile ON auth.users;
CREATE TRIGGER on_auth_user_created_profile
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION handle_new_user_profile();

-- ─── RLS ─────────────────────────────────────────────────────────
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Users can read their own profile
CREATE POLICY "users_read_own_profile" ON user_profiles
    FOR SELECT TO authenticated
    USING (auth.uid() = user_id);

-- Admins can read all profiles (for the admin panel)
CREATE POLICY "admins_read_all_profiles" ON user_profiles
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM user_profiles up
            WHERE up.user_id = auth.uid() AND up.role = 'admin'
        )
    );

-- Admins can update any profile (approve/block)
CREATE POLICY "admins_update_profiles" ON user_profiles
    FOR UPDATE TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM user_profiles up
            WHERE up.user_id = auth.uid() AND up.role = 'admin'
        )
    );

-- Service role (API backend) bypasses RLS automatically
