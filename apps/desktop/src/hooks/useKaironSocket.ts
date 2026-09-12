import { useEffect, useMemo, useRef } from "react";
import { KaironSocket } from "../services/kaironSocket";
import { useKaironStore } from "../stores/kaironStore";
import type { ClientEvent, ServerEvent } from "../types/kairon";

export function useKaironSocket(enabled = true, voice = true) {
  const socketRef = useRef<KaironSocket | null>(null);
  const setState = useKaironStore((store) => store.setState);
  const setConnected = useKaironStore((store) => store.setConnected);
  const setTranscript = useKaironStore((store) => store.setTranscript);
  const setResponse = useKaironStore((store) => store.setResponse);
  const setMemoryCount = useKaironStore((store) => store.setMemoryCount);
  const setMessages = useKaironStore((store) => store.setMessages);
  const addMessage = useKaironStore((store) => store.addMessage);
  const appendAssistantDelta = useKaironStore((store) => store.appendAssistantDelta);
  const finalizeAssistant = useKaironStore((store) => store.finalizeAssistant);

  useEffect(() => {
    if (!enabled) return;
    const socket = new KaironSocket(
      `ws://127.0.0.1:8765/ws?voice=${voice}`,
      (event: ServerEvent) => {
        if (event.type === "state_changed") {
          setState(event.state);
        }

        if (event.type === "transcription") {
          setResponse("");
          setTranscript(event.text);
          addMessage({ role: "user", text: event.text });
        }

        if (event.type === "assistant_message") {
          finalizeAssistant(event.text, event.sources);
        }

        if (event.type === "assistant_delta") {
          appendAssistantDelta(event.text);
        }

        if (event.type === "conversation_history") {
          setMessages(
            event.messages.map((message, index) => ({
              id: `history-${message.created_at}-${index}`,
              role: message.role,
              text: message.text,
              createdAt: `${message.created_at.replace(" ", "T")}Z`,
            })),
          );
        }

        if (event.type === "memory_status") {
          setMemoryCount(event.count);
        }

        if (event.type === "speaking_started") {
          setState("speaking");
        }

        if (event.type === "error") {
          setState("error");
          addMessage({ role: "system", text: event.message });
        }
      },
      (connected) => {
        setConnected(connected);
        if (!connected) {
          setState("offline");
        }
      },
    );

    socketRef.current = socket;
    socket.connect();

    return () => { socket.disconnect(); socketRef.current = null; };
  }, [
    enabled,
    voice,
    addMessage,
    appendAssistantDelta,
    finalizeAssistant,
    setConnected,
    setMemoryCount,
    setMessages,
    setResponse,
    setState,
    setTranscript,
  ]);

  return useMemo(
    () => ({
      send: (event: ClientEvent) => socketRef.current?.send(event),
    }),
    [],
  );
}
