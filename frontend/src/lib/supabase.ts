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
  const { data: listener } = supabase.auth.onAuthStateChange((event, session) => {
    callback(session);
  });

  return listener;
}
