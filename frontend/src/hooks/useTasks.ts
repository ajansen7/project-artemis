import { useState, useEffect, useCallback, useRef } from 'react';
import { API_BASE as API, fetchWithAuth } from '../lib/api';

export interface Task {
  id: string;
  name: string;
  skill: string;
  skill_args: string | null;
  source: string;
  status: 'queued' | 'running' | 'complete' | 'failed';
  output_summary: string | null;
  error: string | null;
  created_at: string;
  started_at: string | null;
  ended_at: string | null;
}

export function useTasks() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchTasks = useCallback(async () => {
    try {
      const res = await fetchWithAuth(`${API}/api/tasks`);
      if (!res.ok) return;
      const data = await res.json();
      setTasks(data.tasks ?? []);
    } catch {
      // server may not be up yet
    }
  }, []);

  // Poll whenever any task is active (queued or running)
  useEffect(() => {
    const hasActive = tasks.some(t => t.status === 'queued' || t.status === 'running');
    if (hasActive) {
      if (!intervalRef.current) {
        intervalRef.current = setInterval(fetchTasks, 3000);
      }
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [tasks, fetchTasks]);

  // Initial load
  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  // Refresh when Claude signals a task-table change via SSE
  useEffect(() => {
    const handler = (e: Event) => {
      const tables: string[] | undefined = (e as CustomEvent).detail?.tables;
      if (!tables || tables.includes('tasks') || tables.includes('task_queue')) {
        fetchTasks();
      }
    };
    window.addEventListener('artemis:refresh', handler);
    return () => window.removeEventListener('artemis:refresh', handler);
  }, [fetchTasks]);

  const pollTask = useCallback(async (taskId: string): Promise<Task> => {
    const res = await fetchWithAuth(`${API}/api/tasks/${taskId}`);
    if (!res.ok) throw new Error('Task not found');
    return res.json();
  }, []);

  const cancelTask = useCallback(async (taskId: string) => {
    await fetch(`${API}/api/tasks/${taskId}`, { method: 'DELETE' });
    fetchTasks();
  }, [fetchTasks]);

  const activeCount = tasks.filter(t => t.status === 'queued' || t.status === 'running').length;

  return { tasks, fetchTasks, pollTask, cancelTask, activeCount };
}

/** Polls a single task until it reaches a terminal state, then calls onComplete. */
export function useTaskPoller(
  taskId: string | null,
  onComplete: (task: Task) => void,
  onFailed: (task: Task) => void,
) {
  useEffect(() => {
    if (!taskId) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetchWithAuth(`${API}/api/tasks/${taskId}`);
        if (!res.ok) { clearInterval(interval); return; }
        const task: Task = await res.json();
        if (task.status === 'complete') {
          clearInterval(interval);
          onComplete(task);
        } else if (task.status === 'failed') {
          clearInterval(interval);
          onFailed(task);
        }
      } catch {
        clearInterval(interval);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [taskId]);
}
