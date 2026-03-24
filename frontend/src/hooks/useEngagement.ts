import { useState, useEffect, useCallback } from 'react';
import { supabase } from '../lib/supabase';
import type { EngagementEntry, EngagementStatus } from '../types';

export function useEngagement() {
  const [entries, setEntries] = useState<EngagementEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchEntries = useCallback(async () => {
    setLoading(true);
    try {
      const { data, error: err } = await supabase
        .from('engagement_log')
        .select('*')
        .order('created_at', { ascending: false });

      if (err) throw err;
      setEntries(data || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch engagement log');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEntries();
  }, [fetchEntries]);

  useEffect(() => {
    const channel = supabase
      .channel('engagement-realtime')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'engagement_log' }, () => { fetchEntries(); })
      .subscribe();
    return () => { supabase.removeChannel(channel); };
  }, [fetchEntries]);

  const updateStatus = useCallback(async (id: string, status: EngagementStatus) => {
    const updateData: Record<string, unknown> = { status };
    if (status === 'posted') {
      updateData.posted_at = new Date().toISOString();
    }

    const { error: err } = await supabase
      .from('engagement_log')
      .update(updateData)
      .eq('id', id);

    if (err) {
      setError(err.message);
      return false;
    }

    setEntries(prev =>
      prev.map(e => e.id === id ? { ...e, status, ...(status === 'posted' ? { posted_at: new Date().toISOString() } : {}) } : e)
    );
    return true;
  }, []);

  const counts = {
    total: entries.length,
    drafted: entries.filter(e => e.status === 'drafted').length,
    approved: entries.filter(e => e.status === 'approved').length,
    posted: entries.filter(e => e.status === 'posted').length,
  };

  return { entries, counts, loading, error, updateStatus, refetch: fetchEntries };
}
