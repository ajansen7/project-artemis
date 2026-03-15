import { useState } from 'react';
import type { Job } from '../types';
import { MarkdownModal } from './MarkdownModal';

interface JobDetailProps {
  job: Job;
  onAdvance: () => void;
  onSkip: () => void;
  onDelete: () => void;
}

export function JobDetail({ job, onAdvance, onSkip, onDelete }: JobDetailProps) {
  const nextStatus = getNextStatus(job.status);
  const [generating, setGenerating] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [generateMessage, setGenerateMessage] = useState<string | null>(null);
  
  const [modalOpen, setModalOpen] = useState(false);
  const [modalContent, setModalContent] = useState('');
  const [modalTitle, setModalTitle] = useState('');

  const handleAnalyze = async () => {
    if (!job.url) {
      setGenerateMessage('❌ Error: No URL found to analyze.');
      return;
    }
    setAnalyzing(true);
    setGenerateMessage(null);
    try {
      const response = await fetch('http://localhost:8000/api/run-skill', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ skill: 'analyze', target: `Job ID: ${job.id}, URL: ${job.url}` }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Execution failed');
      
      setModalTitle(`/analyze Results for ${job.companies?.name || 'Job'}`);
      setModalContent(data.output);
      setModalOpen(true);
    } catch (err: any) {
      setModalTitle(`Error running /analyze`);
      setModalContent(`❌ **Error:** ${err.message}`);
      setModalOpen(true);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleViewDocument = (t: string, content: string) => {
    setModalTitle(`${t} for ${job.companies?.name || 'Job'}`);
    setModalContent(content);
    setModalOpen(true);
  };

  const handleGenerate = async () => {
    setGenerating(true);
    setGenerateMessage(null);
    try {
      const companyName = job.companies?.name || '';
      const response = await fetch('http://localhost:8000/api/generate-application', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: job.id, company_name: companyName }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Generation failed');
      }
      
      setGenerateMessage('✅ Generated in applications folder.');
    } catch (err: any) {
      setGenerateMessage(`❌ Error: ${err.message}`);
    } finally {
      setGenerating(false);
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
              <a href={job.url} target="_blank" rel="noopener noreferrer">
                {job.url}
              </a>
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
          <button 
            className="action-btn" 
            style={{ backgroundColor: 'var(--primary)', color: 'white' }}
            onClick={handleGenerate}
            disabled={generating || analyzing}
          >
            {generating ? '✨ Generating...' : (job.applications?.[0]?.resume_md ? '🔄 Re-generate' : '✨ Generate Application')}
          </button>

          {job.applications?.[0]?.resume_md && (
            <button 
              className="action-btn" 
              style={{ backgroundColor: 'var(--bg-elevated)', color: 'var(--text-primary)', padding: '0.4rem 0.75rem' }}
              onClick={() => handleViewDocument('Resume', job.applications![0].resume_md!)}
            >
              📄 Resume
            </button>
          )}
          {job.applications?.[0]?.cover_letter_md && (
            <button 
              className="action-btn" 
              style={{ backgroundColor: 'var(--bg-elevated)', color: 'var(--text-primary)', padding: '0.4rem 0.75rem' }}
              onClick={() => handleViewDocument('Cover Letter', job.applications![0].cover_letter_md!)}
            >
              ✉️ Cover Letter
            </button>
          )}
          {job.applications?.[0]?.primer_md && (
            <button 
              className="action-btn" 
              style={{ backgroundColor: 'var(--bg-elevated)', color: 'var(--text-primary)', padding: '0.4rem 0.75rem' }}
              onClick={() => handleViewDocument('Primer', job.applications![0].primer_md!)}
            >
              📚 Primer
            </button>
          )}
          
          {(job.gap_analysis_json as any)?.markdown ? (
            <>
              <button 
                className="action-btn" 
                style={{ backgroundColor: 'var(--bg-elevated)', color: 'var(--text-primary)' }}
                onClick={() => handleViewDocument('Analysis', (job.gap_analysis_json as any).markdown)}
              >
                📖 View Analysis
              </button>
              <button 
                className="action-btn" 
                style={{ backgroundColor: 'var(--blue-dim)', color: 'var(--blue)' }}
                onClick={handleAnalyze}
                disabled={generating || analyzing || !job.url}
              >
                {analyzing ? '🔍 Analyzing...' : '🔄 Re-analyze'}
              </button>
            </>
          ) : (
            <button 
              className="action-btn" 
              style={{ backgroundColor: 'var(--blue-dim)', color: 'var(--blue)' }}
              onClick={handleAnalyze}
              disabled={generating || analyzing || !job.url}
            >
              {analyzing ? '🔍 Analyzing...' : '🔍 /analyze'}
            </button>
          )}

          {nextStatus && (
            <button className="action-btn review" onClick={onAdvance}>
              → Move to {nextStatus.replace('_', ' ')}
            </button>
          )}
          <button className="action-btn skip" onClick={onSkip}>
            Skip
          </button>
          <button className="action-btn delete" onClick={onDelete}>
            Delete
          </button>
        </div>
        {generateMessage && (
          <div style={{ marginTop: 12, fontSize: '0.85rem', color: generateMessage.startsWith('✅') ? 'var(--success)' : 'var(--danger)' }}>
            {generateMessage}
          </div>
        )}
      </div>
      
      <MarkdownModal 
        isOpen={modalOpen} 
        onClose={() => setModalOpen(false)} 
        title={modalTitle} 
        content={modalContent} 
      />
    </div>
  );
}

function getNextStatus(current: string): string | null {
  const flow: Record<string, string> = {
    scouted: 'to_review',
    to_review: 'applied',
    applied: 'interviewing',
    interviewing: 'offer',
  };
  return flow[current] || null;
}
