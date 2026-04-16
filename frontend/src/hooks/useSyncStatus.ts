import { useState, useEffect } from 'react';

const LAST_SYNC_KEY = 'artemis:lastSync';

export interface SyncStatus {
  lastSync: Date | null;
  isSyncing: boolean;
  formattedTime: string;
}

export function useSyncStatus() {
  const [lastSync, setLastSync] = useState<Date | null>(() => {
    const stored = localStorage.getItem(LAST_SYNC_KEY);
    return stored ? new Date(stored) : null;
  });

  const [isSyncing, setIsSyncing] = useState(false);

  useEffect(() => {
    // Listen for custom sync events
    const handleSyncStart = () => setIsSyncing(true);
    const handleSyncComplete = () => {
      setIsSyncing(false);
      const now = new Date();
      setLastSync(now);
      localStorage.setItem(LAST_SYNC_KEY, now.toISOString());
    };

    window.addEventListener('artemis:sync:start', handleSyncStart);
    window.addEventListener('artemis:sync:complete', handleSyncComplete);

    return () => {
      window.removeEventListener('artemis:sync:start', handleSyncStart);
      window.removeEventListener('artemis:sync:complete', handleSyncComplete);
    };
  }, []);

  const formattedTime = lastSync
    ? formatTime(lastSync)
    : 'Never synced';

  return {
    lastSync,
    isSyncing,
    formattedTime,
  };
}

function formatTime(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) {
    return 'Just now';
  } else if (diffMins < 60) {
    return `${diffMins}m ago`;
  } else if (diffHours < 24) {
    return `${diffHours}h ago`;
  } else if (diffDays === 1) {
    return 'Yesterday';
  } else if (diffDays < 7) {
    return `${diffDays}d ago`;
  } else {
    return date.toLocaleDateString();
  }
}
