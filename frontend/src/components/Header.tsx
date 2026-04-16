import { useState } from 'react';
import { MarkdownModal } from './MarkdownModal';
import { API_BASE, fetchWithAuth } from '../lib/api';
import { supabase } from '../lib/supabase';
import { useSyncStatus } from '../hooks/useSyncStatus';

interface HeaderProps {
  counts: Record<string, number>;
  session?: any;
}

export function Header({ counts, session }: HeaderProps) {
  const [runningSkill, setRunningSkill] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalContent, setModalContent] = useState('');
  const [modalTitle, setModalTitle] = useState('');
  const syncStatus = useSyncStatus();

  const handleRunSkill = async (skill: string) => {
    setRunningSkill(skill);

    // Emit sync start event for /sync command
    if (skill === 'sync') {
      window.dispatchEvent(new Event('artemis:sync:start'));
    }

    try {
      const response = await fetchWithAuth(`${API_BASE}/api/run-skill`, {
        method: 'POST',
        body: JSON.stringify({ skill }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Execution failed');

      setModalTitle(`/${skill} Results`);
      setModalContent(data.output);
      setModalOpen(true);

      // Emit sync complete event after /sync succeeds
      if (skill === 'sync') {
        window.dispatchEvent(new Event('artemis:sync:complete'));
      }
    } catch (err: any) {
      setModalTitle(`Error running /${skill}`);
      setModalContent(`❌ **Error:** ${err.message}`);
      setModalOpen(true);
    } finally {
      setRunningSkill(null);
    }
  };

  const stats = [
    { key: 'scouted', label: 'Scouted' },
    { key: 'to_review', label: 'To Review' },
    { key: 'applied', label: 'Applied' },
    { key: 'recruiter_engaged', label: 'Engaged' },
    { key: 'interviewing', label: 'Interviewing' },
    { key: 'offer', label: 'Offers' },
  ];

  return (
    <header className="header">
      <div className="header-left">
        <div className="header-logo">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
            <path d="M2 12h20" />
          </svg>
          Artemis
        </div>
        <div className="stats-bar">
          {stats.map(s => (
            <div key={s.key} className="stat-item">
              <span className="stat-count">{counts[s.key] || 0}</span>
              <span className="stat-label">{s.label}</span>
            </div>
          ))}
        </div>
      </div>
      
      <div className="header-right" style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
        {session?.user?.email && (
          <div style={{
            fontSize: '12px',
            color: 'var(--text-secondary)',
            padding: '4px 8px',
            borderRadius: '4px',
            backgroundColor: 'var(--bg-elevated)',
          }}>
            {session.user.email}
          </div>
        )}
        <button
          className="action-btn"
          style={{
            backgroundColor: 'var(--bg-elevated)',
            color: 'var(--text-primary)',
            fontSize: '12px',
            padding: '4px 8px'
          }}
          onClick={async () => {
            await supabase.auth.signOut();
            await fetch('/api/auth/logout', { method: 'POST' });
          }}
        >
          Sign out
        </button>
        <div className="sync-status" style={{
          fontSize: '12px',
          color: 'var(--text-secondary)',
          padding: '4px 8px',
          borderRadius: '4px',
          backgroundColor: 'var(--bg-elevated)',
          minWidth: '100px',
          textAlign: 'center',
        }}>
          {syncStatus.isSyncing ? (
            <>⏳ Syncing...</>
          ) : (
            <>✓ {syncStatus.formattedTime}</>
          )}
        </div>
        <button
          className="action-btn"
          style={{ backgroundColor: 'var(--bg-elevated)', color: 'var(--text-primary)' }}
          onClick={() => handleRunSkill('review')}
          disabled={runningSkill !== null}
        >
          {runningSkill === 'review' ? '⏳ Running...' : '📋 /review'}
        </button>
        <button
          className="action-btn"
          style={{ backgroundColor: 'var(--bg-elevated)', color: 'var(--text-primary)' }}
          onClick={() => handleRunSkill('sync')}
          disabled={runningSkill !== null}
        >
          {runningSkill === 'sync' ? '⏳ Syncing...' : '🔄 /sync'}
        </button>
      </div>

      <MarkdownModal 
        isOpen={modalOpen} 
        onClose={() => setModalOpen(false)} 
        title={modalTitle} 
        content={modalContent} 
      />
    </header>
  );
}
