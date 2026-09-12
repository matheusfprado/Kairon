from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 8765
    db_path: str = "data/kairon.db"
    llm_provider: Literal["ollama", "mock"] = "ollama"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2:1b"
    ollama_timeout_seconds: float = Field(default=120, gt=0, allow_inf_nan=False)
    ollama_fallback_models: str = "llama3.2:3b"
    llm_failure_cooldown_seconds: float = Field(default=30, ge=0, allow_inf_nan=False)
    conversation_timeout_seconds: int = 8
    microphone_echo_guard_seconds: float = 1.2
    stt_model: str = "base"
    stt_language: str = "pt"
    stt_beam_size: int = Field(default=1, ge=1, le=10)
    microphone_device: int | None = None
    microphone_vad_mode: int = Field(default=0, ge=0, le=3)
    microphone_speech_frames: int = Field(default=3, ge=1, le=10)
    microphone_silence_seconds: float = Field(default=0.45, ge=0.15, le=2)
    microphone_min_rms: int = Field(default=0, ge=0, le=5000)
    audio_output_device: int | None = None
    wake_word_model: str = "models/wake-word/kairon.ppn"
    wake_word_aliases: str = "kairon,cairon,kiron,kairom,caíron,kyron"
    wake_word_required: bool = True
    web_search_max_results: int = 5
    knowledge_path: str = "knowledge"
    knowledge_embedding_model: str = "nomic-embed-text-v2-moe"
    knowledge_embedding_dimensions: int = 256
    knowledge_search_limit: int = 4
    knowledge_min_score: float = 0.33
    knowledge_max_file_mb: int = 25
    tts_provider: Literal["edge", "windows"] = "edge"
    tts_voice: str = "pt-BR-AntonioNeural"
    tts_rate: str = "-3%"
    tts_pitch: str = "+0Hz"

    model_config = SettingsConfigDict(env_prefix="KAIRON_", env_file=".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()
