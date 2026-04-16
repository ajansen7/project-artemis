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
export async function syncFromServerSession(): Promise<any | null> {
  try {
    const res = await fetch('/api/auth/session');
    if (!res.ok) return null;
    const data = await res.json();
    if (!data.signed_in || !data.access_token) return null;

    // Only sync if no active browser session exists
    const { data: { session: existing } } = await supabase.auth.getSession();
    if (existing) return existing; // don't override an active browser session

    const { data: { session }, error } = await supabase.auth.setSession({
      access_token: data.access_token,
      refresh_token: data.refresh_token,
    });
    if (error) return null;
    return session;
  } catch {
    return null;
  }
}
