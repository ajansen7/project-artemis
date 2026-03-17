import { useState, useEffect, useCallback, useRef } from 'react';

export interface Task {
  id: string;
  name: string;
  status: 'running' | 'complete' | 'failed';
  started_at: string;
  ended_at: string | null;
  tmux_window: string;
  output?: string;
}

const API = 'http://localhost:8000';

export function useTasks() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchTasks = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/tasks`);
      if (!res.ok) return;
      const data = await res.json();
      setTasks(data.tasks ?? []);
    } catch {
      // server may not be up yet
    }
  }, []);

  // Poll whenever any task is running
  useEffect(() => {
    const hasRunning = tasks.some(t => t.status === 'running');
    if (hasRunning) {
      if (!intervalRef.current) {
        intervalRef.current = setInterval(fetchTasks, 2000);
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

  const pollTask = useCallback(async (taskId: string): Promise<Task> => {
    const res = await fetch(`${API}/api/tasks/${taskId}`);
    if (!res.ok) throw new Error('Task not found');
    return res.json();
  }, []);

  const killTask = useCallback(async (taskId: string) => {
    await fetch(`${API}/api/tasks/${taskId}`, { method: 'DELETE' });
    fetchTasks();
  }, [fetchTasks]);

  const runningCount = tasks.filter(t => t.status === 'running').length;

  return { tasks, fetchTasks, pollTask, killTask, runningCount };
}

/** Polls a single task until it reaches a terminal state, then calls onComplete. */
export function useTaskPoller(
  taskId: string | null,
  onComplete: (task: Task) => void,
  onFailed: (task: Task) => void,
) {
  const { pollTask } = useTasks();

  useEffect(() => {
    if (!taskId) return;

    const interval = setInterval(async () => {
      try {
        const task = await pollTask(taskId);
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
    }, 2000);

    return () => clearInterval(interval);
  }, [taskId]);
}
