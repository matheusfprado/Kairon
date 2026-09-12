from dataclasses import dataclass

from pydantic import BaseModel


class DocumentSection(BaseModel):
    text: str
    page_number: int | None = None


class KnowledgeChunk(BaseModel):
    index: int
    content: str
    page_number: int | None = None


class KnowledgeMatch(BaseModel):
    content: str
    title: str
    path: str
    page_number: int | None = None
    score: float

    @property
    def source_title(self) -> str:
        if self.page_number is not None:
            return f"{self.title} - pagina {self.page_number}"
        return self.title


class KnowledgeStatus(BaseModel):
    documents: int
    chunks: int
    indexed: int = 0
    removed: int = 0
    failed: int = 0


@dataclass(frozen=True)
class DocumentState:
    path: str
    sha256: str
    modified_ns: int
    file_size: int
