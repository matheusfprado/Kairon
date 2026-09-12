import { create } from "zustand";
import type { KaironState, Message } from "../types/kairon";

interface KaironStore {
  state: KaironState;
  transcript: string;
  response: string;
  connected: boolean;
  microphoneActive: boolean;
  memoryCount: number;
  messages: Message[];
  setState: (state: KaironState) => void;
  setConnected: (connected: boolean) => void;
  setTranscript: (transcript: string) => void;
  setResponse: (response: string) => void;
  setMemoryCount: (count: number) => void;
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Omit<Message, "id" | "createdAt">) => void;
  appendAssistantDelta: (text: string) => void;
  finalizeAssistant: (text: string, sources: Message["sources"]) => void;
  upsertMessage: (id: string, role: Message["role"], text: string, append?: boolean) => void;
}

export const useKaironStore = create<KaironStore>((set) => ({
  state: "idle",
  transcript: "",
  response: "",
  connected: false,
  microphoneActive: false,
  memoryCount: 0,
  messages: [],
  setState: (state) =>
    set({
      state,
      microphoneActive: state === "listening_for_wake_word" || state === "listening",
    }),
  setConnected: (connected) => set({ connected }),
  setTranscript: (transcript) => set({ transcript }),
  setResponse: (response) => set({ response }),
  setMemoryCount: (memoryCount) => set({ memoryCount }),
  setMessages: (messages) => set({ messages }),
  upsertMessage: (id, role, text, append = false) => set((current) => {
    const existing = current.messages.find((message) => message.id === id);
    const content = append ? (existing?.text ?? "") + text : text;
    const message: Message = { id, role, text: content,
      createdAt: existing?.createdAt ?? new Date().toISOString() };
    return {
      messages: existing ? current.messages.map((item) => item.id === id ? message : item)
        : [...current.messages, message],
      ...(role === "assistant" ? { response: content } : {}),
    };
  }),
  addMessage: (message) =>
    set((current) => ({
      messages: [
        ...current.messages,
        {
          ...message,
          id: crypto.randomUUID(),
          createdAt: new Date().toISOString(),
        },
      ],
    })),
  appendAssistantDelta: (text) =>
    set((current) => {
      const messages = [...current.messages];
      const last = messages.at(-1);
      if (last?.role === "assistant" && last.id.startsWith("stream-")) {
        messages[messages.length - 1] = { ...last, text: last.text + text };
      } else {
        messages.push({
          id: `stream-${crypto.randomUUID()}`,
          role: "assistant",
          text,
          createdAt: new Date().toISOString(),
        });
      }
      return { messages, response: current.response + text };
    }),
  finalizeAssistant: (text, sources) =>
    set((current) => {
      const messages = [...current.messages];
      const last = messages.at(-1);
      if (last?.role === "assistant" && last.id.startsWith("stream-")) {
        messages[messages.length - 1] = { ...last, id: crypto.randomUUID(), text, sources };
      } else {
        messages.push({
          id: crypto.randomUUID(), role: "assistant", text, sources,
          createdAt: new Date().toISOString(),
        });
      }
      return { messages, response: text };
    }),
}));
