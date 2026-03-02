"use client";

import { useState } from "react";
import { Gap } from "@/types/database";
import { supabase } from "@/lib/supabase";
import { X, Save, Loader2, Sparkles } from "lucide-react";

interface Props {
    gap: Gap;
    onClose: () => void;
    onSaved: () => void;
}

export default function AnecdoteCaptureModal({ gap, onClose, onSaved }: Props) {
    const [title, setTitle] = useState("");
    const [situation, setSituation] = useState("");
    const [task, setTask] = useState("");
    const [action, setAction] = useState("");
    const [result, setResult] = useState("");
    const [tags, setTags] = useState(gap.requirement);
    const [saving, setSaving] = useState(false);
    const [embedding, setEmbedding] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState("");

    const handleSave = async () => {
        if (!title.trim() || !situation.trim()) return;

        setSaving(true);
        setError("");

        try {
            // Step 1: Insert into Supabase anecdotes table
            const { data, error: sbError } = await supabase
                .from("anecdotes")
                .insert([{
                    title: title.trim(),
                    situation: situation.trim(),
                    task: task.trim(),
                    action: action.trim(),
                    result: result.trim(),
                    tags: tags.split(",").map(t => t.trim()).filter(Boolean),
                    source: "hitl_gap_response",
                }])
                .select()
                .single();

            if (sbError) throw sbError;

            // Step 2: Embed into the vector DB via the backend
            setEmbedding(true);
            const anecdoteText = [
                `Anecdote: ${title}`,
                `Situation: ${situation}`,
                `Task: ${task}`,
                `Action: ${action}`,
                `Result: ${result}`,
                `Tags: ${tags}`,
                `Gap addressed: ${gap.requirement}`,
            ].join("\n\n");

            try {
                await fetch("/api/embed", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        text: anecdoteText,
                        source: `anecdote:${data.id}`,
                        content_type: "anecdote",
                        tags: tags.split(",").map((t: string) => t.trim()).filter(Boolean),
                    }),
                });
            } catch {
                // Embedding is optional — doesn't block the save
                console.warn("Embedding failed, anecdote still saved to Supabase");
            }

            setSuccess(true);
            setTimeout(() => {
                onSaved();
                onClose();
            }, 1500);
        } catch (err: any) {
            setError(err.message || "Failed to save anecdote");
        } finally {
            setSaving(false);
            setEmbedding(false);
        }
    };

    if (success) {
        return (
            <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
                <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
                <div className="relative bg-card border border-green-500/30 rounded-2xl shadow-2xl p-8 flex flex-col items-center gap-3">
                    <Sparkles className="w-10 h-10 text-green-400 animate-pulse" />
                    <p className="text-lg font-semibold text-green-400">Anecdote Saved!</p>
                    <p className="text-sm text-muted-foreground">Added to knowledge base</p>
                </div>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

            <div className="relative bg-card border border-border rounded-2xl shadow-2xl w-full max-w-lg max-h-[85vh] overflow-y-auto">
                {/* Header */}
                <div className="sticky top-0 bg-card border-b border-border p-5 flex justify-between items-start z-10 rounded-t-2xl">
                    <div>
                        <h2 className="text-base font-semibold text-foreground">Capture Anecdote</h2>
                        <p className="text-xs text-muted-foreground mt-1">
                            Addressing gap: <span className="text-yellow-400">{gap.requirement}</span>
                        </p>
                    </div>
                    <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-secondary transition-colors">
                        <X className="w-4 h-4 text-muted-foreground" />
                    </button>
                </div>

                {/* STAR Form */}
                <div className="p-5 space-y-4">
                    <div>
                        <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Title *</label>
                        <input
                            className="w-full mt-1 bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                            placeholder="e.g., Led cross-functional data pipeline migration"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                        />
                    </div>

                    <div>
                        <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Situation *</label>
                        <textarea
                            className="w-full mt-1 bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 min-h-[60px]"
                            placeholder="What was the context? What challenge did you face?"
                            value={situation}
                            onChange={(e) => setSituation(e.target.value)}
                        />
                    </div>

                    <div>
                        <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Task</label>
                        <textarea
                            className="w-full mt-1 bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 min-h-[50px]"
                            placeholder="What were you specifically responsible for?"
                            value={task}
                            onChange={(e) => setTask(e.target.value)}
                        />
                    </div>

                    <div>
                        <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Action</label>
                        <textarea
                            className="w-full mt-1 bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 min-h-[60px]"
                            placeholder="What did you do? Be specific about your contributions."
                            value={action}
                            onChange={(e) => setAction(e.target.value)}
                        />
                    </div>

                    <div>
                        <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Result</label>
                        <textarea
                            className="w-full mt-1 bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 min-h-[50px]"
                            placeholder="What was the outcome? Include metrics if possible."
                            value={result}
                            onChange={(e) => setResult(e.target.value)}
                        />
                    </div>

                    <div>
                        <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Tags (comma-separated)</label>
                        <input
                            className="w-full mt-1 bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                            value={tags}
                            onChange={(e) => setTags(e.target.value)}
                        />
                    </div>

                    {error && <p className="text-xs text-destructive">{error}</p>}

                    <button
                        onClick={handleSave}
                        disabled={saving || !title.trim() || !situation.trim()}
                        className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg transition-colors disabled:opacity-50"
                    >
                        {saving ? (
                            <>
                                <Loader2 className="w-4 h-4 animate-spin" />
                                {embedding ? "Embedding..." : "Saving..."}
                            </>
                        ) : (
                            <>
                                <Save className="w-4 h-4" />
                                Save Anecdote & Embed
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}
