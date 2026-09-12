import re
from pathlib import Path

from pypdf import PdfReader

from core.knowledge.models import DocumentSection, KnowledgeChunk

SUPPORTED_EXTENSIONS = {".md", ".pdf", ".txt"}


class DocumentLoader:
    def __init__(self, max_file_bytes: int) -> None:
        self.max_file_bytes = max_file_bytes

    def load(self, path: Path) -> list[DocumentSection]:
        if path.stat().st_size > self.max_file_bytes:
            raise ValueError(f"Documento excede {self.max_file_bytes // 1_048_576} MB.")

        extension = path.suffix.lower()
        if extension == ".pdf":
            return self._load_pdf(path)
        if extension in {".md", ".txt"}:
            return [DocumentSection(text=self._read_text(path))]
        raise ValueError(f"Formato nao suportado: {extension}")

    @staticmethod
    def _load_pdf(path: Path) -> list[DocumentSection]:
        reader = PdfReader(path)
        sections = []
        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                sections.append(DocumentSection(text=text, page_number=page_number))
        return sections

    @staticmethod
    def _read_text(path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            return path.read_text(encoding="cp1252")


class DocumentChunker:
    def __init__(self, chunk_size: int = 1200, overlap: int = 180) -> None:
        if overlap >= chunk_size:
            raise ValueError("O overlap deve ser menor que o tamanho do fragmento.")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split(self, sections: list[DocumentSection]) -> list[KnowledgeChunk]:
        chunks: list[KnowledgeChunk] = []
        for section in sections:
            text = self._normalize(section.text)
            start = 0
            while start < len(text):
                end = min(start + self.chunk_size, len(text))
                if end < len(text):
                    boundary = max(text.rfind("\n", start, end), text.rfind(" ", start, end))
                    if boundary > start + self.chunk_size // 2:
                        end = boundary

                content = text[start:end].strip()
                if content:
                    chunks.append(
                        KnowledgeChunk(
                            index=len(chunks),
                            content=content,
                            page_number=section.page_number,
                        )
                    )
                if end >= len(text):
                    break
                start = max(end - self.overlap, start + 1)
        return chunks

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.replace("\x00", " ").replace("\r\n", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
