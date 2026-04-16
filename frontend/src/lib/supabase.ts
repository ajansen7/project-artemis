import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY in .env.local');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Initialize auth state on app load
export async function initAuth() {
  const {
    data: { session },
  } = await supabase.auth.getSession();

  return session;
}

// Subscribe to auth state changes
export function onAuthStateChange(callback: (session: any | null) => void) {
  const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
    callback(session);
  });

  return subscription;
}

// Sync from CLI session stored on FastAPI server
export async function syncFromServerSession(forceSync: boolean = false): Promise<any | null> {
  try {
    const res = await fetch('/api/auth/session');
    if (!res.ok) return null;
    const data = await res.json();
    if (!data.signed_in || !data.access_token) return null;

    const { data: { session: existing } } = await supabase.auth.getSession();

    // If forceSync is true (e.g., on focus), always sync from CLI if different user
    if (forceSync && existing && existing.user?.id !== data.user_id) {
      const { data: { session }, error } = await supabase.auth.setSession({
        access_token: data.access_token,
        refresh_token: data.refresh_token,
      });
      if (error) return null;
      return session;
    }

    // If no active browser session, sync from CLI
    if (!existing) {
      const { data: { session }, error } = await supabase.auth.setSession({
        access_token: data.access_token,
        refresh_token: data.refresh_token,
      });
      if (error) return null;
      return session;
    }

    // Browser session exists and same user or not forcing sync
    return existing;
  } catch {
    return null;
  }
}
