import { useEffect } from "react";
import { useSimulationStore } from "../store/simulationStore";
import type { StepEvent } from "../types";
export function useSimulationWebSocket(
  runId: string | null,
  mode: "live" | "replay" = "live",
  streamVersion = 0,
) {
  useEffect(() => {
    if (!runId) return;
    let disposed = false,
      finished = false,
      retries = 0,
      socket: WebSocket | null = null,
      timer: ReturnType<typeof setTimeout> | undefined;
    const state = () => useSimulationStore.getState();
    const url = new URL(
      import.meta.env.VITE_API_URL || window.location.origin,
      window.location.origin,
    );
    url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
    url.pathname = `/simulation/${runId}/${mode === "live" ? "stream" : "replay"}`;
    const connect = () => {
      if (disposed || finished) return;
      state().setWebSocketState("connecting");
      socket = new WebSocket(url.toString());
      socket.onopen = () => {
        if (disposed) return;
        retries = 0;
        state().setWebSocketState("open");
      };
      socket.onmessage = (message) => {
        if (disposed) return;
        try {
          const event = JSON.parse(message.data) as StepEvent;
          if (event.type === "step") state().handleStepEvent(event);
          else if (event.type === "episode_end")
            state().handleEpisodeEnd(event);
          else if (event.type === "simulation_end") {
            finished = true;
            state().handleSimulationEnd(event);
            state().setWebSocketState("closed");
          } else if (event.type === "error") {
            finished = true;
            if (event.trust_scores) state().handleStepEvent(event);
            useSimulationStore.setState({ status: "error" });
            state().setWebSocketState("error");
          }
        } catch {
          state().setWebSocketState("error");
        }
      };
      socket.onerror = () => {
        if (!disposed) state().setWebSocketState("error");
      };
      socket.onclose = () => {
        if (disposed || finished) return;
        if (retries < 5) {
          timer = setTimeout(connect, 500 * 2 ** retries++);
        } else {
          state().setWebSocketState("error");
          useSimulationStore.setState({ status: "error" });
        }
      };
    };
    connect();
    return () => {
      disposed = true;
      clearTimeout(timer);
      socket?.close();
      state().setWebSocketState("closed");
    };
  }, [runId, mode, streamVersion]);
  return { connectionState: useSimulationStore((s) => s.webSocketState) };
}
