export type KaironState =
  | "idle"
  | "listening_for_wake_word"
  | "wake_word_detected"
  | "listening"
  | "processing"
  | "thinking"
  | "speaking"
  | "executing"
  | "error"
  | "offline";

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  text: string;
  sources?: ResponseSource[];
  createdAt: string;
}

export interface ResponseSource {
  title: string;
  url: string;
}

export interface StoredMessage {
  role: "user" | "assistant" | "system";
  text: string;
  created_at: string;
}

export type ServerEvent =
  | { type: "state_changed"; state: KaironState }
  | { type: "transcription"; text: string }
  | { type: "assistant_message"; text: string; sources: ResponseSource[] }
  | { type: "assistant_delta"; text: string }
  | { type: "conversation_history"; messages: StoredMessage[] }
  | { type: "memory_status"; count: number }
  | { type: "speaking_started" }
  | { type: "speaking_finished" }
  | { type: "error"; message: string };

export type ClientEvent =
  | { type: "submit_text"; text: string; speak?: boolean }
  | { type: "mock_wake_word" }
  | { type: "stop_speaking" };
