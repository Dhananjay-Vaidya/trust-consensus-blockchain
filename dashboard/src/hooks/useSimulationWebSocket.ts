import { useEffect, useRef, useState } from 'react';
import { useSimulationStore } from '../store/simulationStore';
import type { StepEvent } from '../types';

const MAX_RETRIES = 5;
const BASE_DELAY_MS = 500;

export function useSimulationWebSocket(runId: string | null) {
  const { handleStepEvent, handleEpisodeEnd, setWs, setStatus } =
    useSimulationStore();
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef(0);
  const stopRef = useRef(false);
  const [lastEvent, setLastEvent] = useState<StepEvent | null>(null);
  const [reconnectCount, setReconnectCount] = useState(0);
  const [wsStatus, setWsStatus] = useState<
    'idle' | 'connecting' | 'open' | 'closed' | 'error'
  >('idle');

  useEffect(() => {
    if (!runId) return;

    stopRef.current = false;
    retryRef.current = 0;

    function connect() {
      if (stopRef.current) return;

      const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
      // In dev (Vite proxy) the same host works; in prod the API is same-origin
      const host = window.location.host;
      const url = `${proto}://${host}/simulation/${runId}/stream`;

      setWsStatus('connecting');
      const ws = new WebSocket(url);
      wsRef.current = ws;
      setWs(ws);

      ws.onopen = () => {
        setWsStatus('open');
        retryRef.current = 0;
        setReconnectCount((c) => c + 1);
      };

      ws.onmessage = (e) => {
        try {
          const event: StepEvent = JSON.parse(e.data);
          setLastEvent(event);

          if (event.type === 'step') {
            handleStepEvent(event);
          } else if (event.type === 'episode_end') {
            handleEpisodeEnd(event);
          } else if (event.type === 'simulation_end') {
            setStatus('completed');
            setWsStatus('closed');
            ws.close();
          } else if (event.type === 'error') {
            setStatus('error');
            setWsStatus('error');
            console.error('[WS] simulation error:', event.action_description);
            ws.close();
          }
        } catch (err) {
          console.warn('[WS] parse error', err);
        }
      };

      ws.onerror = () => {
        setWsStatus('error');
      };

      ws.onclose = () => {
        setWs(null);
        if (stopRef.current) {
          setWsStatus('closed');
          return;
        }
        if (retryRef.current < MAX_RETRIES) {
          const delay = BASE_DELAY_MS * Math.pow(2, retryRef.current);
          retryRef.current += 1;
          setTimeout(connect, delay);
        } else {
          setWsStatus('closed');
          setStatus('error');
        }
      };
    }

    connect();

    return () => {
      stopRef.current = true;
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      setWs(null);
    };
  }, [runId]);

  return { status: wsStatus, lastEvent, reconnectCount };
}
