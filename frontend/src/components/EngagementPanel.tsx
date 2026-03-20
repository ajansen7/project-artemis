import { useState } from 'react';
import type { EngagementEntry, EngagementStatus } from '../types';
import {
  ENGAGEMENT_STATUS_LABELS,
  ENGAGEMENT_ACTION_LABELS,
  ENGAGEMENT_PLATFORM_LABELS,
} from '../types';
import { useEngagement } from '../hooks/useEngagement';

// ─── Status Badge ────────────────────────────────────────────────

function EngagementStatusBadge({ status }: { status: EngagementStatus }) {
  return (
    <span className={`engagement-status-badge engagement-status--${status}`}>
      {ENGAGEMENT_STATUS_LABELS[status]}
    </span>
  );
}

// ─── Action Badge ────────────────────────────────────────────────

function ActionBadge({ action }: { action: string }) {
  return (
    <span className="engagement-action-badge">
      {ENGAGEMENT_ACTION_LABELS[action as keyof typeof ENGAGEMENT_ACTION_LABELS] || action}
    </span>
  );
}

// ─── Engagement Card ─────────────────────────────────────────────

function EngagementCard({
  entry,
  onUpdateStatus,
}: {
  entry: EngagementEntry;
  onUpdateStatus: (id: string, status: EngagementStatus) => void;
}) {
  const [expanded, setExpanded] = useState(false);

  const nextStatus: Partial<Record<EngagementStatus, EngagementStatus>> = {
    drafted: 'approved',
    approved: 'posted',
  };

  const next = nextStatus[entry.status];

  return (
    <div className={`engagement-card ${expanded ? 'expanded' : ''}`}>
      <div className="engagement-card-header" onClick={() => setExpanded(e => !e)}>
        <div className="engagement-card-left">
          <div className="engagement-card-top">
            <span className="engagement-platform-label">
              {ENGAGEMENT_PLATFORM_LABELS[entry.platform] || entry.platform}
            </span>
            <ActionBadge action={entry.action_type} />
          </div>
          {entry.target_person && (
            <span className="engagement-target">{entry.target_person}</span>
          )}
        </div>
        <div className="engagement-card-right">
          <EngagementStatusBadge status={entry.status} />
          <span className="engagement-date">
            {new Date(entry.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
          </span>
          <span className="expand-chevron">{expanded ? '\u25B2' : '\u25BC'}</span>
        </div>
      </div>

      {expanded && (
        <div className="engagement-card-body">
          {entry.content && (
            <div className="engagement-content-preview">
              <pre className="outreach-message">{entry.content}</pre>
            </div>
          )}
          {entry.target_url && (
            <div className="engagement-url">
              <a href={entry.target_url} target="_blank" rel="noreferrer">
                {entry.target_url}
              </a>
            </div>
          )}
          <div className="engagement-card-actions">
            {next && (
              <button
                className="action-btn review"
                onClick={e => { e.stopPropagation(); onUpdateStatus(entry.id, next); }}
              >
                Mark {ENGAGEMENT_STATUS_LABELS[next]}
              </button>
            )}
            {entry.status === 'drafted' && (
              <button
                className="action-btn skip"
                onClick={e => { e.stopPropagation(); onUpdateStatus(entry.id, 'skipped'); }}
              >
                Skip
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Pipeline Summary ────────────────────────────────────────────

function EngagementSummary({ counts }: { counts: Record<string, number> }) {
  const stages = [
    { key: 'drafted', label: 'Drafted' },
    { key: 'approved', label: 'Approved' },
    { key: 'posted', label: 'Posted' },
  ];

  return (
    <div className="networking-pipeline-summary">
      {stages.map(s => (
        <div key={s.key} className="pipeline-stage">
          <span className={`pipeline-stage-count ${(counts[s.key] || 0) > 0 ? 'has-contacts' : ''}`}>
            {counts[s.key] || 0}
          </span>
          <span className="pipeline-stage-label">{s.label}</span>
        </div>
      ))}
    </div>
  );
}

// ─── Engagement Panel ────────────────────────────────────────────

export function EngagementPanel() {
  const { entries, counts, loading, error, updateStatus } = useEngagement();
  const [filter, setFilter] = useState<EngagementStatus | 'all'>('all');

  const filtered = filter === 'all' ? entries : entries.filter(e => e.status === filter);

  if (loading) return (
    <div className="loading">
      <div className="loading-spinner" />
      Loading engagement log...
    </div>
  );

  if (error) return <div className="empty-state"><p>Error: {error}</p></div>;

  if (entries.length === 0) return (
    <div className="empty-state">
      <h3>No engagement activity yet</h3>
      <p>Use the LinkedIn or Blogger skills to generate engagement drafts.</p>
    </div>
  );

  return (
    <div className="networking-panel">
      <div className="networking-header">
        <div className="networking-stats">
          <span className="networking-stat">
            <strong>{counts.total}</strong> entries
          </span>
          {counts.drafted > 0 && (
            <span className="networking-stat">
              <strong>{counts.drafted}</strong> pending review
            </span>
          )}
        </div>
      </div>

      <EngagementSummary counts={counts} />

      <div className="status-filter" style={{ marginBottom: 0 }}>
        {(['all', 'drafted', 'approved', 'posted', 'skipped'] as const).map(s => (
          <button
            key={s}
            className={`filter-pill ${filter === s ? 'active' : ''}`}
            onClick={() => setFilter(s)}
          >
            {s === 'all' ? 'All' : ENGAGEMENT_STATUS_LABELS[s]}
          </button>
        ))}
      </div>

      <div className="company-contact-group">
        <div className="contact-cards">
          {filtered.map(entry => (
            <EngagementCard
              key={entry.id}
              entry={entry}
              onUpdateStatus={updateStatus}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
