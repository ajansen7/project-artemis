import { useState } from 'react';
import type { Job, JobStatus } from '../types';
import { StatusBadge } from './StatusBadge';
import { JobDetail } from './JobDetail';

interface JobTableProps {
  jobs: Job[];
  loading: boolean;
  onUpdateStatus: (jobId: string, status: JobStatus, notes?: string) => void;
  onDelete: (jobId: string) => void;
  onUpdate: () => void;
}

export function JobTable({ jobs, loading, onUpdateStatus, onDelete, onUpdate }: JobTableProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (loading) {
    return (
      <div className="loading">
        <div className="loading-spinner" />
        Loading jobs...
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <div className="job-table">
        <div className="empty-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <h3>No jobs found</h3>
          <p>Run the scout to find some leads, or change the filter.</p>
        </div>
      </div>
    );
  }

  function getScoreClass(score: number | null): string {
    if (score === null) return 'none';
    if (score >= 70) return 'high';
    if (score >= 40) return 'medium';
    return 'low';
  }

  function getNextStatus(current: string): JobStatus | null {
    const flow: Record<string, JobStatus> = {
      scouted: 'to_review',
      to_review: 'applied',
      applied: 'recruiter_engaged',
      recruiter_engaged: 'interviewing',
      interviewing: 'offer',
    };
    return flow[current] || null;
  }

  return (
    <div className="job-table">
      <div className="job-table-header">
        <span>Company</span>
        <span>Title</span>
        <span>Status</span>
        <span>Score</span>
        <span>Source</span>
        <span>Added</span>
      </div>

      {jobs.map(job => {
        const isExpanded = expandedId === job.id;
        const companyName = job.companies?.name || 'Unknown';
        const nextStatus = getNextStatus(job.status);

        return (
          <div key={job.id}>
            <div
              className={`job-row ${isExpanded ? 'expanded' : ''}`}
              onClick={() => setExpandedId(isExpanded ? null : job.id)}
            >
              <span className="job-company">{companyName}</span>
              <span className="job-title">{job.title}</span>
              <StatusBadge status={job.status} />
              <span className={`job-score-pill ${getScoreClass(job.match_score)}`}>
                {job.match_score !== null ? job.match_score : 'N/A'}
              </span>
              <span className="job-source">{job.source || '—'}</span>
              <span className="job-date">
                {new Date(job.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              </span>
            </div>

            {isExpanded && (
              <JobDetail
                job={job}
                onAdvance={() => nextStatus && onUpdateStatus(job.id, nextStatus)}
                onSkip={() => onUpdateStatus(job.id, 'not_interested')}
                onDelete={() => onDelete(job.id)}
                onUpdate={onUpdate}
                onSetStatus={(status, notes) => onUpdateStatus(job.id, status, notes)}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
