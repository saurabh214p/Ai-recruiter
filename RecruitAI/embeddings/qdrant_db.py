"""
RecruitAI - Qdrant Vector Database Manager
Handles collection creation, resume storage, and similarity search.

Uses Qdrant in-memory mode — no Docker or external server required.
Data persists within the Python process lifetime.
"""

import logging
import os
import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

logger = logging.getLogger(__name__)


class QdrantManager:
    """Manages the Qdrant vector database for student resumes.

    Collection schema:
        - id: UUID string
        - vector: Dense embedding (384-d for bge-small-en-v1.5)
        - payload: {student_name, skills, projects, education,
                     experience, summary, resume_path}
    """

    def __init__(
        self,
        collection_name: str | None = None,
        dimension: int | None = None,
    ):
        """Initialize the Qdrant client and ensure collection exists.

        Args:
            collection_name: Qdrant collection name. Defaults to QDRANT_COLLECTION env var.
            dimension: Embedding vector dimension. Defaults to EMBEDDING_DIMENSION env var.
        """
        self.collection_name = collection_name or os.getenv(
            "QDRANT_COLLECTION", "student_resumes"
        )
        self.dimension = dimension or int(
            os.getenv("EMBEDDING_DIMENSION", "384")
        )

        logger.info("Initializing Qdrant client (in-memory mode)")
        self.client = QdrantClient(":memory:")
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Create the collection if it doesn't already exist."""
        existing = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in existing:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.dimension,
                    distance=Distance.COSINE,
                ),
            )
            logger.info(
                f"Created collection '{self.collection_name}' "
                f"(dim={self.dimension}, distance=COSINE)"
            )
        else:
            logger.info(f"Collection '{self.collection_name}' already exists")

    def upsert_resume(
        self, resume_data: dict[str, Any], embedding: list[float]
    ) -> str:
        """Store a resume embedding with its metadata payload.

        Args:
            resume_data: Resume metadata dict. Expected keys:
                student_name, skills, projects, education,
                experience, summary, resume_path.
            embedding: Dense vector embedding of the resume.

        Returns:
            The generated point ID (UUID string).
        """
        point_id = str(uuid.uuid4())

        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=resume_data,
                )
            ],
        )

        logger.info(
            f"Stored resume for '{resume_data.get('student_name', 'Unknown')}' "
            f"(id={point_id[:8]}…)"
        )
        return point_id

    def search(
        self, query_embedding: list[float], limit: int = 20
    ) -> list[dict[str, Any]]:
        """Search for similar resumes by embedding vector.

        Args:
            query_embedding: Query vector (e.g., from a job description).
            limit: Maximum number of results to return.

        Returns:
            List of dicts with 'score' key and all payload fields,
            sorted by descending cosine similarity.
        """
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=limit,
        )

        candidates = [
            {
                "score": hit.score,
                **(hit.payload or {}),  # Flatten payload fields into dict
            }
            for hit in response.points
        ]

        logger.info(f"Qdrant search returned {len(candidates)} candidates")
        return candidates

    def get_count(self) -> int:
        """Get the number of stored resume vectors.

        Returns:
            Total points count in the collection.
        """
        info = self.client.get_collection(self.collection_name)
        return info.points_count

    def check_duplicate(self, student_name: str) -> bool:
        """Check if a resume for this student name already exists.

        Args:
            student_name: Student name to check.

        Returns:
            True if a resume with this name exists.
        """
        points, _ = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="student_name",
                        match=MatchValue(value=student_name),
                    )
                ]
            ),
            limit=1,
        )
        return len(points) > 0


# ================================================================
# Module-level Singleton
# ================================================================
# Critical: Both student and recruiter pages MUST share the same
# in-memory Qdrant instance so resumes uploaded by students are
# visible when recruiters search.
_qdrant_instance: QdrantManager | None = None


def get_qdrant_manager() -> QdrantManager:
    """Get or create the singleton QdrantManager instance.

    Returns:
        Shared QdrantManager with persistent in-memory data.
    """
    global _qdrant_instance
    if _qdrant_instance is None:
        _qdrant_instance = QdrantManager()
    return _qdrant_instance
