import json
import re
import sqlite3

from core.memory.extractor import normalize_text
from core.memory.models import MemoryCandidate, MemoryType

MEMORY_QUERY_HINTS = {
    "user_name": ("nome", "chamo"),
    "user_residence": ("moro", "moradia", "cidade", "onde vivo"),
    "user_occupation": ("trabalho", "profissao", "ocupacao"),
    "current_project": ("projeto", "trabalhando"),
}
STOP_WORDS = {
    "a", "ao", "as", "com", "como", "da", "das", "de", "do", "dos", "e", "em",
    "eu", "me", "meu", "minha", "o", "os", "para", "por", "que", "sobre", "um", "uma",
    "usuario", "voce",
}


class MemoryRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def ensure_conversation(self) -> int:
        row = self.connection.execute(
            "SELECT id FROM conversations ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row:
            return int(row["id"])

        cursor = self.connection.execute("INSERT INTO conversations (title) VALUES (?)", ("Kairon",))
        self.connection.commit()
        return int(cursor.lastrowid)

    def add_message(self, conversation_id: int, role: str, content: str) -> None:
        self.connection.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
            (conversation_id, role, content),
        )
        self.connection.execute(
            "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (conversation_id,),
        )
        self.connection.commit()

    def recent_messages(self, conversation_id: int, limit: int = 6) -> list[dict[str, str]]:
        rows = self.connection.execute(
            """
            SELECT role, content
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (conversation_id, limit),
        ).fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]

    def conversation_history(
        self,
        conversation_id: int,
        limit: int = 40,
    ) -> list[dict[str, str]]:
        rows = self.connection.execute(
            """
            SELECT role, content, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (conversation_id, limit),
        ).fetchall()
        return [
            {
                "role": str(row["role"]),
                "text": str(row["content"]),
                "created_at": str(row["created_at"]),
            }
            for row in reversed(rows)
        ]

    def user_messages(self) -> list[str]:
        rows = self.connection.execute(
            "SELECT content FROM messages WHERE role = 'user' ORDER BY id"
        ).fetchall()
        return [str(row["content"]) for row in rows]

    def add_memory(
        self,
        memory_type: MemoryType,
        content: str,
        importance: int = 5,
        metadata: dict[str, str] | None = None,
    ) -> None:
        memory_key = (metadata or {}).get("memory_key") or self._fallback_key(content)
        self.remember(
            MemoryCandidate(
                type=memory_type,
                content=content,
                importance=importance,
                key=memory_key,
            ),
            metadata=metadata,
        )

    def remember(
        self,
        candidate: MemoryCandidate,
        metadata: dict[str, str] | None = None,
    ) -> bool:
        stored_metadata = {**(metadata or {}), "memory_key": candidate.key}
        rows = self.connection.execute(
            "SELECT id, content, metadata FROM memories ORDER BY id"
        ).fetchall()
        for row in rows:
            try:
                current_metadata = json.loads(str(row["metadata"]))
            except json.JSONDecodeError:
                current_metadata = {}
            if current_metadata.get("memory_key") != candidate.key:
                continue

            changed = normalize_text(str(row["content"])) != normalize_text(candidate.content)
            self.connection.execute(
                """
                UPDATE memories
                SET type = ?, content = ?, importance = ?, metadata = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    candidate.type.value,
                    candidate.content,
                    candidate.importance,
                    json.dumps(stored_metadata, ensure_ascii=False),
                    int(row["id"]),
                ),
            )
            self.connection.commit()
            return changed

        self.connection.execute(
            "INSERT INTO memories (type, content, importance, metadata) VALUES (?, ?, ?, ?)",
            (
                candidate.type.value,
                candidate.content,
                candidate.importance,
                json.dumps(stored_metadata, ensure_ascii=False),
            ),
        )
        self.connection.commit()
        return True

    def search_memories(self, query: str, limit: int = 5) -> list[str]:
        rows = self.connection.execute(
            "SELECT type, content, importance, metadata FROM memories ORDER BY id DESC"
        ).fetchall()
        normalized_query = normalize_text(query)
        if self._requests_all_memories(normalized_query):
            return [str(row["content"]) for row in rows[:limit]]

        query_tokens = self._tokens(normalized_query)
        scored: list[tuple[float, str]] = []
        for row in rows:
            content = str(row["content"])
            normalized_content = normalize_text(content)
            content_tokens = self._tokens(normalized_content)
            overlap = len(query_tokens & content_tokens)
            score = float(overlap * 2) + int(row["importance"]) / 20

            try:
                metadata = json.loads(str(row["metadata"]))
            except json.JSONDecodeError:
                metadata = {}
            memory_key = str(metadata.get("memory_key", ""))
            for key, hints in MEMORY_QUERY_HINTS.items():
                if memory_key == key and any(hint in normalized_query for hint in hints):
                    score += 5
            if str(row["type"]) == MemoryType.PREFERENCE.value and any(
                hint in normalized_query for hint in ("gost", "prefer")
            ):
                score += 4
            if score >= 2:
                scored.append((score, content))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [content for _, content in scored[:limit]]

    def list_memories(self, limit: int = 20) -> list[str]:
        rows = self.connection.execute(
            "SELECT content FROM memories ORDER BY importance DESC, id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [str(row["content"]) for row in rows]

    def count_memories(self) -> int:
        return int(self.connection.execute("SELECT COUNT(*) FROM memories").fetchone()[0])

    @staticmethod
    def _fallback_key(content: str) -> str:
        return f"content:{normalize_text(content)}"

    @staticmethod
    def _tokens(value: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-z0-9]+", value)
            if len(token) > 2 and token not in STOP_WORDS
        }

    @staticmethod
    def _requests_all_memories(query: str) -> bool:
        return any(
            phrase in query
            for phrase in (
                "o que voce lembra",
                "o que sabe sobre mim",
                "suas memorias",
                "memoria sobre mim",
                "tudo que lembra",
            )
        )
