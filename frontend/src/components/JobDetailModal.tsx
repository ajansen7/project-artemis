"use client";

import { useState } from "react";
import { Job, Gap } from "@/types/database";
import { supabase } from "@/lib/supabase";
import {
    X, ExternalLink, Building2, AlertTriangle, CheckCircle2,
    Lightbulb, Edit3, Save, Trash2, ThumbsDown, MessageSquarePlus
} from "lucide-react";

interface Props {
    job: Job;
    onClose: () => void;
    onUpdate: () => void;
    onCaptureAnecdote: (gap: Gap) => void;
}

export default function JobDetailModal({ job, onClose, onUpdate, onCaptureAnecdote }: Props) {
    const [editing, setEditing] = useState(false);
    const [title, setTitle] = useState(job.title);
    const [notes, setNotes] = useState(job.notes || "");
    const [saving, setSaving] = useState(false);
    const [showNotInterested, setShowNotInterested] = useState(false);
    const [reason, setReason] = useState("");

    const analysis = job.gap_analysis_json;

    const handleSave = async () => {
        setSaving(true);
        await supabase.from("jobs").update({ title, notes }).eq("id", job.id);
        setSaving(false);
        setEditing(false);
        onUpdate();
    };

    const handleDelete = async () => {
        await supabase.from("jobs").update({ status: "deleted" }).eq("id", job.id);
        onUpdate();
        onClose();
    };

    const handleNotInterested = async () => {
        if (!reason.trim()) return;
        await supabase
            .from("jobs")
            .update({ status: "not_interested", rejection_reason: reason })
            .eq("id", job.id);
        onUpdate();
        onClose();
    };

    const getScoreColor = (score: number | null) => {
        if (score === null) return "text-muted-foreground";
        if (score >= 80) return "text-green-400";
        if (score >= 60) return "text-yellow-400";
        return "text-red-400";
    };

    const getSeverityColor = (severity: string) => {
        if (severity === "high") return "bg-red-500/20 text-red-400 border-red-500/30";
        if (severity === "medium") return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
        return "bg-blue-500/20 text-blue-400 border-blue-500/30";
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

            {/* Modal */}
            <div className="relative bg-card border border-border rounded-2xl shadow-2xl w-full max-w-2xl max-h-[85vh] overflow-y-auto">
                {/* Header */}
                <div className="sticky top-0 bg-card border-b border-border p-6 flex justify-between items-start z-10 rounded-t-2xl">
                    <div className="flex-1 mr-4">
                        {editing ? (
                            <input
                                className="w-full bg-background border border-border rounded-lg px-3 py-2 text-lg font-semibold focus:outline-none focus:ring-2 focus:ring-primary/50"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                            />
                        ) : (
                            <h2 className="text-lg font-semibold text-foreground">{job.title}</h2>
                        )}
                        <p className="text-sm text-muted-foreground flex items-center gap-1 mt-1">
                            <Building2 className="w-3.5 h-3.5" />
                            {job.company_name || "Unknown Company"}
                        </p>
                    </div>

                    <div className="flex items-center gap-2">
                        {/* Score */}
                        <div className={`text-2xl font-bold ${getScoreColor(job.match_score)}`}>
                            {job.match_score ?? "—"}
                        </div>
                        <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-secondary transition-colors">
                            <X className="w-5 h-5 text-muted-foreground" />
                        </button>
                    </div>
                </div>

                {/* Body */}
                <div className="p-6 space-y-6">
                    {/* Actions bar */}
                    <div className="flex flex-wrap gap-2">
                        {job.url && (
                            <a
                                href={job.url}
                                target="_blank"
                                rel="noreferrer"
                                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-secondary hover:bg-secondary/80 rounded-lg transition-colors"
                            >
                                <ExternalLink className="w-3.5 h-3.5" /> View Posting
                            </a>
                        )}
                        <button
                            onClick={() => setEditing(!editing)}
                            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-secondary hover:bg-secondary/80 rounded-lg transition-colors"
                        >
                            <Edit3 className="w-3.5 h-3.5" /> {editing ? "Cancel" : "Edit"}
                        </button>
                        {editing && (
                            <button
                                onClick={handleSave}
                                disabled={saving}
                                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg transition-colors"
                            >
                                <Save className="w-3.5 h-3.5" /> Save
                            </button>
                        )}
                        <button
                            onClick={() => setShowNotInterested(true)}
                            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-yellow-500/10 hover:bg-yellow-500/20 text-yellow-400 rounded-lg transition-colors"
                        >
                            <ThumbsDown className="w-3.5 h-3.5" /> Not Interested
                        </button>
                        <button
                            onClick={handleDelete}
                            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-destructive/10 hover:bg-destructive/20 text-destructive rounded-lg transition-colors"
                        >
                            <Trash2 className="w-3.5 h-3.5" /> Delete
                        </button>
                    </div>

                    {/* Not Interested Reason */}
                    {showNotInterested && (
                        <div className="bg-yellow-500/5 border border-yellow-500/20 rounded-xl p-4 space-y-3">
                            <p className="text-sm font-medium text-yellow-400">Why are you passing on this role?</p>
                            <textarea
                                className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yellow-500/50 min-h-[80px]"
                                placeholder="e.g., Comp too low, wrong seniority, not excited about the product area..."
                                value={reason}
                                onChange={(e) => setReason(e.target.value)}
                            />
                            <div className="flex gap-2">
                                <button
                                    onClick={handleNotInterested}
                                    disabled={!reason.trim()}
                                    className="px-4 py-2 text-xs font-medium bg-yellow-500 hover:bg-yellow-600 text-black rounded-lg transition-colors disabled:opacity-50"
                                >
                                    Confirm — Not Interested
                                </button>
                                <button
                                    onClick={() => setShowNotInterested(false)}
                                    className="px-4 py-2 text-xs font-medium bg-secondary hover:bg-secondary/80 rounded-lg transition-colors"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Notes */}
                    {editing ? (
                        <div>
                            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Notes</label>
                            <textarea
                                className="w-full mt-1 bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 min-h-[60px]"
                                value={notes}
                                onChange={(e) => setNotes(e.target.value)}
                                placeholder="Your notes about this role..."
                            />
                        </div>
                    ) : job.notes ? (
                        <div>
                            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Notes</h3>
                            <p className="text-sm text-foreground/80 bg-secondary/30 rounded-lg p-3">{job.notes}</p>
                        </div>
                    ) : null}

                    {/* Matched Requirements */}
                    {analysis?.matched_requirements && analysis.matched_requirements.length > 0 && (
                        <div>
                            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3 flex items-center gap-1.5">
                                <CheckCircle2 className="w-3.5 h-3.5 text-green-400" />
                                Matched Requirements ({analysis.matched_requirements.length})
                            </h3>
                            <div className="space-y-1.5">
                                {analysis.matched_requirements.map((req, i) => (
                                    <div key={i} className="flex items-start gap-2 text-sm text-foreground/80">
                                        <span className="text-green-400 mt-0.5">✓</span>
                                        <span>{req}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Gaps — the HITL section */}
                    {analysis?.gaps && analysis.gaps.length > 0 && (
                        <div>
                            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3 flex items-center gap-1.5">
                                <AlertTriangle className="w-3.5 h-3.5 text-yellow-400" />
                                Gaps ({analysis.gaps.length})
                            </h3>
                            <div className="space-y-3">
                                {analysis.gaps.map((gap, i) => (
                                    <div key={i} className="bg-secondary/30 border border-border/50 rounded-xl p-4">
                                        <div className="flex items-start justify-between gap-3">
                                            <div className="flex-1">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full border ${getSeverityColor(gap.severity)}`}>
                                                        {gap.severity}
                                                    </span>
                                                    <span className="text-sm font-medium text-foreground">{gap.requirement}</span>
                                                </div>
                                                <p className="text-xs text-muted-foreground mt-1">{gap.suggestion}</p>
                                            </div>
                                            <button
                                                onClick={() => onCaptureAnecdote(gap)}
                                                className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-primary/10 hover:bg-primary/20 text-primary rounded-lg transition-colors"
                                                title="I have an anecdote for this!"
                                            >
                                                <MessageSquarePlus className="w-3.5 h-3.5" />
                                                <span className="hidden sm:inline">Add Anecdote</span>
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Recommended Actions */}
                    {analysis?.recommended_actions && analysis.recommended_actions.length > 0 && (
                        <div>
                            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3 flex items-center gap-1.5">
                                <Lightbulb className="w-3.5 h-3.5 text-accent" />
                                Recommended Actions
                            </h3>
                            <div className="space-y-1.5">
                                {analysis.recommended_actions.map((action, i) => (
                                    <div key={i} className="flex items-start gap-2 text-sm text-foreground/80">
                                        <span className="text-accent mt-0.5">→</span>
                                        <span>{action}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Rejection Reason (if already set) */}
                    {job.rejection_reason && (
                        <div>
                            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Rejection Reason</h3>
                            <p className="text-sm text-yellow-400/80 bg-yellow-500/5 border border-yellow-500/20 rounded-lg p-3">
                                {job.rejection_reason}
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
