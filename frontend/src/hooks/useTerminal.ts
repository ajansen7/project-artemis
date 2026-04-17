import { useEffect, useRef, useCallback, useState } from 'react';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import { WebLinksAddon } from '@xterm/addon-web-links';
import { supabase } from '../lib/supabase';

export type TerminalStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

interface UseTerminalOptions {
  /** DOM element to mount the terminal into */
  containerRef: React.RefObject<HTMLDivElement | null>;
}

export function useTerminal({ containerRef }: UseTerminalOptions) {
  const [status, setStatus] = useState<TerminalStatus>('disconnected');
  const [error, setError] = useState<string | null>(null);

  const termRef = useRef<Terminal | null>(null);
  const fitRef = useRef<FitAddon | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const disposablesRef = useRef<{ dispose: () => void }[]>([]);

  const connect = useCallback(async () => {
    const container = containerRef.current;
    if (!container) return;

    // Get auth token
    const { data: { session } } = await supabase.auth.getSession();
    if (!session?.access_token) {
      setError('Not authenticated');
      setStatus('error');
      return;
    }

    setStatus('connecting');
    setError(null);

    // ─── Create terminal if not yet created ───────────────────
    if (!termRef.current) {
      const term = new Terminal({
        cursorBlink: true,
        fontSize: 14,
        fontFamily: 'Menlo, Monaco, "Courier New", monospace',
        theme: {
          background: '#1e1e1e',
          foreground: '#d4d4d4',
          cursor: '#d4d4d4',
          selectionBackground: '#264f78',
        },
        allowProposedApi: true,
      });

      const fitAddon = new FitAddon();
      term.loadAddon(fitAddon);
      term.loadAddon(new WebLinksAddon());
      term.open(container);
      fitAddon.fit();

      termRef.current = term;
      fitRef.current = fitAddon;
    }

    const term = termRef.current;

    // ─── WebSocket connection ─────────────────────────────────
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/terminal`;
    const ws = new WebSocket(wsUrl);
    ws.binaryType = 'arraybuffer';
    wsRef.current = ws;

    ws.onopen = () => {
      // Send auth token as first message
      ws.send(JSON.stringify({ token: session.access_token }));
      setStatus('connected');

      // Send initial size
      const dims = fitRef.current?.proposeDimensions();
      if (dims) {
        ws.send(JSON.stringify({ type: 'resize', rows: dims.rows, cols: dims.cols }));
      }
    };

    ws.onmessage = (event) => {
      if (event.data instanceof ArrayBuffer) {
        term.write(new Uint8Array(event.data));
      } else {
        term.write(event.data);
      }
    };

    ws.onclose = (event) => {
      setStatus('disconnected');
      if (event.code === 4001) {
        setError('Authentication failed');
      } else if (event.code === 4003) {
        setError(event.reason || 'Access denied');
      } else if (event.code === 4004) {
        setError(event.reason || 'Orchestrator not running');
      } else if (event.code !== 1000) {
        setError('Connection lost');
        // Auto-reconnect after 3 seconds
        reconnectTimer.current = setTimeout(() => connect(), 3000);
      }
    };

    ws.onerror = () => {
      setStatus('error');
      setError('WebSocket connection failed');
    };

    // ─── Clean up old input handlers before registering new ones ─
    disposablesRef.current.forEach(d => d.dispose());
    disposablesRef.current = [];

    // ─── Terminal input → WebSocket ───────────────────────────
    const inputDisposable = term.onData((data) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(new TextEncoder().encode(data));
      }
    });

    // ─── Terminal binary input (for special keys) ─────────────
    const binaryDisposable = term.onBinary((data) => {
      if (ws.readyState === WebSocket.OPEN) {
        const buffer = new Uint8Array(data.length);
        for (let i = 0; i < data.length; i++) {
          buffer[i] = data.charCodeAt(i) & 0xff;
        }
        ws.send(buffer);
      }
    });

    disposablesRef.current = [inputDisposable, binaryDisposable];
  }, [containerRef]);

  const disconnect = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
    disposablesRef.current.forEach(d => d.dispose());
    disposablesRef.current = [];
    if (wsRef.current) {
      wsRef.current.close(1000);
      wsRef.current = null;
    }
    setStatus('disconnected');
    setError(null);
  }, []);

  // Handle container resize
  useEffect(() => {
    const handleResize = () => {
      if (fitRef.current && termRef.current) {
        fitRef.current.fit();
        const dims = fitRef.current.proposeDimensions();
        if (dims && wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(
            JSON.stringify({ type: 'resize', rows: dims.rows, cols: dims.cols })
          );
        }
      }
    };

    window.addEventListener('resize', handleResize);

    // Also observe the container for size changes
    const observer = new ResizeObserver(handleResize);
    if (containerRef.current) {
      observer.observe(containerRef.current);
    }

    return () => {
      window.removeEventListener('resize', handleResize);
      observer.disconnect();
    };
  }, [containerRef]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
      if (termRef.current) {
        termRef.current.dispose();
        termRef.current = null;
      }
    };
  }, [disconnect]);

  return { status, error, connect, disconnect, terminal: termRef };
}
