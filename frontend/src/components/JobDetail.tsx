import { useState } from 'react';
import type { Job } from '../types';
import { MarkdownModal } from './MarkdownModal';
import { ApplicationModal } from './ApplicationModal';
import { useTaskPoller } from '../hooks/useTasks';

interface JobDetailProps {
  job: Job;
  onAdvance: () => void;
  onSkip: () => void;
  onDelete: () => void;
  onUpdate: () => void;
}

export function JobDetail({ job, onAdvance, onSkip, onDelete, onUpdate }: JobDetailProps) {
  const nextStatus = getNextStatus(job.status);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeTaskId, setAnalyzeTaskId] = useState<string | null>(null);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [applicationModalOpen, setApplicationModalOpen] = useState(false);

  useTaskPoller(
    analyzeTaskId,
    (task) => {
      setAnalyzing(false);
      setAnalyzeTaskId(null);
      setModalTitle(`Analysis — ${job.companies?.name || 'Job'}`);
      setModalContent(task.output ?? '');
      setModalOpen(true);
      setTimeout(onUpdate, 500);
    },
    () => {
      setAnalyzing(false);
      setAnalyzeTaskId(null);
      setStatusMsg('❌ Analyze failed. Run: tmux attach -t artemis');
    },
  );

  const [modalOpen, setModalOpen] = useState(false);
  const [modalContent, setModalContent] = useState('');
  const [modalTitle, setModalTitle] = useState('');

  const handleAnalyze = async () => {
    if (!job.url) {
      setStatusMsg('❌ No URL to analyze.');
      return;
    }
    setAnalyzing(true);
    setStatusMsg('Analyzing in tmux… check the task panel or run: tmux attach -t artemis');
    try {
      const response = await fetch('http://localhost:8000/api/run-skill', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ skill: 'analyze', target: `Job ID: ${job.id}, URL: ${job.url}` }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Failed to start task');
      setAnalyzeTaskId(data.task_id);
    } catch (err: any) {
      setAnalyzing(false);
      setStatusMsg(`❌ ${err.message}`);
    }
  };

  return (
    <div className="job-detail">
      <div className="job-detail-inner">
        <div className="detail-section">
          <h4>Description</h4>
          <p>{job.description_md || 'No description available.'}</p>
        </div>

        <div className="detail-section">
          <h4>Details</h4>
          {job.url && (
            <div className="detail-url" style={{ marginBottom: 8 }}>
              <a href={job.url} target="_blank" rel="noopener noreferrer">{job.url}</a>
            </div>
          )}
          <p>
            <strong>Source:</strong> {job.source || 'unknown'}<br />
            <strong>Score:</strong> {job.match_score ?? 'Not scored'}<br />
            <strong>Added:</strong> {new Date(job.created_at).toLocaleDateString()}
          </p>
          {job.gap_analysis_json && !(job.gap_analysis_json as any).markdown && (
            <>
              <h4 style={{ marginTop: 16 }}>Gap Analysis</h4>
              <pre style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', whiteSpace: 'pre-wrap' }}>
                {JSON.stringify(job.gap_analysis_json, null, 2)}
              </pre>
            </>
          )}
        </div>

        <div className="detail-actions">
          {/* Primary CTA — opens the full application flow modal */}
          <button
            className="action-btn"
            style={{ backgroundColor: 'var(--primary)', color: 'white' }}
            onClick={() => setApplicationModalOpen(true)}
          >
            {(job.applications?.[0] as any)?.resume_md ? '📂 Application' : '🚀 Start Application'}
          </button>

          {/* Analysis */}
          {(job.gap_analysis_json as any)?.markdown ? (
            <>
              <button
                className="action-btn"
                style={{ backgroundColor: 'var(--bg-elevated)', color: 'var(--text-primary)' }}
                onClick={() => {
                  setModalTitle(`Analysis — ${job.companies?.name || 'Job'}`);
                  setModalContent((job.gap_analysis_json as any).markdown);
                  setModalOpen(true);
                }}
              >
                📖 Analysis
              </button>
              <button
                className="action-btn"
                style={{ backgroundColor: 'var(--blue-dim)', color: 'var(--blue)' }}
                onClick={handleAnalyze}
                disabled={analyzing || !job.url}
              >
                {analyzing ? '🔍 Analyzing...' : '🔄 Re-analyze'}
              </button>
            </>
          ) : (
            <button
              className="action-btn"
              style={{ backgroundColor: 'var(--blue-dim)', color: 'var(--blue)' }}
              onClick={handleAnalyze}
              disabled={analyzing || !job.url}
            >
              {analyzing ? '🔍 Analyzing...' : '🔍 Analyze'}
            </button>
          )}

          {/* Pipeline progression — skip to_review→applied since that's in the modal */}
          {nextStatus && (
            <button className="action-btn review" onClick={onAdvance}>
              → Move to {nextStatus.replace('_', ' ')}
            </button>
          )}
          <button className="action-btn skip" onClick={onSkip}>Skip</button>
          <button className="action-btn delete" onClick={onDelete}>Delete</button>
        </div>

        {statusMsg && (
          <div style={{ marginTop: 12, fontSize: '0.85rem', color: statusMsg.startsWith('✅') ? 'var(--success)' : 'var(--danger)' }}>
            {statusMsg}
          </div>
        )}
      </div>

      <ApplicationModal
        isOpen={applicationModalOpen}
        onClose={() => setApplicationModalOpen(false)}
        job={job}
        onGenerationComplete={() => { setTimeout(onUpdate, 1000); }}
        onSubmitted={() => { onAdvance(); onUpdate(); }}
      />

      <MarkdownModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={modalTitle}
        content={modalContent}
        onSaved={() => setTimeout(onUpdate, 500)}
      />
    </div>
  );
}

function getNextStatus(current: string): string | null {
  const flow: Record<string, string> = {
    scouted: 'to_review',
    // to_review → applied is handled by the Start Application modal
    applied: 'interviewing',
    interviewing: 'offer',
  };
  return flow[current] || null;
}
