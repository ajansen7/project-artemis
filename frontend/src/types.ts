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
  applications?: { resume_md: string | null; cover_letter_md: string | null; primer_md: string | null; form_fills_md: string | null; resume_pdf_path: string | null; submitted_at: string | null }[];
}

export type JobStatus =
  | 'scouted'
  | 'to_review'
  | 'applied'
  | 'recruiter_engaged'
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
  'recruiter_engaged',
  'interviewing',
  'offer',
];

// ─── Networking Types ────────────────────────────────────────────

export type OutreachStatus =
  | 'identified'
  | 'draft_ready'
  | 'sent'
  | 'connected'
  | 'responded'
  | 'meeting_scheduled'
  | 'warm';

export type ContactPriority = 'high' | 'medium' | 'low';

export type InteractionType =
  | 'connection_request'
  | 'message_sent'
  | 'response_received'
  | 'meeting_scheduled'
  | 'referral_requested'
  | 'referral_given'
  | 'note';

export interface ContactInteraction {
  id: string;
  contact_id: string;
  interaction_type: InteractionType;
  notes: string | null;
  occurred_at: string;
  created_at: string;
}

export interface Contact {
  id: string;
  company_id: string | null;
  name: string;
  title: string | null;
  linkedin_url: string | null;
  email: string | null;
  relationship_type: string;
  notes: string | null;
  last_contacted_at: string | null;
  outreach_status: OutreachStatus;
  priority: ContactPriority | null;
  source: string;
  outreach_message_md: string | null;
  is_personal_connection: boolean;
  mutual_connection_notes: string | null;
  created_at: string;
  updated_at: string;
  companies: { name: string } | null;
  contact_job_links?: { job_id: string; jobs?: { title: string; companies?: { name: string } | null } | null }[];
  contact_interactions?: ContactInteraction[];
}

export const OUTREACH_STATUS_ORDER: OutreachStatus[] = [
  'identified',
  'draft_ready',
  'sent',
  'connected',
  'responded',
  'meeting_scheduled',
  'warm',
];

export const OUTREACH_STATUS_LABELS: Record<OutreachStatus, string> = {
  identified: 'Identified',
  draft_ready: 'Draft Ready',
  sent: 'Sent',
  connected: 'Connected',
  responded: 'Responded',
  meeting_scheduled: 'Meeting Set',
  warm: 'Warm',
};

export const INTERACTION_TYPE_LABELS: Record<InteractionType, string> = {
  connection_request: 'Connection Request',
  message_sent: 'Message Sent',
  response_received: 'Response Received',
  meeting_scheduled: 'Meeting Scheduled',
  referral_requested: 'Referral Requested',
  referral_given: 'Referral Given',
  note: 'Note',
};

// ─── Job Status Labels ───────────────────────────────────────────

export const STATUS_LABELS: Record<JobStatus, string> = {
  scouted: 'Scouted',
  to_review: 'To Review',
  applied: 'Applied',
  recruiter_engaged: 'Engaged',
  interviewing: 'Interviewing',
  offer: 'Offer',
  not_interested: 'Skipped',
  rejected: 'Rejected',
  deleted: 'Deleted',
};

// ─── Engagement Types ────────────────────────────────────────────

export type EngagementPlatform = 'linkedin' | 'medium' | 'personal_blog';
export type EngagementActionType = 'like' | 'comment' | 'share' | 'connection_request' | 'blog_post';
export type EngagementStatus = 'drafted' | 'approved' | 'posted' | 'skipped';

export interface EngagementEntry {
  id: string;
  platform: EngagementPlatform;
  action_type: EngagementActionType;
  target_url: string | null;
  target_person: string | null;
  content: string | null;
  status: EngagementStatus;
  posted_at: string | null;
  created_at: string;
  updated_at: string;
}

export const ENGAGEMENT_STATUS_LABELS: Record<EngagementStatus, string> = {
  drafted: 'Drafted',
  approved: 'Approved',
  posted: 'Posted',
  skipped: 'Skipped',
};

export const ENGAGEMENT_ACTION_LABELS: Record<EngagementActionType, string> = {
  like: 'Like',
  comment: 'Comment',
  share: 'Share',
  connection_request: 'Connection Request',
  blog_post: 'Blog Post',
};

export const ENGAGEMENT_PLATFORM_LABELS: Record<EngagementPlatform, string> = {
  linkedin: 'LinkedIn',
  medium: 'Medium',
  personal_blog: 'Blog',
};

// ─── Blog Types ──────────────────────────────────────────────────

export type BlogPostStatus = 'idea' | 'draft' | 'review' | 'published';

export interface BlogPost {
  id: string;
  title: string;
  slug: string;
  status: BlogPostStatus;
  platform: string | null;
  tags: string[];
  summary: string | null;
  published_url: string | null;
  published_at: string | null;
  draft_path: string | null;
  content: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export const BLOG_STATUS_LABELS: Record<BlogPostStatus, string> = {
  idea: 'Idea',
  draft: 'Draft',
  review: 'Review',
  published: 'Published',
};

export const BLOG_STATUS_ORDER: BlogPostStatus[] = ['idea', 'draft', 'review', 'published'];

// ─── Schedule Types ─────────────────────────────────────────────

export type ScheduleStatus = 'success' | 'failed' | 'running' | null;

export interface ScheduledJob {
  id: string;
  name: string;
  skill: string;
  skill_args: string | null;
  cron_expr: string;
  enabled: boolean;
  last_run_at: string | null;
  last_status: ScheduleStatus;
  last_error: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export const SCHEDULE_STATUS_LABELS: Record<string, string> = {
  success: 'Success',
  failed: 'Failed',
  running: 'Running',
};

// ─── Job Sort/Group ─────────────────────────────────────────

export type JobSortMode = 'default' | 'score' | 'date' | 'company';

export const JOB_SORT_LABELS: Record<JobSortMode, string> = {
  default: 'Pipeline Priority',
  score: 'Match Score',
  date: 'Date Added',
  company: 'Company',
};

export const AVAILABLE_SKILLS = [
  { value: '/inbox', label: 'Inbox Check' },
  { value: '/linkedin', label: 'LinkedIn Engagement' },
  { value: '/scout', label: 'Job Scout' },
  { value: '/network', label: 'Networking Follow-ups' },
  { value: '/prep', label: 'Interview Prep' },
  { value: '/blog-ideas', label: 'Blog Ideas' },
  { value: '/blog-status', label: 'Blog Status' },
  { value: '/blog-write', label: 'Blog Write' },
  { value: '/review', label: 'Pipeline Review' },
  { value: '/status', label: 'Pipeline Status' },
  { value: '/dedupe', label: 'Deduplicate Jobs' },
  { value: '/cull', label: 'Cull Stale Jobs' },
];

export const CRON_PRESETS = [
  { label: 'Weekdays at 7am', value: '0 7 * * 1-5' },
  { label: 'Weekdays at 8am', value: '0 8 * * 1-5' },
  { label: 'Weekdays at 9am', value: '0 9 * * 1-5' },
  { label: 'Daily at 6pm', value: '0 18 * * *' },
  { label: 'Mon & Thu at 10am', value: '0 10 * * 1,4' },
  { label: 'Weekly Monday at 10am', value: '0 10 * * 1' },
  { label: 'Weekly Friday at 9am', value: '0 9 * * 5' },
  { label: 'Custom', value: '' },
];
