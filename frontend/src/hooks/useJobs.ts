import { useState, useEffect, useCallback, useMemo } from 'react';
import { supabase } from '../lib/supabase';
import type { Job, JobStatus, JobSortMode } from '../types';

const STATUS_PRIORITY: Record<string, number> = {
  to_review: 0,
  scouted: 1,
  applied: 2,
  recruiter_engaged: 3,
  interviewing: 4,
  offer: 5,
  not_interested: 6,
  rejected: 7,
};

function sortJobs(jobs: Job[], mode: JobSortMode): Job[] {
  return [...jobs].sort((a, b) => {
    switch (mode) {
      case 'score': {
        const aScore = a.match_score ?? -1;
        const bScore = b.match_score ?? -1;
        if (aScore !== bScore) return bScore - aScore;
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      }
      case 'date':
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      case 'company': {
        const aName = a.companies?.name || 'zzz';
        const bName = b.companies?.name || 'zzz';
        const cmp = aName.localeCompare(bName);
        if (cmp !== 0) return cmp;
        const aScore = a.match_score ?? -1;
        const bScore = b.match_score ?? -1;
        return bScore - aScore;
      }
      default: {
        // Pipeline priority > score > recency
        const aPri = STATUS_PRIORITY[a.status] ?? 99;
        const bPri = STATUS_PRIORITY[b.status] ?? 99;
        if (aPri !== bPri) return aPri - bPri;
        const aScore = a.match_score ?? -1;
        const bScore = b.match_score ?? -1;
        if (aScore !== bScore) return bScore - aScore;
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      }
    }
  });
}

export function groupJobsByCompany(jobs: Job[]): Map<string, Job[]> {
  const groups = new Map<string, Job[]>();
  for (const job of jobs) {
    const company = job.companies?.name || 'Unknown';
    const group = groups.get(company) || [];
    group.push(job);
    groups.set(company, group);
  }
  // Sort within each group by score descending
  for (const [key, group] of groups) {
    groups.set(key, group.sort((a, b) => (b.match_score ?? -1) - (a.match_score ?? -1)));
  }
  // Sort groups by count descending, then alphabetically
  return new Map(
    [...groups.entries()].sort((a, b) => {
      if (b[1].length !== a[1].length) return b[1].length - a[1].length;
      return a[0].localeCompare(b[0]);
    })
  );
}

export function useJobs(statusFilter: JobStatus | 'all' = 'all') {
  const [rawJobs, setRawJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortMode, setSortMode] = useState<JobSortMode>('default');
  const [groupByCompany, setGroupByCompany] = useState(false);

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    try {
      let query = supabase
        .from('jobs')
        .select('*, companies(name, domain, careers_url), applications(resume_md, cover_letter_md, primer_md, form_fills_md, resume_pdf_path, submitted_at)')
        .not('status', 'eq', 'deleted')
        .order('created_at', { ascending: false });

      if (statusFilter !== 'all') {
        query = query.eq('status', statusFilter);
      }

      const { data, error: err } = await query;
      if (err) throw err;
      setRawJobs(data || []);
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

  const jobs = useMemo(() => sortJobs(rawJobs, sortMode), [rawJobs, sortMode]);

  const companyGroups = useMemo(
    () => groupByCompany ? groupJobsByCompany(jobs) : null,
    [jobs, groupByCompany]
  );

  const updateStatus = useCallback(async (jobId: string, status: JobStatus, notes?: string) => {
    const updateData: Record<string, unknown> = { status };
    if (notes) {
      if (status === 'not_interested' || status === 'rejected') {
        updateData.rejection_reason = notes;
      } else {
        updateData.notes = notes;
      }
    }

    const { error: err } = await supabase
      .from('jobs')
      .update(updateData)
      .eq('id', jobId);

    if (err) {
      setError(err.message);
      return false;
    }

    setRawJobs(prev => prev.map(j => j.id === jobId ? { ...j, status, ...(notes ? (status === 'not_interested' || status === 'rejected' ? { rejection_reason: notes } : { notes }) : {}) } : j));
    return true;
  }, []);

  const deleteJob = useCallback(async (jobId: string) => {
    return updateStatus(jobId, 'deleted');
  }, [updateStatus]);

  const counts = rawJobs.reduce<Record<string, number>>((acc, j) => {
    acc[j.status] = (acc[j.status] || 0) + 1;
    return acc;
  }, {});

  return {
    jobs,
    loading,
    error,
    counts,
    updateStatus,
    deleteJob,
    refetch: fetchJobs,
    sortMode,
    setSortMode,
    groupByCompany,
    setGroupByCompany,
    companyGroups,
  };
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
