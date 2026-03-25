import { useState } from 'react';
import type { Task } from '../hooks/useTasks';
import { useTasks } from '../hooks/useTasks';

function elapsed(startedAt: string, endedAt: string | null): string {
  const start = new Date(startedAt).getTime();
  const end = endedAt ? new Date(endedAt).getTime() : Date.now();
  const secs = Math.floor((end - start) / 1000);
  if (secs < 60) return `${secs}s`;
  return `${Math.floor(secs / 60)}m ${secs % 60}s`;
}

function StatusDot({ status }: { status: Task['status'] }) {
  if (status === 'running' || status === 'queued') {
    return (
      <span style={{
        display: 'inline-block',
        width: 8, height: 8,
        borderRadius: '50%',
        backgroundColor: status === 'running' ? 'var(--primary)' : 'var(--text-secondary, #888)',
        animation: status === 'running' ? 'pulse 1.2s ease-in-out infinite' : undefined,
        flexShrink: 0,
      }} />
    );
  }
  const color = status === 'complete' ? 'var(--success, #4caf78)' : 'var(--danger, #f44)';
  const symbol = status === 'complete' ? '✓' : '✕';
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      width: 14, height: 14, borderRadius: '50%',
      backgroundColor: color, color: 'white',
      fontSize: '0.6rem', fontWeight: 700, flexShrink: 0,
    }}>
      {symbol}
    </span>
  );
}

function TaskRow({ task, onKill }: { task: Task; onKill: () => void }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div style={{ borderBottom: '1px solid var(--border)' }}>
      <div
        style={{
          display: 'flex', alignItems: 'center', gap: 8,
          padding: '0.5rem 0.75rem', cursor: 'pointer',
          fontSize: '0.8rem',
        }}
        onClick={() => setExpanded(e => !e)}
      >
        <StatusDot status={task.status} />
        <span style={{
          flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          color: 'var(--text-primary)',
        }}>
          {task.name}
        </span>
        <span style={{ color: 'var(--text-muted)', flexShrink: 0, fontVariantNumeric: 'tabular-nums' }}>
          {elapsed(task.started_at, task.ended_at)}
        </span>
        {task.status === 'running' && (
          <button
            onClick={e => { e.stopPropagation(); onKill(); }}
            style={{
              background: 'none', border: 'none', color: 'var(--text-muted)',
              cursor: 'pointer', padding: '0 2px', fontSize: '0.75rem',
            }}
            title="Kill task"
          >
            ✕
          </button>
        )}
        <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
          {expanded ? '▲' : '▼'}
        </span>
      </div>

      {expanded && (
        <div style={{
          padding: '0.5rem 0.75rem',
          backgroundColor: 'var(--bg-base)',
          fontFamily: 'var(--font-mono, monospace)',
          fontSize: '0.72rem',
          color: 'var(--text-secondary)',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-all',
          maxHeight: 200,
          overflowY: 'auto',
          lineHeight: 1.5,
        }}>
          {task.output
            ? task.output
            : <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>No output yet…</span>
          }
        </div>
      )}
    </div>
  );
}

export function TasksPanel() {
  const { tasks, fetchTasks, cancelTask, activeCount } = useTasks();
  const killTask = cancelTask;
  const runningCount = activeCount;
  const [open, setOpen] = useState(false);

  // Auto-open when a task starts
  if (runningCount > 0 && !open) {
    // open panel when first task starts
  }

  const recentTasks = tasks
    .slice()
    .sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime())
    .slice(0, 10);

  if (recentTasks.length === 0) return null;

  return (
    <>
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
      `}</style>

      <div style={{
        position: 'fixed',
        bottom: 16,
        right: 16,
        width: open ? 420 : 'auto',
        backgroundColor: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)',
        boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
        zIndex: 900,
        overflow: 'hidden',
        transition: 'width 150ms ease',
      }}>
        {/* Header / collapsed pill */}
        <div
          style={{
            display: 'flex', alignItems: 'center', gap: 8,
            padding: '0.55rem 0.9rem',
            cursor: 'pointer',
            borderBottom: open ? '1px solid var(--border)' : 'none',
            userSelect: 'none',
          }}
          onClick={() => setOpen(o => !o)}
        >
          {runningCount > 0
            ? <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--primary)', animation: 'pulse 1.2s ease-in-out infinite', display: 'inline-block' }} />
            : <span style={{ fontSize: '0.8rem' }}>🖥</span>
          }
          <span style={{ fontSize: '0.8rem', color: 'var(--text-primary)', fontWeight: 500 }}>
            {runningCount > 0
              ? `${runningCount} task${runningCount > 1 ? 's' : ''} running`
              : `${recentTasks.length} task${recentTasks.length > 1 ? 's' : ''}`
            }
          </span>
          <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem', marginLeft: 'auto' }}>
            {open ? '▼' : '▲'}
          </span>
        </div>

        {open && (
          <>
            {/* tmux attach hint */}
            <div style={{
              padding: '0.4rem 0.75rem',
              backgroundColor: 'var(--bg-elevated)',
              borderBottom: '1px solid var(--border)',
              display: 'flex', alignItems: 'center', gap: 8,
            }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                tmux attach -t {'{'}artemis{'}'}
              </span>
              <button
                onClick={() => navigator.clipboard?.writeText('tmux attach -t artemis')}
                style={{
                  marginLeft: 'auto', background: 'none', border: 'none',
                  color: 'var(--text-muted)', fontSize: '0.72rem', cursor: 'pointer',
                }}
                title="Copy to clipboard"
              >
                copy
              </button>
              <button
                onClick={fetchTasks}
                style={{
                  background: 'none', border: 'none',
                  color: 'var(--text-muted)', fontSize: '0.72rem', cursor: 'pointer',
                }}
                title="Refresh"
              >
                ↻
              </button>
            </div>

            {/* Task list */}
            <div style={{ maxHeight: 320, overflowY: 'auto' }}>
              {recentTasks.map(task => (
                <TaskRow
                  key={task.id}
                  task={task}
                  onKill={() => killTask(task.id)}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </>
  );
}
