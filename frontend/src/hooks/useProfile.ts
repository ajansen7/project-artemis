import { useState, useEffect } from 'react';
import type { UserProfile } from '../types';
import { fetchMyProfile } from '../lib/api';

export function useProfile() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = async () => {
    try {
      const p = await fetchMyProfile();
      setProfile(p);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refetch();
  }, []);

  return { profile, loading, error, refetch };
}
