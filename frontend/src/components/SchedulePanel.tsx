import { useState } from 'react';
import cronstrue from 'cronstrue';
import type { ScheduledJob, ScheduleStatus } from '../types';
import {
  SCHEDULE_STATUS_LABELS,
  AVAILABLE_SKILLS,
  CRON_PRESETS,
} from '../types';
import { useSchedules } from '../hooks/useSchedules';

// ─── Status Badge ────────────────────────────────────────────────

function ScheduleStatusBadge({ status }: { status: ScheduleStatus }) {
  if (!status) {
    return (
      <span className="engagement-status-badge engagement-status--skipped">
        Never
      </span>
    );
  }
  return (
    <span className={`engagement-status-badge engagement-status--${status}`}>
      {SCHEDULE_STATUS_LABELS[status] || status}
    </span>
  );
}

// ─── Skill Badge ────────────────────────────────────────────────

function SkillBadge({ skill }: { skill: string }) {
  const found = AVAILABLE_SKILLS.find(s => s.value === skill);
  return (
    <span className="engagement-action-badge">
      {found ? found.label : skill}
    </span>
  );
}

// ─── Cron Display ───────────────────────────────────────────────

function cronToHuman(expr: string): string {
  try {
    return cronstrue.toString(expr);
  } catch {
    return expr;
  }
}

// ─── Schedule Form ──────────────────────────────────────────────

function ScheduleForm({
  initial,
  onSave,
  onCancel,
}: {
  initial?: Partial<ScheduledJob>;
  onSave: (fields: Partial<ScheduledJob>) => void;
  onCancel: () => void;
}) {
  const [name, setName] = useState(initial?.name || '');
  const [skill, setSkill] = useState(initial?.skill || AVAILABLE_SKILLS[0].value);
  const [cronPreset, setCronPreset] = useState(() => {
    const match = CRON_PRESETS.find(p => p.value === initial?.cron_expr);
    return match ? match.value : '';
  });
  const [cronCustom, setCronCustom] = useState(initial?.cron_expr || '');
  const [notes, setNotes] = useState(initial?.notes || '');

  const isCustom = cronPreset === '';
  const cronExpr = isCustom ? cronCustom : cronPreset;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !cronExpr.trim()) return;
    onSave({
      name: name.trim(),
      skill,
      cron_expr: cronExpr.trim(),
      notes: notes.trim() || null,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="engagement-card-body" style={{ padding: '12px 16px' }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <input
          type="text"
          placeholder="Schedule name"
          value={name}
          onChange={e => setName(e.target.value)}
          style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', fontSize: '14px' }}
          required
        />
        <select
          value={skill}
          onChange={e => setSkill(e.target.value)}
          style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', fontSize: '14px' }}
        >
          {AVAILABLE_SKILLS.map(s => (
            <option key={s.value} value={s.value}>{s.label} ({s.value})</option>
          ))}
        </select>
        <select
          value={cronPreset}
          onChange={e => {
            setCronPreset(e.target.value);
            if (e.target.value !== '') setCronCustom(e.target.value);
          }}
          style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', fontSize: '14px' }}
        >
          {CRON_PRESETS.map(p => (
            <option key={p.label} value={p.value}>{p.label}</option>
          ))}
        </select>
        {isCustom && (
          <input
            type="text"
            placeholder="Cron expression (e.g. 0 9 * * 1-5)"
            value={cronCustom}
            onChange={e => setCronCustom(e.target.value)}
            style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', fontSize: '14px', fontFamily: 'monospace' }}
            required
          />
        )}
        <textarea
          placeholder="Notes (optional)"
          value={notes}
          onChange={e => setNotes(e.target.value)}
          rows={2}
          style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', fontSize: '14px', resize: 'vertical' }}
        />
        <div style={{ display: 'flex', gap: '8px' }}>
          <button type="submit" className="action-btn review">Save</button>
          <button type="button" className="action-btn skip" onClick={onCancel}>Cancel</button>
        </div>
      </div>
    </form>
  );
}

// ─── Schedule Card ──────────────────────────────────────────────

function ScheduleCard({
  schedule,
  onToggle,
  onUpdate,
  onDelete,
}: {
  schedule: ScheduledJob;
  onToggle: (id: string, enabled: boolean) => void;
  onUpdate: (id: string, fields: Partial<ScheduledJob>) => void;
  onDelete: (id: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [editing, setEditing] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [runNowMsg, setRunNowMsg] = useState<string | null>(null);

  const handleRunNow = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const response = await fetch(`http://localhost:8000/api/schedules/${schedule.id}/run-now`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      if (!response.ok) throw new Error('Request failed');
      setRunNowMsg('Triggered!');
    } catch {
      setRunNowMsg('Error triggering');
    }
    setTimeout(() => setRunNowMsg(null), 2000);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirmDelete) {
      onDelete(schedule.id);
    } else {
      setConfirmDelete(true);
      setTimeout(() => setConfirmDelete(false), 3000);
    }
  };

  const handleSaveEdit = (fields: Partial<ScheduledJob>) => {
    onUpdate(schedule.id, fields);
    setEditing(false);
  };

  return (
    <div className={`engagement-card ${expanded ? 'expanded' : ''}`}>
      <div className="engagement-card-header" onClick={() => setExpanded(e => !e)}>
        <div className="engagement-card-left">
          <div className="engagement-card-top">
            <strong>{schedule.name}</strong>
            <SkillBadge skill={schedule.skill} />
          </div>
          <span className="engagement-target" style={{ fontSize: '12px', opacity: 0.7 }}>
            {cronToHuman(schedule.cron_expr)}
          </span>
        </div>
        <div className="engagement-card-right">
          <label
            onClick={e => e.stopPropagation()}
            style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer', fontSize: '12px' }}
          >
            <input
              type="checkbox"
              checked={schedule.enabled}
              onChange={e => onToggle(schedule.id, e.target.checked)}
              style={{ accentColor: 'var(--accent)' }}
            />
            {schedule.enabled ? 'Enabled' : 'Disabled'}
          </label>
          <ScheduleStatusBadge status={schedule.last_status} />
          {schedule.last_run_at && (
            <span className="engagement-date">
              {new Date(schedule.last_run_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
            </span>
          )}
          <span className="expand-chevron">{expanded ? '\u25B2' : '\u25BC'}</span>
        </div>
      </div>

      {expanded && !editing && (
        <div className="engagement-card-body">
          {schedule.notes && (
            <div className="engagement-content-preview" style={{ opacity: 0.7, fontSize: '13px' }}>
              {schedule.notes}
            </div>
          )}
          {schedule.last_status === 'failed' && schedule.last_error && (
            <div style={{ background: 'rgba(239,68,68,0.1)', padding: '8px 12px', borderRadius: '6px', fontSize: '13px', color: '#ef4444', marginBottom: '8px' }}>
              <strong>Last error:</strong> {schedule.last_error}
            </div>
          )}
          <div className="engagement-card-actions">
            <button className="action-btn review" onClick={handleRunNow}>
              {runNowMsg || 'Run Now'}
            </button>
            <button className="action-btn review" onClick={e => { e.stopPropagation(); setEditing(true); }}>
              Edit
            </button>
            <button className="action-btn skip" onClick={handleDelete}>
              {confirmDelete ? 'Confirm Delete?' : 'Delete'}
            </button>
          </div>
        </div>
      )}

      {expanded && editing && (
        <ScheduleForm
          initial={schedule}
          onSave={handleSaveEdit}
          onCancel={() => setEditing(false)}
        />
      )}
    </div>
  );
}

// ─── Pipeline Summary ────────────────────────────────────────────

function ScheduleSummary({ counts }: { counts: Record<string, number> }) {
  const stages = [
    { key: 'total', label: 'Total' },
    { key: 'enabled', label: 'Enabled' },
    { key: 'disabled', label: 'Disabled' },
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

// ─── Schedule Panel ─────────────────────────────────────────────

export function SchedulePanel() {
  const { schedules, counts, loading, error, updateSchedule, createSchedule, deleteSchedule, toggleEnabled } = useSchedules();
  const [filter, setFilter] = useState<'all' | 'enabled' | 'disabled'>('all');
  const [showAdd, setShowAdd] = useState(false);

  const filtered = filter === 'all'
    ? schedules
    : filter === 'enabled'
      ? schedules.filter(s => s.enabled)
      : schedules.filter(s => !s.enabled);

  const handleCreate = async (fields: Partial<ScheduledJob>) => {
    const ok = await createSchedule({ ...fields, enabled: true });
    if (ok) setShowAdd(false);
  };

  if (loading) return (
    <div className="loading">
      <div className="loading-spinner" />
      Loading schedules...
    </div>
  );

  if (error) return <div className="empty-state"><p>Error: {error}</p></div>;

  if (schedules.length === 0 && !showAdd) return (
    <div className="empty-state">
      <h3>No scheduled jobs yet</h3>
      <p>Create automated schedules for your job search skills.</p>
      <button className="action-btn review" onClick={() => setShowAdd(true)} style={{ marginTop: '12px' }}>
        + Add Schedule
      </button>
      {showAdd && (
        <ScheduleForm onSave={handleCreate} onCancel={() => setShowAdd(false)} />
      )}
    </div>
  );

  return (
    <div className="networking-panel">
      <div className="networking-header">
        <div className="networking-stats">
          <span className="networking-stat">
            <strong>{counts.total}</strong> schedules
          </span>
          {counts.enabled > 0 && (
            <span className="networking-stat">
              <strong>{counts.enabled}</strong> active
            </span>
          )}
        </div>
        <button className="action-btn review" onClick={() => setShowAdd(s => !s)}>
          {showAdd ? 'Cancel' : '+ Add Schedule'}
        </button>
      </div>

      {showAdd && (
        <ScheduleForm onSave={handleCreate} onCancel={() => setShowAdd(false)} />
      )}

      <ScheduleSummary counts={counts} />

      <div className="status-filter" style={{ marginBottom: 0 }}>
        {(['all', 'enabled', 'disabled'] as const).map(s => (
          <button
            key={s}
            className={`filter-pill ${filter === s ? 'active' : ''}`}
            onClick={() => setFilter(s)}
          >
            {s === 'all' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      <div className="company-contact-group">
        <div className="contact-cards">
          {filtered.map(schedule => (
            <ScheduleCard
              key={schedule.id}
              schedule={schedule}
              onToggle={toggleEnabled}
              onUpdate={updateSchedule}
              onDelete={deleteSchedule}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
