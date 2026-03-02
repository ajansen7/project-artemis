"use client";

import { useState } from "react";
import { Plus, Search, Loader2 } from "lucide-react";
import { supabase } from "@/lib/supabase";

export default function AddJobForm({ onJobAdded }: { onJobAdded: () => void }) {
    const [url, setUrl] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [status, setStatus] = useState("");

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!url) return;

        setLoading(true);
        setError("");
        setStatus("Creating job entry...");

        try {
            // Step 1: Insert a placeholder row in Supabase so the card shows immediately
            const { data: job, error: sbError } = await supabase
                .from('jobs')
                .insert([
                    {
                        url: url,
                        title: 'Analyzing...',
                        status: 'scouted',
                        company_id: null,
                    }
                ])
                .select()
                .single();

            if (sbError) throw sbError;

            setUrl("");
            onJobAdded();
            setStatus("Running Analyst agent...");

            // Step 2: Fire off the analysis in the background  
            // This calls our Next.js API route which proxies to the Python FastAPI backend
            fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ job_url: url }),
            })
                .then(res => res.json())
                .then(data => {
                    if (data.error) {
                        console.error("Analysis error:", data.error);
                    }
                    // The analyst upserts results to Supabase directly,
                    // and the KanbanBoard's real-time subscription will pick them up
                    onJobAdded();
                    setStatus("");
                })
                .catch(err => {
                    console.error("Analysis request failed:", err);
                    setStatus("");
                });

        } catch (err: any) {
            setError(err.message || "Failed to add job.");
            setStatus("");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-card w-full lg:w-[400px] border border-border p-5 rounded-xl shadow-lg flex flex-col gap-4 relative overflow-hidden group">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary/40 to-accent/40 opacity-0 transition-opacity group-hover:opacity-100" />

            <div>
                <h3 className="font-semibold text-lg flex items-center gap-2">
                    <Search className="w-5 h-5 text-primary" />
                    Scout New Job
                </h3>
                <p className="text-sm text-muted-foreground mt-1">
                    Paste a URL to generate a match score and gap analysis.
                </p>
            </div>

            <form onSubmit={handleSubmit} className="flex gap-2">
                <input
                    type="url"
                    required
                    placeholder="https://company.com/careers/..."
                    className="flex-1 bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all placeholder:text-muted-foreground/50"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    disabled={loading}
                />
                <button
                    type="submit"
                    disabled={loading || !url}
                    className="bg-primary hover:bg-primary/90 text-primary-foreground px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center min-w-[44px]"
                >
                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                </button>
            </form>

            {status && <p className="text-xs text-primary/70 animate-pulse">{status}</p>}
            {error && <p className="text-xs text-destructive">{error}</p>}
        </div>
    );
}
