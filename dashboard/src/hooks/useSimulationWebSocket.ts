import { useEffect, useMemo, useRef, useState } from 'react';

import { useSimulationStore } from '../store/simulationStore';
import type { StepEvent } from '../types';

const MAX_RETRIES = 5;
const BASE_DELAY_MS = 500;

export function useSimulationWebSocket(runId: string | null, mode: 'live' | 'replay' = 'live') {
  const {
    handleStepEvent,
    handleEpisodeEnd,
    handleSimulationEnd,
    setWebSocketState,
  } = useSimulationStore();
  const wsRef = useRef<WebSocket | null>(null);
  const retriesRef = useRef(0);
  const closedRef = useRef(false);
  const [connectionState, setConnectionState] = useState<'idle' | 'connecting' | 'open' | 'closed' | 'error'>('idle');

  const socketUrl = useMemo(() => {
    if (!runId) return null;
    const isHttps = window.location.protocol === 'https:';
    const protocol = isHttps ? 'wss' : 'ws';
    const host = import.meta.env.DEV
      ? 'localhost:8000'
      : window.location.host;
    const suffix = mode === 'live' ? 'stream' : 'replay';
    return `${protocol}://${host}/simulation/${runId}/${suffix}`;
  }, [mode, runId]);

  useEffect(() => {
    if (!socketUrl || !runId) return;

    closedRef.current = false;
    retriesRef.current = 0;

    const connect = () => {
      if (closedRef.current) return;
      setConnectionState('connecting');
      setWebSocketState('connecting');

      const socket = new WebSocket(socketUrl);
      wsRef.current = socket;

      socket.onopen = () => {
        retriesRef.current = 0;
        setConnectionState('open');
        setWebSocketState('open');
      };

      socket.onmessage = (message) => {
        const event = JSON.parse(message.data) as StepEvent;
        if (event.type === 'step') {
          handleStepEvent(event);
        } else if (event.type === 'episode_end') {
          handleEpisodeEnd(event);
        } else if (event.type === 'simulation_end') {
          handleSimulationEnd(event);
          setConnectionState('closed');
          setWebSocketState('closed');
        } else if (event.type === 'error') {
          handleSimulationEnd(event);
          setConnectionState('error');
          setWebSocketState('error');
        }
      };

      socket.onerror = () => {
        setConnectionState('error');
        setWebSocketState('error');
      };

      socket.onclose = () => {
        if (closedRef.current) {
          setConnectionState('closed');
          setWebSocketState('closed');
          return;
        }

        if (retriesRef.current < MAX_RETRIES) {
          const delay = BASE_DELAY_MS * 2 ** retriesRef.current;
          retriesRef.current += 1;
          window.setTimeout(connect, delay);
        } else {
          setConnectionState('closed');
          setWebSocketState('closed');
        }
      };
    };

    connect();

    return () => {
      closedRef.current = true;
      wsRef.current?.close();
      wsRef.current = null;
      setWebSocketState('closed');
    };
  }, [handleEpisodeEnd, handleSimulationEnd, handleStepEvent, runId, setWebSocketState, socketUrl]);

  return { connectionState };
}
