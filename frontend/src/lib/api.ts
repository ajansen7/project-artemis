import { supabase } from './supabase';
import type { UserProfile } from '../types';

export const API_BASE = window.location.origin;

export async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  const { data: { session } } = await supabase.auth.getSession();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };
  if (session?.access_token) {
    headers['Authorization'] = `Bearer ${session.access_token}`;
  }
  return fetch(url, { ...options, headers });
}

export async function fetchMyProfile(): Promise<UserProfile> {
  const res = await fetchWithAuth(`${API_BASE}/api/profile/me`);
  if (!res.ok) throw new Error('Failed to fetch profile');
  return res.json();
}

export async function fetchAllUsers(): Promise<UserProfile[]> {
  const res = await fetchWithAuth(`${API_BASE}/api/admin/users`);
  if (!res.ok) throw new Error('Failed to fetch users');
  const data = await res.json();
  return data.users;
}

export async function updateUser(
  userId: string,
  update: { status?: string; role?: string }
): Promise<void> {
  const res = await fetchWithAuth(`${API_BASE}/api/admin/users/${userId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(update),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Update failed' }));
    throw new Error(err.detail || 'Update failed');
  }
}
