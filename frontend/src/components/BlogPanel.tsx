import { useState } from 'react';
import type { BlogPost, BlogPostStatus } from '../types';
import { BLOG_STATUS_LABELS, BLOG_STATUS_ORDER } from '../types';
import { useBlogPosts } from '../hooks/useBlogPosts';
import { MarkdownModal } from './MarkdownModal';

// ─── Blog Status Badge ──────────────────────────────────────────

function BlogStatusBadge({ status }: { status: BlogPostStatus }) {
  return (
    <span className={`blog-status-badge blog-status--${status}`}>
      {BLOG_STATUS_LABELS[status]}
    </span>
  );
}

// ─── Blog Card ───────────────────────────────────────────────────

function BlogCard({
  post,
  onUpdateStatus,
}: {
  post: BlogPost;
  onUpdateStatus: (id: string, status: BlogPostStatus) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalContent, setModalContent] = useState('');
  const [loadingContent, setLoadingContent] = useState(false);

  const currentIdx = BLOG_STATUS_ORDER.indexOf(post.status);
  const next = BLOG_STATUS_ORDER[currentIdx + 1] || null;

  const openPost = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setLoadingContent(true);
    try {
      const res = await fetch(`http://localhost:8000/api/blog-post-content/${post.id}`);
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to load post');
      }
      const data = await res.json();
      setModalContent(data.content);
      setModalOpen(true);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoadingContent(false);
    }
  };

  return (
    <>
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
            {/* Status stepper */}
            <div className="status-stepper">
              {BLOG_STATUS_ORDER.map((s, i) => (
                <div
                  key={s}
                  className={`stepper-dot ${i < currentIdx ? 'done' : ''} ${i === currentIdx ? 'active' : ''}`}
                  title={BLOG_STATUS_LABELS[s]}
                />
              ))}
              <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
                {post.draft_path && (
                  <button
                    className="action-btn"
                    style={{ padding: '4px 10px', fontSize: '0.72rem' }}
                    onClick={openPost}
                    disabled={loadingContent}
                  >
                    {loadingContent ? 'Loading…' : 'Read Post'}
                  </button>
                )}
                {next && (
                  <button
                    className="action-btn review"
                    style={{ padding: '4px 10px', fontSize: '0.72rem' }}
                    onClick={e => { e.stopPropagation(); onUpdateStatus(post.id, next); }}
                  >
                    Move to {BLOG_STATUS_LABELS[next]}
                  </button>
                )}
              </div>
            </div>

            {post.notes && (
              <div className="contact-section">
                <h4>Notes</h4>
                <p>{post.notes}</p>
              </div>
            )}

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
          </div>
        )}
      </div>

      <MarkdownModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={post.title}
        content={modalContent}
      />
    </>
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
  const { posts, counts, loading, error, updateStatus } = useBlogPosts();
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
            />
          ))}
        </div>
      </div>
    </div>
  );
}
