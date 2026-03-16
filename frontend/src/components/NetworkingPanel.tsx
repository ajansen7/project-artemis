import { useState } from 'react';
import type { Contact, OutreachStatus, InteractionType } from '../types';
import {
  OUTREACH_STATUS_LABELS,
  OUTREACH_STATUS_ORDER,
  INTERACTION_TYPE_LABELS,
} from '../types';
import { useContacts } from '../hooks/useContacts';

// ─── Outreach Status Badge ────────────────────────────────────────

function OutreachBadge({ status }: { status: OutreachStatus }) {
  return (
    <span className={`outreach-badge outreach-badge--${status.replace('_', '-')}`}>
      {OUTREACH_STATUS_LABELS[status]}
    </span>
  );
}

// ─── Priority Badge ───────────────────────────────────────────────

function PriorityBadge({ priority }: { priority: string | null }) {
  if (!priority) return null;
  return <span className={`priority-badge ${priority}`}>{priority}</span>;
}

// ─── Status Stepper ───────────────────────────────────────────────

const STEPPER_STATUSES: OutreachStatus[] = ['identified', 'draft_ready', 'sent', 'connected', 'responded', 'meeting_scheduled', 'warm'];

function StatusStepper({
  current,
  onAdvance,
}: {
  current: OutreachStatus;
  onAdvance: (status: OutreachStatus) => void;
}) {
  const currentIdx = STEPPER_STATUSES.indexOf(current);
  const next = STEPPER_STATUSES[currentIdx + 1];

  return (
    <div className="status-stepper">
      {STEPPER_STATUSES.map((s, i) => (
        <div
          key={s}
          className={`stepper-dot ${i < currentIdx ? 'done' : ''} ${i === currentIdx ? 'active' : ''}`}
          title={OUTREACH_STATUS_LABELS[s]}
        />
      ))}
      {next && (
        <button
          className="action-btn review"
          style={{ marginLeft: 'auto', padding: '4px 10px', fontSize: '0.72rem' }}
          onClick={() => onAdvance(next)}
        >
          → {OUTREACH_STATUS_LABELS[next]}
        </button>
      )}
    </div>
  );
}

// ─── Log Interaction Form ─────────────────────────────────────────

const INTERACTION_OPTIONS: InteractionType[] = [
  'connection_request',
  'message_sent',
  'response_received',
  'meeting_scheduled',
  'referral_requested',
  'referral_given',
  'note',
];

function LogInteractionForm({
  onSubmit,
  onCancel,
}: {
  onSubmit: (type: InteractionType, notes: string) => void;
  onCancel: () => void;
}) {
  const [type, setType] = useState<InteractionType>('note');
  const [notes, setNotes] = useState('');

  return (
    <div className="log-interaction-form">
      <select
        value={type}
        onChange={e => setType(e.target.value as InteractionType)}
        className="interaction-select"
      >
        {INTERACTION_OPTIONS.map(t => (
          <option key={t} value={t}>{INTERACTION_TYPE_LABELS[t]}</option>
        ))}
      </select>
      <textarea
        value={notes}
        onChange={e => setNotes(e.target.value)}
        placeholder="Notes (optional)..."
        className="interaction-notes"
        rows={2}
      />
      <div style={{ display: 'flex', gap: 8 }}>
        <button className="action-btn review" onClick={() => onSubmit(type, notes)}>
          Log
        </button>
        <button className="action-btn skip" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </div>
  );
}

// ─── Contact Card ─────────────────────────────────────────────────

function ContactCard({
  contact,
  onStatusAdvance,
  onLogInteraction,
}: {
  contact: Contact;
  onStatusAdvance: (contactId: string, status: OutreachStatus) => void;
  onLogInteraction: (contactId: string, type: InteractionType, notes: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [showLogForm, setShowLogForm] = useState(false);

  const linkedRoles = contact.contact_job_links
    ?.map(l => l.jobs?.title)
    .filter(Boolean)
    .join(', ');

  return (
    <div className={`contact-card ${expanded ? 'expanded' : ''}`}>
      <div className="contact-card-header" onClick={() => setExpanded(e => !e)}>
        <div className="contact-card-left">
          <div className="contact-name-row">
            <span className="contact-name">{contact.name}</span>
            {contact.is_personal_connection && (
              <span className="personal-flag" title="Personal connection">★</span>
            )}
          </div>
          <span className="contact-title">{contact.title}</span>
          {linkedRoles && (
            <span className="contact-linked-role">Re: {linkedRoles}</span>
          )}
        </div>
        <div className="contact-card-right">
          <PriorityBadge priority={contact.priority} />
          <OutreachBadge status={contact.outreach_status} />
          <span className="expand-chevron">{expanded ? '▲' : '▼'}</span>
        </div>
      </div>

      {expanded && (
        <div className="contact-card-body">
          <StatusStepper
            current={contact.outreach_status}
            onAdvance={status => onStatusAdvance(contact.id, status)}
          />

          {contact.linkedin_url && (
            <div className="contact-linkedin">
              <a href={`https://${contact.linkedin_url.replace(/^https?:\/\//, '')}`} target="_blank" rel="noreferrer">
                LinkedIn →
              </a>
            </div>
          )}

          {contact.mutual_connection_notes && (
            <div className="contact-section">
              <h4>Connection Context</h4>
              <p>{contact.mutual_connection_notes}</p>
            </div>
          )}

          {contact.outreach_message_md && (
            <div className="contact-section">
              <h4>Outreach Message</h4>
              <pre className="outreach-message">{contact.outreach_message_md}</pre>
            </div>
          )}

          {contact.notes && (
            <div className="contact-section">
              <h4>Notes</h4>
              <p>{contact.notes}</p>
            </div>
          )}

          {(contact.contact_interactions?.length ?? 0) > 0 && (
            <div className="contact-section">
              <h4>Interaction History</h4>
              <div className="interaction-log">
                {contact.contact_interactions!.map(i => (
                  <div key={i.id} className="interaction-item">
                    <span className="interaction-type">{INTERACTION_TYPE_LABELS[i.interaction_type]}</span>
                    <span className="interaction-date">
                      {new Date(i.occurred_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    </span>
                    {i.notes && <span className="interaction-notes-text">{i.notes}</span>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {showLogForm ? (
            <LogInteractionForm
              onSubmit={(type, notes) => {
                onLogInteraction(contact.id, type, notes);
                setShowLogForm(false);
              }}
              onCancel={() => setShowLogForm(false)}
            />
          ) : (
            <button
              className="action-btn skip"
              style={{ marginTop: 8, fontSize: '0.75rem' }}
              onClick={e => { e.stopPropagation(); setShowLogForm(true); }}
            >
              + Log Interaction
            </button>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Pipeline Summary Bar ─────────────────────────────────────────

function PipelineSummary({ contacts }: { contacts: Contact[] }) {
  const counts = OUTREACH_STATUS_ORDER.reduce<Record<string, number>>((acc, s) => {
    acc[s] = contacts.filter(c => c.outreach_status === s).length;
    return acc;
  }, {});

  return (
    <div className="networking-pipeline-summary">
      {OUTREACH_STATUS_ORDER.map(s => (
        <div key={s} className="pipeline-stage">
          <span className={`pipeline-stage-count ${counts[s] > 0 ? 'has-contacts' : ''}`}>{counts[s]}</span>
          <span className="pipeline-stage-label">{OUTREACH_STATUS_LABELS[s]}</span>
        </div>
      ))}
    </div>
  );
}

// ─── Networking Panel ─────────────────────────────────────────────

export function NetworkingPanel() {
  const { byCompany, contacts, counts, loading, error, updateOutreachStatus, logInteraction } = useContacts();

  if (loading) return (
    <div className="loading">
      <div className="loading-spinner" />
      Loading contacts...
    </div>
  );

  if (error) return <div className="empty-state"><p>Error: {error}</p></div>;

  if (contacts.length === 0) return (
    <div className="empty-state">
      <h3>No contacts yet</h3>
      <p>Run Artemis networking to identify contacts for your target roles.</p>
    </div>
  );

  return (
    <div className="networking-panel">
      <div className="networking-header">
        <div className="networking-stats">
          <span className="networking-stat">
            <strong>{counts.total}</strong> contacts
          </span>
          {counts.personal > 0 && (
            <span className="networking-stat personal">
              <strong>{counts.personal}</strong> personal connections ★
            </span>
          )}
          <span className="networking-stat">
            <strong>{counts.active}</strong> active
          </span>
        </div>
      </div>

      <PipelineSummary contacts={contacts} />

      {Object.entries(byCompany).map(([company, companyContacts]) => (
        <div key={company} className="company-contact-group">
          <div className="company-contact-header">
            <span className="company-contact-name">{company}</span>
            <span className="company-contact-count">{companyContacts.length}</span>
          </div>
          <div className="contact-cards">
            {companyContacts.map(c => (
              <ContactCard
                key={c.id}
                contact={c}
                onStatusAdvance={updateOutreachStatus}
                onLogInteraction={logInteraction}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
