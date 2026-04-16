import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import type { BlogPost, BlogPostStatus } from '../types';
import { BLOG_STATUS_LABELS, BLOG_STATUS_ORDER } from '../types';
import { useBlogPosts } from '../hooks/useBlogPosts';
import { API_BASE, fetchWithAuth } from '../lib/api';

// ─── Blog Status Badge ──────────────────────────────────────────

function BlogStatusBadge({ status }: { status: BlogPostStatus }) {
  return (
    <span className={`blog-status-badge blog-status--${status}`}>
      {BLOG_STATUS_LABELS[status]}
    </span>
  );
}

// ─── Status Picker ────────────────────────────────────────────────

function StatusPicker({
  post,
  onUpdateStatus,
}: {
  post: BlogPost;
  onUpdateStatus: (id: string, status: BlogPostStatus) => void;
}) {
  const isPublished = post.status === 'published';

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Status</span>
      <select
        disabled={isPublished}
        value={post.status}
        style={{
          fontSize: '0.72rem',
          padding: '3px 6px',
          borderRadius: 4,
          border: '1px solid var(--border)',
          background: 'var(--bg-card)',
          color: isPublished ? 'var(--text-muted)' : 'var(--text)',
          cursor: isPublished ? 'not-allowed' : 'pointer',
        }}
        onChange={e => onUpdateStatus(post.id, e.target.value as BlogPostStatus)}
        onClick={e => e.stopPropagation()}
      >
        {BLOG_STATUS_ORDER.filter(s => s !== 'published').map(s => (
          <option key={s} value={s}>{BLOG_STATUS_LABELS[s]}</option>
        ))}
        <option value="published" disabled={!isPublished}>
          {BLOG_STATUS_LABELS['published']}
        </option>
      </select>
    </div>
  );
}

// ─── Draft Editor ────────────────────────────────────────────────

function DraftEditor({
  post,
  onSave,
  onGenerate,
  onProcessFeedback,
}: {
  post: BlogPost;
  onSave: (id: string, updates: { content?: string; notes?: string }) => Promise<boolean>;
  onGenerate: (id: string) => Promise<void>;
  onProcessFeedback: (id: string) => Promise<void>;
}) {
  const [tab, setTab] = useState<'edit' | 'preview'>('edit');
  const [content, setContent] = useState(post.content ?? '');
  const [notes, setNotes] = useState(post.notes ?? '');
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [processingFeedback, setProcessingFeedback] = useState(false);
  const [saveMsg, setSaveMsg] = useState('');

  // Sync if post updates externally (e.g. after generate completes)
  useEffect(() => {
    setContent(post.content ?? '');
    setNotes(post.notes ?? '');
    setDirty(false);
  }, [post.content, post.notes]);

  const handleSave = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setSaving(true);
    const ok = await onSave(post.id, { content, notes });
    setSaving(false);
    if (ok) {
      setDirty(false);
      setSaveMsg('Saved');
      setTimeout(() => setSaveMsg(''), 2000);
    }
  };

  const handleGenerate = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setGenerating(true);
    await onGenerate(post.id);
    setGenerating(false);
  };

  const handleProcessFeedback = async (e: React.MouseEvent) => {
    e.stopPropagation();
    // Auto-save any unsaved changes before dispatching
    if (dirty) {
      setSaving(true);
      await onSave(post.id, { content, notes });
      setSaving(false);
      setDirty(false);
    }
    setProcessingFeedback(true);
    await onProcessFeedback(post.id);
    setProcessingFeedback(false);
  };

  const hasContent = !!content.trim();

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation();
    await navigator.clipboard.writeText(content);
    setSaveMsg('Copied!');
    setTimeout(() => setSaveMsg(''), 2000);
  };

  return (
    <div style={{ marginTop: 12 }} onClick={e => e.stopPropagation()}>
      {/* Editor header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
        <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text)' }}>Draft</span>
        {hasContent && (
          <>
            <button
              className={`filter-pill ${tab === 'edit' ? 'active' : ''}`}
              style={{ padding: '2px 10px', fontSize: '0.7rem' }}
              onClick={() => setTab('edit')}
            >
              Edit
            </button>
            <button
              className={`filter-pill ${tab === 'preview' ? 'active' : ''}`}
              style={{ padding: '2px 10px', fontSize: '0.7rem' }}
              onClick={() => setTab('preview')}
            >
              Preview
            </button>
          </>
        )}
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 6, alignItems: 'center' }}>
          {saveMsg && (
            <span style={{ fontSize: '0.7rem', color: 'var(--success, #4caf50)' }}>{saveMsg}</span>
          )}
          {hasContent && dirty && (
            <button
              className="action-btn review"
              style={{ padding: '3px 10px', fontSize: '0.7rem' }}
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? 'Saving…' : 'Save'}
            </button>
          )}
          {hasContent && (
            <button
              className="action-btn"
              style={{ padding: '3px 10px', fontSize: '0.7rem' }}
              onClick={handleCopy}
              title="Copy markdown to clipboard"
            >
              Copy
            </button>
          )}
          {hasContent && (
            <button
              className="action-btn"
              style={{ padding: '3px 10px', fontSize: '0.7rem' }}
              onClick={handleProcessFeedback}
              disabled={processingFeedback}
              title="Send draft + revision notes to AI — extracts voice lessons, updates storybank"
            >
              {processingFeedback ? 'Processing…' : 'Process Revisions'}
            </button>
          )}
          {!hasContent && (
            <button
              className="action-btn"
              style={{ padding: '3px 10px', fontSize: '0.7rem' }}
              onClick={handleGenerate}
              disabled={generating}
            >
              {generating ? 'Generating…' : 'Generate Draft'}
            </button>
          )}
        </div>
      </div>

      {/* Content area */}
      {!hasContent ? (
        <div style={{
          padding: '20px',
          textAlign: 'center',
          fontSize: '0.78rem',
          color: 'var(--text-muted)',
          border: '1px dashed var(--border)',
          borderRadius: 6,
        }}>
          No draft yet. Click "Generate Draft" to write one, or start typing below.
          <textarea
            style={{
              display: 'block',
              width: '100%',
              marginTop: 12,
              minHeight: 120,
              padding: 8,
              fontSize: '0.78rem',
              fontFamily: 'monospace',
              border: '1px solid var(--border)',
              borderRadius: 4,
              background: 'var(--bg)',
              color: 'var(--text)',
              resize: 'vertical',
              boxSizing: 'border-box',
            }}
            placeholder="Or write your draft here…"
            value={content}
            onChange={e => { setContent(e.target.value); setDirty(true); }}
          />
          {content.trim() && (
            <button
              className="action-btn review"
              style={{ marginTop: 8, padding: '3px 12px', fontSize: '0.7rem' }}
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? 'Saving…' : 'Save Draft'}
            </button>
          )}
        </div>
      ) : tab === 'edit' ? (
        <textarea
          style={{
            width: '100%',
            minHeight: 280,
            padding: 10,
            fontSize: '0.78rem',
            fontFamily: 'monospace',
            border: '1px solid var(--border)',
            borderRadius: 6,
            background: 'var(--bg)',
            color: 'var(--text)',
            resize: 'vertical',
            boxSizing: 'border-box',
          }}
          value={content}
          onChange={e => { setContent(e.target.value); setDirty(true); }}
        />
      ) : (
        <div
          style={{
            padding: '12px 16px',
            border: '1px solid var(--border)',
            borderRadius: 6,
            background: 'var(--bg)',
            fontSize: '0.82rem',
            lineHeight: 1.7,
            maxHeight: 480,
            overflowY: 'auto',
          }}
          className="markdown-preview"
        >
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      )}

      {/* Revision Notes */}
      <div style={{ marginTop: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
          <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text)' }}>
            Revision Notes
          </span>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            — annotate what you want changed and why
          </span>
        </div>
        <textarea
          style={{
            width: '100%',
            minHeight: 100,
            padding: 10,
            fontSize: '0.78rem',
            fontFamily: 'inherit',
            border: '1px solid var(--border)',
            borderRadius: 6,
            background: 'var(--bg)',
            color: 'var(--text)',
            resize: 'vertical',
            boxSizing: 'border-box',
          }}
          placeholder={`Example:\n• Intro: too abstract, ground it in a specific moment\n• Para 3: the Artemis story is the right one but needs more detail on why it was hard\n• Tone overall: sounds a bit formal, loosen it up`}
          value={notes}
          onChange={e => { setNotes(e.target.value); setDirty(true); }}
        />
        {processingFeedback && (
          <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 4 }}>
            Running /blog-revise in background — the draft will update when done.
          </p>
        )}
      </div>
    </div>
  );
}

// ─── Blog Card ───────────────────────────────────────────────────

function BlogCard({
  post,
  onUpdateStatus,
  onUpdatePost,
}: {
  post: BlogPost;
  onUpdateStatus: (id: string, status: BlogPostStatus) => void;
  onUpdatePost: (id: string, updates: { content?: string; notes?: string }) => Promise<boolean>;
}) {
  const [expanded, setExpanded] = useState(false);
  const [generatingTask, setGeneratingTask] = useState<string | null>(null);
  const [feedbackTask, setFeedbackTask] = useState<string | null>(null);
  const [publishTask, setPublishTask] = useState<string | null>(null);

  const isPublished = post.status === 'published';

  const handleGenerate = async (id: string) => {
    const res = await fetchWithAuth(`${API_BASE}/api/blog-posts/${id}/generate`, { method: 'POST' });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to start generation' }));
      alert(err.detail);
      return;
    }
    const data = await res.json();
    setGeneratingTask(data.task_id);
    alert(`Draft generation started (task: ${data.task_id}). The content will appear once the skill completes.`);
  };

  const handleProcessFeedback = async (id: string) => {
    // Save current notes first, then dispatch
    const res = await fetchWithAuth(`${API_BASE}/api/blog-posts/${id}/process-feedback`, { method: 'POST' });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to start feedback processing' }));
      alert(err.detail);
      return;
    }
    const data = await res.json();
    setFeedbackTask(data.task_id);
  };

  const handlePublish = async (e: React.MouseEvent) => {
    e.stopPropagation();
    const res = await fetchWithAuth(`${API_BASE}/api/blog-posts/${post.id}/publish`, { method: 'POST' });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to queue publish task' }));
      alert(err.detail);
      return;
    }
    const data = await res.json();
    setPublishTask(data.task_id);
  };

  return (
    <div className={`blog-card ${expanded ? 'expanded' : ''}`}>
      <div className="blog-card-header" onClick={() => setExpanded(e => !e)}>
        <div className="blog-card-left">
          <span className="blog-card-title">{post.title}</span>
          {post.summary && (
            <span className="blog-card-summary">{post.summary}</span>
          )}
          {post.tags.length > 0 && (
            <div className="blog-card-tags">
              {post.tags.map(tag => (
                <span key={tag} className="blog-tag">{tag}</span>
              ))}
            </div>
          )}
        </div>
        <div className="blog-card-right">
          {post.platform && (
            <span className="engagement-platform-label">{post.platform}</span>
          )}
          <BlogStatusBadge status={post.status} />
          <span className="engagement-date">
            {new Date(post.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
          </span>
          <span className="expand-chevron">{expanded ? '\u25B2' : '\u25BC'}</span>
        </div>
      </div>

      {expanded && (
        <div className="blog-card-body">
          {/* Status picker + Publish button */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <StatusPicker post={post} onUpdateStatus={onUpdateStatus} />
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {(generatingTask || feedbackTask || publishTask) && (
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                  Task running in background…
                </span>
              )}
              {!isPublished && (
                <button
                  className="action-btn review"
                  style={{ padding: '3px 12px', fontSize: '0.72rem' }}
                  onClick={handlePublish}
                  disabled={!!publishTask}
                  title="Queue publish task — will open Chrome and post to LinkedIn (confirms via Telegram)"
                >
                  {publishTask ? 'Publishing…' : 'Publish'}
                </button>
              )}
            </div>
          </div>

          {/* Draft editor (hidden for published posts) */}
          {!isPublished ? (
            <DraftEditor
              post={post}
              onSave={onUpdatePost}
              onGenerate={handleGenerate}
              onProcessFeedback={handleProcessFeedback}
            />
          ) : (
            <>
              {post.published_url && (
                <div className="contact-section">
                  <h4>Published URL</h4>
                  <a href={post.published_url} target="_blank" rel="noreferrer">
                    {post.published_url}
                  </a>
                </div>
              )}
              {post.published_at && (
                <div className="contact-section">
                  <h4>Published</h4>
                  <p>{new Date(post.published_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</p>
                </div>
              )}
              {post.content && (
                <div className="contact-section">
                  <h4>Content</h4>
                  <div
                    style={{
                      padding: '10px 14px',
                      border: '1px solid var(--border)',
                      borderRadius: 6,
                      background: 'var(--bg)',
                      fontSize: '0.82rem',
                      lineHeight: 1.7,
                      maxHeight: 320,
                      overflowY: 'auto',
                    }}
                    className="markdown-preview"
                  >
                    <ReactMarkdown>{post.content}</ReactMarkdown>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Pipeline Summary ────────────────────────────────────────────

function BlogSummary({ counts }: { counts: Record<string, number> }) {
  const stages = [
    { key: 'ideas', label: 'Ideas' },
    { key: 'drafts', label: 'Drafts' },
    { key: 'inReview', label: 'In Review' },
    { key: 'published', label: 'Published' },
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

// ─── Blog Panel ──────────────────────────────────────────────────

export function BlogPanel() {
  const { posts, counts, loading, error, updateStatus, updatePost } = useBlogPosts();
  const [filter, setFilter] = useState<BlogPostStatus | 'all'>('all');

  const filtered = filter === 'all' ? posts : posts.filter(p => p.status === filter);

  if (loading) return (
    <div className="loading">
      <div className="loading-spinner" />
      Loading blog posts...
    </div>
  );

  if (error) return <div className="empty-state"><p>Error: {error}</p></div>;

  if (posts.length === 0) return (
    <div className="empty-state">
      <h3>No blog posts yet</h3>
      <p>Use the Blogger skill to generate content ideas and drafts.</p>
    </div>
  );

  return (
    <div className="networking-panel">
      <div className="networking-header">
        <div className="networking-stats">
          <span className="networking-stat">
            <strong>{counts.total}</strong> posts
          </span>
          {counts.published > 0 && (
            <span className="networking-stat">
              <strong>{counts.published}</strong> published
            </span>
          )}
        </div>
      </div>

      <BlogSummary counts={counts} />

      <div className="status-filter" style={{ marginBottom: 0 }}>
        {(['all', 'idea', 'draft', 'review', 'published'] as const).map(s => (
          <button
            key={s}
            className={`filter-pill ${filter === s ? 'active' : ''}`}
            onClick={() => setFilter(s)}
          >
            {s === 'all' ? 'All' : BLOG_STATUS_LABELS[s]}
          </button>
        ))}
      </div>

      <div className="company-contact-group">
        <div className="contact-cards">
          {filtered.map(post => (
            <BlogCard
              key={post.id}
              post={post}
              onUpdateStatus={updateStatus}
              onUpdatePost={updatePost}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
