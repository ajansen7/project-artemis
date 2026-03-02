"use client";

import { Draggable } from "@hello-pangea/dnd";
import { Building2, Sparkles, AlertCircle, FileText } from "lucide-react";
import { Job } from "@/types/database";

interface Props {
    job: Job;
    index: number;
    onClick: (job: Job) => void;
}

export default function JobCard({ job, index, onClick }: Props) {
    const getScoreColor = (score: number | null) => {
        if (score === null) return "text-muted-foreground bg-muted";
        if (score >= 80) return "text-green-400 bg-green-400/10 border-green-400/20";
        if (score >= 60) return "text-yellow-400 bg-yellow-400/10 border-yellow-400/20";
        return "text-red-400 bg-red-400/10 border-red-400/20";
    };

    const isAnalyzing = job.title === 'Analyzing...';

    return (
        <Draggable draggableId={job.id} index={index}>
            {(provided, snapshot) => (
                <div
                    ref={provided.innerRef}
                    {...provided.draggableProps}
                    {...provided.dragHandleProps}
                    onClick={() => !snapshot.isDragging && onClick(job)}
                    className={`
            bg-card border border-border p-4 rounded-xl shadow-sm mb-3 cursor-pointer
            transition-all duration-200 
            ${snapshot.isDragging ? 'shadow-xl ring-2 ring-primary/50 scale-[1.02] rotate-1 z-50' : 'hover:border-primary/30 hover:shadow-md'}
          `}
                    style={{
                        ...provided.draggableProps.style,
                    }}
                >
                    <div className="flex justify-between items-start gap-4 mb-3">
                        <div>
                            <h4 className="font-medium text-sm leading-tight text-foreground" title={job.title}>
                                {job.title?.length > 45 ? job.title.substring(0, 45) + '...' : (job.title || 'Untitled Role')}
                            </h4>
                            <p className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
                                <Building2 className="w-3 h-3" />
                                {job.company_name || 'Unknown Company'}
                            </p>
                        </div>

                        {!isAnalyzing ? (
                            <div className={`flex flex-col items-center justify-center shrink-0 w-10 h-10 rounded-full border ${getScoreColor(job.match_score)}`}>
                                <span className="text-xs font-bold leading-none">{job.match_score || '?'}</span>
                            </div>
                        ) : (
                            <div className="flex items-center justify-center shrink-0 w-8 h-8 rounded-full bg-secondary animate-pulse">
                                <Sparkles className="w-3 h-3 text-muted-foreground" />
                            </div>
                        )}
                    </div>

                    <div className="flex items-center justify-between text-xs text-muted-foreground border-t border-border/50 pt-3">
                        {job.gap_analysis_json && job.gap_analysis_json.gaps ? (
                            <div className="flex items-center gap-1 text-yellow-500/80">
                                <AlertCircle className="w-3 h-3" />
                                <span>{job.gap_analysis_json.gaps.length} gaps</span>
                            </div>
                        ) : isAnalyzing ? (
                            <span className="text-primary/70 animate-pulse">Running analysis...</span>
                        ) : (
                            <span>No analysis</span>
                        )}

                        {job.url && (
                            <a
                                href={job.url}
                                target="_blank"
                                rel="noreferrer"
                                className="hover:text-primary transition-colors flex items-center gap-1"
                                onClick={(e) => e.stopPropagation()}
                            >
                                <FileText className="w-3 h-3" />
                                <span>Source</span>
                            </a>
                        )}
                    </div>
                </div>
            )}
        </Draggable>
    );
}
