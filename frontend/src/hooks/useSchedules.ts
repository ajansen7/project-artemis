import { useState, useEffect, useCallback } from 'react';
import { supabase } from '../lib/supabase';
import type { ScheduledJob } from '../types';

import { API_BASE as API } from '../lib/api';

export function useSchedules() {
  const [schedules, setSchedules] = useState<ScheduledJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSchedules = useCallback(async () => {
    setLoading(true);
    try {
      const { data, error: err } = await supabase
        .from('scheduled_jobs')
        .select('*')
        .order('created_at', { ascending: true });

      if (err) throw err;
      setSchedules(data || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch schedules');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSchedules();
  }, [fetchSchedules]);

  // Refresh when Claude signals a schedules-table change via SSE
  useEffect(() => {
    const handler = (e: Event) => {
      const tables: string[] | undefined = (e as CustomEvent).detail?.tables;
      if (!tables || tables.includes('scheduled_jobs') || tables.includes('schedules')) {
        fetchSchedules();
      }
    };
    window.addEventListener('artemis:refresh', handler);
    return () => window.removeEventListener('artemis:refresh', handler);
  }, [fetchSchedules]);

  // Mutations go through the API so APScheduler stays in sync

  const updateSchedule = useCallback(async (id: string, fields: Partial<ScheduledJob>) => {
    try {
      const res = await fetch(`${API}/api/schedules/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(fields),
      });
      if (!res.ok) throw new Error(await res.text());
      const updated = await res.json();
      setSchedules(prev => prev.map(s => s.id === id ? updated : s));
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update schedule');
      return false;
    }
  }, []);

  const createSchedule = useCallback(async (fields: Partial<ScheduledJob>) => {
    try {
      const res = await fetch(`${API}/api/schedules`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(fields),
      });
      if (!res.ok) throw new Error(await res.text());
      const created = await res.json();
      setSchedules(prev => [...prev, created]);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create schedule');
      return false;
    }
  }, []);

  const deleteSchedule = useCallback(async (id: string) => {
    try {
      const res = await fetch(`${API}/api/schedules/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error(await res.text());
      setSchedules(prev => prev.filter(s => s.id !== id));
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete schedule');
      return false;
    }
  }, []);

  const toggleEnabled = useCallback(async (id: string, enabled: boolean) => {
    return updateSchedule(id, { enabled } as Partial<ScheduledJob>);
  }, [updateSchedule]);

  const counts = {
    total: schedules.length,
    enabled: schedules.filter(s => s.enabled).length,
    disabled: schedules.filter(s => !s.enabled).length,
  };

  return { schedules, counts, loading, error, updateSchedule, createSchedule, deleteSchedule, toggleEnabled, refetch: fetchSchedules };
}
