import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { API_BASE, fetchWithAuth } from '../lib/api';

type DocType = 'resume' | 'cover_letter' | 'primer';

interface MarkdownModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  content: string;
  // When provided, enables save + teach-agent actions
  jobId?: string;
  docType?: DocType;
  onSaved?: (newContent: string) => void;
}

export function MarkdownModal({
  isOpen, onClose, title, content,
  jobId, docType, onSaved,
}: MarkdownModalProps) {
  const [mode, setMode] = useState<'preview' | 'edit'>('preview');
  const [editContent, setEditContent] = useState(content);
  const [saving, setSaving] = useState(false);
  const [teaching, setTeaching] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [originalContent, setOriginalContent] = useState(content);

  // Reset state when a new document is opened
  useEffect(() => {
    setMode('preview');
    setEditContent(content);
    setOriginalContent(content);
    setStatusMsg(null);
  }, [content, isOpen]);

  if (!isOpen) return null;

  const isEditable = !!(jobId && docType);
  const isDirty = editContent !== originalContent;

  const handleSave = async () => {
    if (!jobId || !docType) return;
    setSaving(true);
    setStatusMsg(null);
    try {
      const res = await fetchWithAuth(`${API_BASE}/api/save-document`, {
        method: 'POST',
        body: JSON.stringify({ job_id: jobId, doc_type: docType, content: editContent }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Save failed');
      setOriginalContent(editContent);
      setMode('preview');
      setStatusMsg('✅ Saved');
      onSaved?.(editContent);
    } catch (err: any) {
      setStatusMsg(`❌ ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleTeachAgent = async () => {
    if (!jobId || !docType || !isDirty && editContent === originalContent) return;
    // Use the last-saved content as "edited" and the original as baseline
    const edited = mode === 'edit' ? editContent : originalContent;
    setTeaching(true);
    setStatusMsg(null);
    try {
      const res = await fetchWithAuth(`${API_BASE}/api/learn-from-edit`, {
        method: 'POST',
        body: JSON.stringify({
          job_id: jobId,
          doc_type: docType,
          original_content: content,   // the pre-edit version
          edited_content: edited,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Learn failed');
      setStatusMsg('🧠 Agent updated from your corrections');
    } catch (err: any) {
      setStatusMsg(`❌ ${err.message}`);
    } finally {
      setTeaching(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" style={{ maxWidth: 780 }} onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div className="modal-header">
          <h2>{title}</h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {isEditable && (
              <>
                <button
                  className="action-btn"
                  style={{
                    padding: '0.3rem 0.7rem',
                    fontSize: '0.8rem',
                    backgroundColor: mode === 'edit' ? 'var(--primary)' : 'var(--bg-elevated)',
                    color: mode === 'edit' ? 'white' : 'var(--text-secondary)',
                  }}
                  onClick={() => setMode(mode === 'edit' ? 'preview' : 'edit')}
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
                {/* Teach agent — only for resume/cover letter, only after a save has happened */}
                {docType !== 'primer' && originalContent !== content && (
                  <button
                    className="action-btn"
                    style={{ padding: '0.3rem 0.7rem', fontSize: '0.8rem', backgroundColor: 'var(--blue-dim)', color: 'var(--blue)' }}
                    onClick={handleTeachAgent}
                    disabled={teaching}
                    title="Extract reusable lessons from your edits so future drafts don't repeat the same mistakes"
                  >
                    {teaching ? 'Extracting lessons…' : '🧠 Extract Lessons'}
                  </button>
                )}
              </>
            )}
            <button className="close-btn" onClick={onClose}>✕</button>
          </div>
        </div>

        {/* Body */}
        <div className="modal-body" style={mode === 'edit' ? { padding: 0 } : undefined}>
          {mode === 'edit' ? (
            <textarea
              value={editContent}
              onChange={e => setEditContent(e.target.value)}
              style={{
                width: '100%',
                minHeight: 520,
                padding: '1rem',
                fontFamily: 'var(--font-mono, monospace)',
                fontSize: '0.82rem',
                lineHeight: 1.6,
                border: 'none',
                outline: 'none',
                resize: 'vertical',
                backgroundColor: 'var(--bg-base, #1a1a1a)',
                color: 'var(--text-primary)',
                boxSizing: 'border-box',
              }}
              spellCheck={false}
            />
          ) : (
            <div className="markdown-body">
              <ReactMarkdown>{editContent}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* Status bar */}
        {statusMsg && (
          <div style={{
            padding: '0.5rem 1rem',
            fontSize: '0.82rem',
            borderTop: '1px solid var(--border)',
            color: statusMsg.startsWith('✅') || statusMsg.startsWith('🧠')
              ? 'var(--success, #4caf78)'
              : 'var(--danger, #f44)',
          }}>
            {statusMsg}
          </div>
        )}
      </div>
    </div>
  );
}
