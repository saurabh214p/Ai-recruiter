"""
RecruitAI - Retrieval Agent (LangGraph Node)
Generates JD embeddings and searches Qdrant for matching candidates.

Responsibilities:
- Build a rich text representation from parsed JD data
- Generate a dense embedding vector
- Query Qdrant for top-N similar resumes
- Return candidate list with similarity scores
"""

import logging
from typing import Any

from embeddings.embedder import Embedder
from embeddings.qdrant_db import QdrantManager
from models.schemas import RecruitmentState
from utils.helper import build_embedding_text

logger = logging.getLogger(__name__)


class RetrievalAgent:
    """Searches the vector database for candidates matching a job description.

    Uses semantic embedding similarity to find the most relevant
    resumes from the Qdrant collection.
    """

    def __init__(self, embedder: Embedder, qdrant_manager: QdrantManager):
        """Initialize with embedding and database dependencies.

        Args:
            embedder: Embedder instance for vector generation.
            qdrant_manager: QdrantManager for vector search.
        """
        self.embedder = embedder
        self.qdrant_manager = qdrant_manager

    def retrieve(
        self, jd_data: dict[str, Any], limit: int = 20
    ) -> list[dict[str, Any]]:
        """Search for candidates matching the job description.

        Args:
            jd_data: Parsed JD data dictionary.
            limit: Maximum number of candidates to retrieve.

        Returns:
            List of candidate dicts with 'score' and payload fields,
            sorted by descending similarity.

        Raises:
            RuntimeError: If search fails or no resumes are stored.
        """
        total_resumes = self.qdrant_manager.get_count()
        if total_resumes == 0:
            raise RuntimeError(
                "No resumes found in the database. "
                "Students must upload resumes before recruiters can search."
            )

        # Build rich text from JD for embedding
        embedding_text = build_embedding_text(jd_data)
        logger.info(
            f"Retrieval Agent: Generating JD embedding "
            f"({len(embedding_text)} chars, {total_resumes} resumes in DB)"
        )

        # Generate query embedding
        query_embedding = self.embedder.encode(embedding_text)

        # Search Qdrant for similar resumes
        candidates = self.qdrant_manager.search(
            query_embedding=query_embedding,
            limit=min(limit, total_resumes),
        )

        logger.info(
            f"Retrieval Agent: Retrieved {len(candidates)} candidates "
            f"(top score: {candidates[0]['score']:.4f})" if candidates else
            "Retrieval Agent: No candidates found"
        )

        return candidates

    def __call__(self, state: RecruitmentState) -> dict[str, Any]:
        """LangGraph node: Retrieve matching candidates.

        Args:
            state: Current graph state containing 'jd_data'.

        Returns:
            State update with 'candidates' list or 'error'.
        """
        if state.get("error"):
            return {}

        try:
            candidates = self.retrieve(state["jd_data"])
            return {"candidates": candidates}
        except Exception as e:
            logger.error(f"Retrieval Agent node error: {e}")
            return {"error": str(e)}
