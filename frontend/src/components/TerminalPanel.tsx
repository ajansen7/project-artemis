import { useRef, useEffect } from 'react';
import { useTerminal } from '../hooks/useTerminal';
import type { TerminalStatus } from '../hooks/useTerminal';
import '@xterm/xterm/css/xterm.css';

function StatusIndicator({ status, error }: { status: TerminalStatus; error: string | null }) {
  const colors: Record<TerminalStatus, string> = {
    disconnected: '#888',
    connecting: '#e6a817',
    connected: '#2e7d32',
    error: '#c62828',
  };

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      fontSize: '13px',
      color: '#ccc',
    }}>
      <span style={{
        width: '8px',
        height: '8px',
        borderRadius: '50%',
        background: colors[status],
        display: 'inline-block',
      }} />
      {status === 'connected' && 'Connected to orchestrator'}
      {status === 'connecting' && 'Connecting...'}
      {status === 'disconnected' && 'Disconnected'}
      {status === 'error' && (error || 'Connection error')}
    </div>
  );
}

export function TerminalPanel() {
  const containerRef = useRef<HTMLDivElement>(null);
  const { status, error, connect, disconnect } = useTerminal({ containerRef });

  // Auto-connect on mount
  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: 'calc(100vh - 160px)',
      background: '#1e1e1e',
      borderRadius: '6px',
      overflow: 'hidden',
    }}>
      {/* Toolbar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '8px 12px',
        background: '#2d2d2d',
        borderBottom: '1px solid #404040',
      }}>
        <StatusIndicator status={status} error={error} />
        <div style={{ display: 'flex', gap: '6px' }}>
          {status === 'disconnected' || status === 'error' ? (
            <button
              onClick={connect}
              style={{
                padding: '4px 12px',
                fontSize: '12px',
                background: '#2e7d32',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              Connect
            </button>
          ) : (
            <button
              onClick={disconnect}
              style={{
                padding: '4px 12px',
                fontSize: '12px',
                background: '#555',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              Disconnect
            </button>
          )}
        </div>
      </div>

      {/* Terminal container */}
      <div
        ref={containerRef}
        style={{
          flex: 1,
          padding: '4px',
          overflow: 'hidden',
        }}
      />
    </div>
  );
}
