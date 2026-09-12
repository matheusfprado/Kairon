from enum import StrEnum

from pydantic import BaseModel, Field


class MemoryType(StrEnum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    PROJECT = "project"
    PREFERENCE = "preference"
    FACT = "fact"


class Memory(BaseModel):
    id: int
    type: MemoryType
    content: str
    importance: int = Field(ge=1, le=10)
    metadata: str = "{}"


class MemoryCandidate(BaseModel):
    type: MemoryType
    content: str
    importance: int = Field(default=7, ge=1, le=10)
    key: str
