from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class KaironState(StrEnum):
    IDLE = "idle"
    LISTENING_FOR_WAKE_WORD = "listening_for_wake_word"
    WAKE_WORD_DETECTED = "wake_word_detected"
    LISTENING = "listening"
    PROCESSING = "processing"
    THINKING = "thinking"
    SPEAKING = "speaking"
    EXECUTING = "executing"
    ERROR = "error"
    OFFLINE = "offline"


class StateChangedEvent(BaseModel):
    type: Literal["state_changed"] = "state_changed"
    state: KaironState


class TranscriptionEvent(BaseModel):
    type: Literal["transcription"] = "transcription"
    text: str


class ResponseSourceEvent(BaseModel):
    title: str
    url: str


class AssistantMessageEvent(BaseModel):
    type: Literal["assistant_message"] = "assistant_message"
    text: str
    sources: list[ResponseSourceEvent] = Field(default_factory=list)


class AssistantDeltaEvent(BaseModel):
    type: Literal["assistant_delta"] = "assistant_delta"
    text: str


class ConversationMessageEvent(BaseModel):
    role: Literal["user", "assistant", "system"]
    text: str
    created_at: str


class ConversationHistoryEvent(BaseModel):
    type: Literal["conversation_history"] = "conversation_history"
    messages: list[ConversationMessageEvent]


class MemoryStatusEvent(BaseModel):
    type: Literal["memory_status"] = "memory_status"
    count: int


class SpeakingStartedEvent(BaseModel):
    type: Literal["speaking_started"] = "speaking_started"


class SpeakingFinishedEvent(BaseModel):
    type: Literal["speaking_finished"] = "speaking_finished"


class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    message: str


ServerEvent = (
    StateChangedEvent
    | TranscriptionEvent
    | AssistantMessageEvent
    | AssistantDeltaEvent
    | ConversationHistoryEvent
    | MemoryStatusEvent
    | SpeakingStartedEvent
    | SpeakingFinishedEvent
    | ErrorEvent
)


class ClientEvent(BaseModel):
    type: Literal["submit_text", "mock_wake_word", "stop_speaking"]
    text: str | None = Field(default=None, max_length=4000)
    speak: bool = True
