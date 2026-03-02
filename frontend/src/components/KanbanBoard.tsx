"use client";

import { useEffect, useState } from "react";
import { DragDropContext, Droppable, DropResult } from "@hello-pangea/dnd";
import { supabase } from "@/lib/supabase";
import { Job, JobStatus, Gap } from "@/types/database";
import JobCard from "./JobCard";
import JobDetailModal from "./JobDetailModal";
import AnecdoteCaptureModal from "./AnecdoteCaptureModal";
import { Loader2 } from "lucide-react";

const COLUMNS: { id: JobStatus; title: string; hidden?: boolean }[] = [
    { id: "scouted", title: "Scouted" },
    { id: "to_review", title: "To Review" },
    { id: "applied", title: "Applied" },
    { id: "interviewing", title: "Interviewing" },
    { id: "offer", title: "Offer" },
    { id: "rejected", title: "Rejected" },
    { id: "not_interested", title: "Not Interested" },
    // 'deleted' jobs are hidden from the board entirely
];

export default function KanbanBoard({ refreshTrigger }: { refreshTrigger: number }) {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedJob, setSelectedJob] = useState<Job | null>(null);
    const [captureGap, setCaptureGap] = useState<Gap | null>(null);

    const fetchJobs = async () => {
        try {
            const { data, error } = await supabase
                .from("jobs")
                .select(`
          id, title, url, status, match_score, gap_analysis_json, 
          rejection_reason, notes, created_at, updated_at,
          company_id,
          companies ( name )
        `)
                .neq("status", "deleted")
                .order("created_at", { ascending: false });

            if (error) throw error;

            const formattedData = (data as any[]).map(job => ({
                ...job,
                company_name: job.companies?.name || null
            }));

            setJobs(formattedData);
        } catch (error) {
            console.error("Error fetching jobs:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchJobs();
    }, [refreshTrigger]);

    useEffect(() => {
        const channel = supabase
            .channel("schema-db-changes")
            .on(
                "postgres_changes",
                { event: "*", schema: "public", table: "jobs" },
                () => fetchJobs()
            )
            .subscribe();

        return () => { supabase.removeChannel(channel); };
    }, []);

    const onDragEnd = async (result: DropResult) => {
        const { destination, source, draggableId } = result;

        if (!destination) return;
        if (destination.droppableId === source.droppableId && destination.index === source.index) return;

        const newStatus = destination.droppableId as JobStatus;

        setJobs(prevJobs => prevJobs.map(job =>
            job.id === draggableId ? { ...job, status: newStatus } : job
        ));

        try {
            const { error } = await supabase
                .from("jobs")
                .update({ status: newStatus })
                .eq("id", draggableId);

            if (error) throw error;
        } catch (error) {
            console.error("Failed to update job status:", error);
            fetchJobs();
        }
    };

    const handleJobClick = (job: Job) => {
        setSelectedJob(job);
    };

    const handleCaptureAnecdote = (gap: Gap) => {
        setCaptureGap(gap);
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center p-20 text-muted-foreground w-full">
                <Loader2 className="w-8 h-8 animate-spin" />
            </div>
        );
    }

    return (
        <>
            <DragDropContext onDragEnd={onDragEnd}>
                <div className="flex gap-4 overflow-x-auto pb-4 h-full w-full items-start">
                    {COLUMNS.map((column) => (
                        <div
                            key={column.id}
                            className="flex flex-col flex-shrink-0 w-[300px] h-full"
                        >
                            <div className="flex items-center justify-between mb-3 px-1">
                                <h3 className="font-semibold text-sm tracking-wide text-foreground uppercase">
                                    {column.title}
                                </h3>
                                <span className="bg-secondary text-secondary-foreground text-xs font-medium px-2 py-0.5 rounded-full">
                                    {jobs.filter((j) => j.status === column.id).length}
                                </span>
                            </div>

                            <Droppable droppableId={column.id}>
                                {(provided, snapshot) => (
                                    <div
                                        ref={provided.innerRef}
                                        {...provided.droppableProps}
                                        className={`
                      flex-1 min-h-[150px] p-2 rounded-xl transition-colors
                      border border-dashed border-border/50
                      ${snapshot.isDraggingOver ? "bg-primary/5 border-primary/30" : "bg-card/30"}
                    `}
                                    >
                                        {jobs
                                            .filter((j) => j.status === column.id)
                                            .map((job, index) => (
                                                <JobCard
                                                    key={job.id}
                                                    job={job}
                                                    index={index}
                                                    onClick={handleJobClick}
                                                />
                                            ))}
                                        {provided.placeholder}
                                    </div>
                                )}
                            </Droppable>
                        </div>
                    ))}
                </div>
            </DragDropContext>

            {/* Job Detail Modal */}
            {selectedJob && (
                <JobDetailModal
                    job={selectedJob}
                    onClose={() => setSelectedJob(null)}
                    onUpdate={() => {
                        fetchJobs();
                        // Refresh the selected job data
                        setSelectedJob(prev => {
                            if (!prev) return null;
                            const updated = jobs.find(j => j.id === prev.id);
                            return updated || prev;
                        });
                    }}
                    onCaptureAnecdote={handleCaptureAnecdote}
                />
            )}

            {/* Anecdote Capture Modal */}
            {captureGap && (
                <AnecdoteCaptureModal
                    gap={captureGap}
                    onClose={() => setCaptureGap(null)}
                    onSaved={() => {
                        setCaptureGap(null);
                        fetchJobs();
                    }}
                />
            )}
        </>
    );
}
