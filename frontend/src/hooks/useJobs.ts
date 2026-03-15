import { useState, useEffect, useCallback } from 'react';
import { supabase } from '../lib/supabase';
import type { Job, JobStatus } from '../types';

export function useJobs(statusFilter: JobStatus | 'all' = 'all') {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    try {
      let query = supabase
        .from('jobs')
        .select('*, companies(name, domain, careers_url), applications(resume_md, cover_letter_md, primer_md)')
        .not('status', 'eq', 'deleted')
        .order('created_at', { ascending: false });

      if (statusFilter !== 'all') {
        query = query.eq('status', statusFilter);
      }

      const { data, error: err } = await query;
      if (err) throw err;
      // Sort for triaging: pipeline priority → match score (desc) → recency
      const sorted = (data || []).sort((a, b) => {
        const statusPriority: Record<string, number> = {
          to_review: 0,
          scouted: 1,
          applied: 2,
          interviewing: 3,
          offer: 4,
          not_interested: 5,
          rejected: 6,
        };
        const aPri = statusPriority[a.status] ?? 99;
        const bPri = statusPriority[b.status] ?? 99;
        if (aPri !== bPri) return aPri - bPri;

        // Higher match score first, nulls last
        const aScore = a.match_score ?? -1;
        const bScore = b.match_score ?? -1;
        if (aScore !== bScore) return bScore - aScore;

        // Most recent first
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      });
      setJobs(sorted);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch jobs');
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  const updateStatus = useCallback(async (jobId: string, status: JobStatus, reason?: string) => {
    const updateData: Record<string, unknown> = { status };
    if (reason) updateData.rejection_reason = reason;

    const { error: err } = await supabase
      .from('jobs')
      .update(updateData)
      .eq('id', jobId);

    if (err) {
      setError(err.message);
      return false;
    }

    setJobs(prev => prev.map(j => j.id === jobId ? { ...j, status, rejection_reason: reason || j.rejection_reason } : j));
    return true;
  }, []);

  const deleteJob = useCallback(async (jobId: string) => {
    return updateStatus(jobId, 'deleted');
  }, [updateStatus]);

  const counts = jobs.reduce<Record<string, number>>((acc, j) => {
    acc[j.status] = (acc[j.status] || 0) + 1;
    return acc;
  }, {});

  return { jobs, loading, error, counts, updateStatus, deleteJob, refetch: fetchJobs };
}

export function useAllCounts() {
  const [counts, setCounts] = useState<Record<string, number>>({});

  useEffect(() => {
    async function fetch() {
      const { data } = await supabase
        .from('jobs')
        .select('status')
        .not('status', 'eq', 'deleted');
      
      if (data) {
        const c: Record<string, number> = {};
        data.forEach((j: { status: string }) => {
          c[j.status] = (c[j.status] || 0) + 1;
        });
        setCounts(c);
      }
    }
    fetch();
  }, []);

  return counts;
}
