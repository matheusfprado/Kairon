import sqlite3

import numpy as np

from core.knowledge.models import DocumentState, KnowledgeChunk, KnowledgeMatch


class KnowledgeRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def document_states(self) -> dict[str, DocumentState]:
        rows = self.connection.execute(
            "SELECT path, sha256, modified_ns, file_size FROM knowledge_documents"
        ).fetchall()
        return {
            str(row["path"]): DocumentState(
                path=str(row["path"]),
                sha256=str(row["sha256"]),
                modified_ns=int(row["modified_ns"]),
                file_size=int(row["file_size"]),
            )
            for row in rows
        }

    def replace_document(
        self,
        path: str,
        title: str,
        file_type: str,
        sha256: str,
        modified_ns: int,
        file_size: int,
        chunks: list[KnowledgeChunk],
        embeddings: list[list[float]],
    ) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("Cada fragmento precisa de um embedding.")

        with self.connection:
            existing = self.connection.execute(
                "SELECT id FROM knowledge_documents WHERE path = ?", (path,)
            ).fetchone()
            if existing:
                document_id = int(existing["id"])
                self.connection.execute(
                    "DELETE FROM knowledge_chunks WHERE document_id = ?", (document_id,)
                )
                self.connection.execute(
                    """
                    UPDATE knowledge_documents
                    SET title = ?, file_type = ?, sha256 = ?, modified_ns = ?, file_size = ?,
                        indexed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (title, file_type, sha256, modified_ns, file_size, document_id),
                )
            else:
                cursor = self.connection.execute(
                    """
                    INSERT INTO knowledge_documents
                      (path, title, file_type, sha256, modified_ns, file_size)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (path, title, file_type, sha256, modified_ns, file_size),
                )
                document_id = int(cursor.lastrowid)

            rows = []
            for chunk, embedding in zip(chunks, embeddings, strict=True):
                vector = np.asarray(embedding, dtype="<f4")
                rows.append(
                    (
                        document_id,
                        chunk.index,
                        chunk.page_number,
                        chunk.content,
                        vector.tobytes(),
                        int(vector.size),
                    )
                )
            self.connection.executemany(
                """
                INSERT INTO knowledge_chunks
                  (document_id, chunk_index, page_number, content, embedding, embedding_dimensions)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                rows,
            )

    def update_file_metadata(self, path: str, modified_ns: int, file_size: int) -> None:
        with self.connection:
            self.connection.execute(
                """
                UPDATE knowledge_documents
                SET modified_ns = ?, file_size = ?
                WHERE path = ?
                """,
                (modified_ns, file_size, path),
            )

    def remove_missing(self, existing_paths: set[str]) -> int:
        states = self.document_states()
        missing = set(states) - existing_paths
        if not missing:
            return 0
        with self.connection:
            for path in missing:
                row = self.connection.execute(
                    "SELECT id FROM knowledge_documents WHERE path = ?", (path,)
                ).fetchone()
                if row:
                    self.connection.execute(
                        "DELETE FROM knowledge_chunks WHERE document_id = ?", (int(row["id"]),)
                    )
                    self.connection.execute("DELETE FROM knowledge_documents WHERE id = ?", (row["id"],))
        return len(missing)

    def search(
        self,
        query_embedding: list[float],
        limit: int,
        min_score: float,
    ) -> list[KnowledgeMatch]:
        query = np.asarray(query_embedding, dtype=np.float32)
        query_norm = float(np.linalg.norm(query))
        if query_norm == 0:
            return []

        rows = self.connection.execute(
            """
            SELECT d.title, d.path, c.page_number, c.content, c.embedding,
                   c.embedding_dimensions
            FROM knowledge_chunks c
            JOIN knowledge_documents d ON d.id = c.document_id
            WHERE c.embedding_dimensions = ?
            """,
            (int(query.size),),
        ).fetchall()
        scored = []
        for row in rows:
            vector = np.frombuffer(row["embedding"], dtype="<f4")
            denominator = query_norm * float(np.linalg.norm(vector))
            score = float(np.dot(query, vector) / denominator) if denominator else 0.0
            if score >= min_score:
                scored.append(
                    KnowledgeMatch(
                        content=str(row["content"]),
                        title=str(row["title"]),
                        path=str(row["path"]),
                        page_number=int(row["page_number"]) if row["page_number"] else None,
                        score=score,
                    )
                )
        scored.sort(key=lambda match: match.score, reverse=True)
        return scored[:limit]

    def status(self) -> tuple[int, int]:
        documents = int(
            self.connection.execute("SELECT COUNT(*) FROM knowledge_documents").fetchone()[0]
        )
        chunks = int(
            self.connection.execute("SELECT COUNT(*) FROM knowledge_chunks").fetchone()[0]
        )
        return documents, chunks
