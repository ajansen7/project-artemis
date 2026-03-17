import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import type { Job } from '../types';

interface ApplicationModalProps {
  isOpen: boolean;
  onClose: () => void;
  job: Job;
  onGenerationComplete: () => void;
  onSubmitted: () => void;
}

type Tab = 'resume' | 'cover_letter' | 'form_fills' | 'primer';

const TAB_LABELS: Record<Tab, string> = {
  resume: '📄 Resume',
  cover_letter: '✉️ Cover Letter',
  form_fills: '📋 Form Fills',
  primer: '📚 Primer',
};

export function ApplicationModal({ isOpen, onClose, job, onGenerationComplete, onSubmitted }: ApplicationModalProps) {
  const [activeTab, setActiveTab] = useState<Tab>('resume');
  const [generating, setGenerating] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [mode, setMode] = useState<'preview' | 'edit'>('preview');
  const [editContent, setEditContent] = useState('');
  const [saving, setSaving] = useState(false);

  const app = job.applications?.[0] as any;
  const hasResume = !!app?.resume_md;
  const hasCoverLetter = !!app?.cover_letter_md;
  const hasFormFills = !!app?.form_fills_md;
  const hasPrimer = !!app?.primer_md;
  const hasPdf = !!app?.resume_pdf_path;
  const isAlreadyApplied = job.status === 'applied';
  const canSubmit = hasResume && hasCoverLetter && !isAlreadyApplied;

  const getContent = (tab: Tab): string => {
    switch (tab) {
      case 'resume': return app?.resume_md || '';
      case 'cover_letter': return app?.cover_letter_md || '';
      case 'form_fills': return app?.form_fills_md || '';
      case 'primer': return app?.primer_md || '';
    }
  };

  const tabHasContent = (tab: Tab) => {
    switch (tab) {
      case 'resume': return hasResume;
      case 'cover_letter': return hasCoverLetter;
      case 'form_fills': return hasFormFills;
      case 'primer': return hasPrimer;
    }
  };

  useEffect(() => {
    setMode('preview');
    setEditContent(getContent(activeTab));
  }, [activeTab, job.applications]);

  if (!isOpen) return null;

  const handleGenerate = async () => {
    setGenerating(true);
    setStatusMsg(null);
    try {
      const res = await fetch('http://localhost:8000/api/generate-application', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: job.id, company_name: job.companies?.name || '' }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Generation failed');
      setStatusMsg('✅ Materials generated. Finder window opened — ready to apply.');
      setTimeout(onGenerationComplete, 1000);
    } catch (err: any) {
      setStatusMsg(`❌ ${err.message}`);
    } finally {
      setGenerating(false);
    }
  };

  const handleMarkSubmitted = async () => {
    setSubmitting(true);
    setStatusMsg(null);
    try {
      const res = await fetch('http://localhost:8000/api/mark-submitted', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: job.id }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed');
      setStatusMsg('✅ Marked submitted! Pipeline updated.');
      setTimeout(() => { onSubmitted(); onClose(); }, 800);
    } catch (err: any) {
      setStatusMsg(`❌ ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await fetch('http://localhost:8000/api/save-document', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: job.id, doc_type: activeTab, content: editContent }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || 'Save failed');
      setMode('preview');
      setStatusMsg('✅ Saved');
      onGenerationComplete();
    } catch (err: any) {
      setStatusMsg(`❌ ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const isEditableTab = activeTab === 'resume' || activeTab === 'cover_letter';
  const isDirty = editContent !== getContent(activeTab);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content"
        style={{ maxWidth: 900, height: '85vh', display: 'flex', flexDirection: 'column' }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="modal-header">
          <div>
            <h2 style={{ margin: 0 }}>{job.companies?.name || 'Company'}</h2>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: 2 }}>{job.title}</div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <button
              className="action-btn"
              style={{ backgroundColor: 'var(--primary)', color: 'white' }}
              onClick={handleGenerate}
              disabled={generating}
            >
              {generating ? '✨ Generating...' : hasResume ? '🔄 Re-generate' : '✨ Generate Application'}
            </button>
            <button className="close-btn" onClick={onClose}>✕</button>
          </div>
        </div>

        {/* Material status strip */}
        <div style={{
          padding: '0.45rem 1.25rem',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          gap: 20,
          fontSize: '0.78rem',
          backgroundColor: 'var(--bg-elevated)',
        }}>
          {(['resume', 'cover_letter', 'form_fills', 'primer'] as const).map(key => {
            const has = { resume: hasResume, cover_letter: hasCoverLetter, form_fills: hasFormFills, primer: hasPrimer }[key];
            const label = { resume: 'Resume', cover_letter: 'Cover Letter', form_fills: 'Form Fills', primer: 'Primer' }[key];
            return (
              <span key={key} style={{ color: has ? 'var(--success, #4caf78)' : 'var(--text-muted)' }}>
                {has ? '●' : '○'} {label}
              </span>
            );
          })}
          <span style={{ marginLeft: 12, color: hasPdf ? 'var(--success, #4caf78)' : 'var(--text-muted)' }}>
            {hasPdf ? '● PDF Ready' : '○ PDF'}
          </span>
          {hasPdf && (
            <span style={{ marginLeft: 'auto', color: 'var(--text-muted)', fontFamily: 'monospace', fontSize: '0.72rem' }}>
              {app.resume_pdf_path?.split('/').slice(-2).join('/')}
            </span>
          )}
        </div>

        {/* Tab bar */}
        <div style={{
          display: 'flex',
          borderBottom: '1px solid var(--border)',
          padding: '0 1.25rem',
          alignItems: 'center',
        }}>
          {(['resume', 'cover_letter', 'form_fills', 'primer'] as Tab[]).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                padding: '0.55rem 1rem',
                fontSize: '0.85rem',
                background: 'none',
                border: 'none',
                borderBottom: activeTab === tab ? '2px solid var(--primary)' : '2px solid transparent',
                color: activeTab === tab
                  ? 'var(--primary)'
                  : tabHasContent(tab) ? 'var(--text-secondary)' : 'var(--text-muted)',
                cursor: 'pointer',
                fontWeight: activeTab === tab ? 600 : 400,
                marginBottom: -1,
              }}
            >
              {TAB_LABELS[tab]}
            </button>
          ))}

          {/* Edit/save controls aligned to the right */}
          {isEditableTab && tabHasContent(activeTab) && (
            <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
              <button
                className="action-btn"
                style={{
                  padding: '0.3rem 0.7rem',
                  fontSize: '0.8rem',
                  backgroundColor: mode === 'edit' ? 'var(--primary)' : 'var(--bg-elevated)',
                  color: mode === 'edit' ? 'white' : 'var(--text-secondary)',
                }}
                onClick={() => setMode(m => m === 'edit' ? 'preview' : 'edit')}
              >
                {mode === 'edit' ? '👁 Preview' : '✏️ Edit'}
              </button>
              {mode === 'edit' && isDirty && (
                <button
                  className="action-btn"
                  style={{ padding: '0.3rem 0.7rem', fontSize: '0.8rem', backgroundColor: 'var(--success, #4caf78)', color: 'white' }}
                  onClick={handleSave}
                  disabled={saving}
                >
                  {saving ? 'Saving…' : '💾 Save'}
                </button>
              )}
            </div>
          )}
        </div>

        {/* Body */}
        <div
          className={mode === 'edit' ? undefined : 'modal-body'}
          style={{ flex: 1, overflow: 'auto', ...(mode === 'edit' ? {} : {}) }}
        >
          {tabHasContent(activeTab) ? (
            mode === 'edit' ? (
              <textarea
                value={editContent}
                onChange={e => setEditContent(e.target.value)}
                style={{
                  width: '100%',
                  height: '100%',
                  minHeight: 400,
                  padding: '1rem',
                  fontFamily: 'var(--font-mono, monospace)',
                  fontSize: '0.82rem',
                  lineHeight: 1.6,
                  border: 'none',
                  outline: 'none',
                  resize: 'none',
                  backgroundColor: 'var(--bg-base, #1a1a1a)',
                  color: 'var(--text-primary)',
                  boxSizing: 'border-box',
                }}
                spellCheck={false}
              />
            ) : (
              <div className="markdown-body" style={{ padding: 'var(--gap-lg)' }}>
                <ReactMarkdown>{getContent(activeTab)}</ReactMarkdown>
              </div>
            )
          ) : (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: 200,
              color: 'var(--text-muted)',
              gap: 8,
              fontSize: '0.9rem',
            }}>
              <span style={{ fontSize: '1.5rem' }}>○</span>
              <span>Not generated yet — click Generate Application above.</span>
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{
          padding: '0.75rem 1.25rem',
          borderTop: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 12,
          flexShrink: 0,
        }}>
          <span style={{
            fontSize: '0.85rem',
            color: statusMsg
              ? (statusMsg.startsWith('✅') ? 'var(--success, #4caf78)' : 'var(--danger, #f44)')
              : 'var(--text-muted)',
          }}>
            {statusMsg || (
              isAlreadyApplied
                ? '✅ Application already submitted'
                : canSubmit
                  ? 'Materials ready — apply, then confirm below.'
                  : 'Generate materials to unlock submission.'
            )}
          </span>
          <button
            className="action-btn"
            style={{
              backgroundColor: canSubmit ? 'var(--success, #4caf78)' : 'var(--bg-elevated)',
              color: canSubmit ? 'white' : 'var(--text-muted)',
              padding: '0.5rem 1.5rem',
              fontWeight: 600,
              opacity: canSubmit ? 1 : 0.5,
              cursor: canSubmit ? 'pointer' : 'not-allowed',
              flexShrink: 0,
            }}
            onClick={handleMarkSubmitted}
            disabled={!canSubmit || submitting}
          >
            {submitting ? 'Marking...' : isAlreadyApplied ? '✅ Submitted' : '✓ Mark Submitted'}
          </button>
        </div>
      </div>
    </div>
  );
}
