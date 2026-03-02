export type JobStatus = 'scouted' | 'to_review' | 'applied' | 'interviewing' | 'rejected' | 'offer' | 'not_interested' | 'deleted';

export interface Gap {
    requirement: string;
    severity: 'high' | 'medium' | 'low';
    suggestion: string;
}

export interface GapAnalysis {
    matched_requirements: string[];
    gaps: Gap[];
    recommended_actions: string[];
}

export interface Job {
    id: string;
    company_id: string | null;
    company_name?: string | null;
    title: string;
    url: string;
    description_md: string | null;
    status: JobStatus;
    match_score: number | null;
    gap_analysis_json: GapAnalysis | null;
    rejection_reason: string | null;
    notes: string | null;
    created_at: string;
    updated_at: string;
}

