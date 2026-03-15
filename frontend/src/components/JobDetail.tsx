import type { Job } from '../types';

interface JobDetailProps {
  job: Job;
  onAdvance: () => void;
  onSkip: () => void;
  onDelete: () => void;
}

export function JobDetail({ job, onAdvance, onSkip, onDelete }: JobDetailProps) {
  const nextStatus = getNextStatus(job.status);

  return (
    <div className="job-detail">
      <div className="job-detail-inner">
        <div className="detail-section">
          <h4>Description</h4>
          <p>{job.description_md || 'No description available.'}</p>
        </div>

        <div className="detail-section">
          <h4>Details</h4>
          {job.url && (
            <div className="detail-url" style={{ marginBottom: 8 }}>
              <a href={job.url} target="_blank" rel="noopener noreferrer">
                {job.url}
              </a>
            </div>
          )}
          <p>
            <strong>Source:</strong> {job.source || 'unknown'}<br />
            <strong>Score:</strong> {job.match_score ?? 'Not scored'}<br />
            <strong>Added:</strong> {new Date(job.created_at).toLocaleDateString()}
          </p>
          {job.gap_analysis_json && (
            <>
              <h4 style={{ marginTop: 16 }}>Gap Analysis</h4>
              <pre style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', whiteSpace: 'pre-wrap' }}>
                {JSON.stringify(job.gap_analysis_json, null, 2)}
              </pre>
            </>
          )}
        </div>

        <div className="detail-actions">
          {nextStatus && (
            <button className="action-btn review" onClick={onAdvance}>
              → Move to {nextStatus.replace('_', ' ')}
            </button>
          )}
          <button className="action-btn skip" onClick={onSkip}>
            Skip
          </button>
          <button className="action-btn delete" onClick={onDelete}>
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}

function getNextStatus(current: string): string | null {
  const flow: Record<string, string> = {
    scouted: 'to_review',
    to_review: 'applied',
    applied: 'interviewing',
    interviewing: 'offer',
  };
  return flow[current] || null;
}
