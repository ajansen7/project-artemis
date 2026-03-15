import type { JobStatus } from '../types';
import { STATUS_ORDER, STATUS_LABELS } from '../types';

interface StatusFilterProps {
  active: JobStatus | 'all';
  counts: Record<string, number>;
  onChange: (status: JobStatus | 'all') => void;
}

export function StatusFilter({ active, counts, onChange }: StatusFilterProps) {
  const totalActive = Object.entries(counts)
    .filter(([k]) => k !== 'deleted')
    .reduce((sum, [, v]) => sum + v, 0);

  return (
    <div className="status-filter">
      <button
        className={`filter-pill ${active === 'all' ? 'active' : ''}`}
        onClick={() => onChange('all')}
      >
        All<span className="pill-count">{totalActive}</span>
      </button>
      {STATUS_ORDER.map(s => (
        <button
          key={s}
          className={`filter-pill ${active === s ? 'active' : ''}`}
          onClick={() => onChange(s)}
        >
          {STATUS_LABELS[s]}<span className="pill-count">{counts[s] || 0}</span>
        </button>
      ))}
      {(counts['not_interested'] || 0) > 0 && (
        <button
          className={`filter-pill ${active === 'not_interested' ? 'active' : ''}`}
          onClick={() => onChange('not_interested')}
        >
          Skipped<span className="pill-count">{counts['not_interested']}</span>
        </button>
      )}
    </div>
  );
}
