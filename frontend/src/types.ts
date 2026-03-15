export interface Job {
  id: string;
  company_id: string | null;
  title: string;
  url: string | null;
  description_md: string | null;
  status: JobStatus;
  match_score: number | null;
  gap_analysis_json: Record<string, unknown> | null;
  source: string | null;
  rejection_reason: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  companies: { name: string; domain: string | null; careers_url: string | null } | null;
}

export type JobStatus =
  | 'scouted'
  | 'to_review'
  | 'applied'
  | 'interviewing'
  | 'offer'
  | 'not_interested'
  | 'rejected'
  | 'deleted';

export interface Company {
  id: string;
  name: string;
  domain: string | null;
  careers_url: string | null;
  is_target: boolean;
  why_target: string | null;
  scout_priority: 'high' | 'medium' | 'low';
  last_scouted_at: string | null;
}

export const STATUS_ORDER: JobStatus[] = [
  'scouted',
  'to_review',
  'applied',
  'interviewing',
  'offer',
];

export const STATUS_LABELS: Record<JobStatus, string> = {
  scouted: 'Scouted',
  to_review: 'To Review',
  applied: 'Applied',
  interviewing: 'Interviewing',
  offer: 'Offer',
  not_interested: 'Skipped',
  rejected: 'Rejected',
  deleted: 'Deleted',
};
