import type { Company } from '../types';

interface CompanySidebarProps {
  companies: Company[];
  loading: boolean;
}

export function CompanySidebar({ companies, loading }: CompanySidebarProps) {
  if (loading) {
    return (
      <aside className="sidebar">
        <div className="sidebar-card">
          <div className="sidebar-title">Target Companies</div>
          <div className="loading" style={{ padding: 16 }}>
            <div className="loading-spinner" />
          </div>
        </div>
      </aside>
    );
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-card">
        <div className="sidebar-title">Target Companies</div>
        {companies.length === 0 ? (
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            No target companies yet. Run the scout to discover some.
          </p>
        ) : (
          companies.map(c => (
            <div key={c.id} className="company-item">
              <div>
                <div className="company-name">{c.name}</div>
                {c.why_target && (
                  <div className="company-why">{c.why_target.slice(0, 60)}{c.why_target.length > 60 ? '…' : ''}</div>
                )}
              </div>
              <span className={`priority-badge ${c.scout_priority}`}>
                {c.scout_priority}
              </span>
            </div>
          ))
        )}
      </div>
    </aside>
  );
}
