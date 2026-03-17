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
  interviewing: 'Interviewing',
  offer: 'Offer',
  not_interested: 'Skipped',
  rejected: 'Rejected',
  deleted: 'Deleted',
};
