import { useEffect } from 'react';
import { API_BASE } from '../lib/api';

/**
 * Connects to the FastAPI SSE stream and fires window custom events when
 * Claude signals a UI refresh. Mount once at the top of the component tree.
 *
 * Downstream hooks listen for 'artemis:refresh' and refetch their data.
 * Event detail: { tables: string[] } — empty/absent means refresh everything.
 */
export function useEvents() {
  useEffect(() => {
    const es = new EventSource(`${API_BASE}/api/events`);
    es.onmessage = (e) => {
      try {
        const payload = JSON.parse(e.data);
        if (payload.event === 'refresh') {
          window.dispatchEvent(
            new CustomEvent('artemis:refresh', { detail: payload.data ?? {} })
          );
        }
      } catch {
        // ignore malformed messages
      }
    };
    return () => es.close();
  }, []);
}
