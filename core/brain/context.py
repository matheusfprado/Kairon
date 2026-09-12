from pydantic import BaseModel, Field

from core.knowledge.models import KnowledgeMatch


class KaironContext(BaseModel):
    conversation_id: int
    user_input: str
    recent_messages: list[dict[str, str]]
    memories: list[str]
    memory_updates: list[str] = Field(default_factory=list)
    web_context: list[str] = Field(default_factory=list)
    knowledge_context: list[KnowledgeMatch] = Field(default_factory=list)
