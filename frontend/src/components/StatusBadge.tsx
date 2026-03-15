import type { JobStatus } from '../types';
import { STATUS_LABELS } from '../types';

interface StatusBadgeProps {
  status: JobStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <span className={`status-badge ${status}`}>
      {STATUS_LABELS[status] || status}
    </span>
  );
}
