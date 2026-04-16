import { useState, useEffect, useCallback } from 'react';
import type { UserProfile } from '../types';
import { fetchAllUsers, updateUser } from '../lib/api';

export function useAdmin() {
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchAllUsers();
      setUsers(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load users');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refetch();
  }, [refetch]);

  const approveUser = async (userId: string) => {
    await updateUser(userId, { status: 'approved' });
    await refetch();
  };

  const blockUser = async (userId: string) => {
    await updateUser(userId, { status: 'blocked' });
    await refetch();
  };

  const setRole = async (userId: string, role: 'admin' | 'user') => {
    await updateUser(userId, { role });
    await refetch();
  };

  return { users, loading, error, refetch, approveUser, blockUser, setRole };
}
