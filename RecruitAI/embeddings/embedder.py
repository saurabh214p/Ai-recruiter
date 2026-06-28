"""
RecruitAI - Embedding Model
Wrapper around SentenceTransformers for generating dense vector embeddings.

Default model: BAAI/bge-small-en-v1.5 (384 dimensions, fast, accurate).
"""

import logging
import os

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class Embedder:
    """Generates dense vector embeddings using SentenceTransformers.

    Embeddings are L2-normalized, making cosine similarity equivalent
    to a simple dot product for efficient computation.
    """

    def __init__(self, model_name: str | None = None):
        """Initialize the embedding model.

        Args:
            model_name: HuggingFace model identifier. Falls back to
                        EMBEDDING_MODEL env var or BAAI/bge-small-en-v1.5.
        """
        model_name = model_name or os.getenv(
            "EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5"
        )
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension: int = self.model.get_sentence_embedding_dimension()
        logger.info(f"Embedding model ready — dimension: {self.dimension}")

    def encode(self, text: str) -> list[float]:
        """Encode a single text into a normalized embedding vector.

        Args:
            text: Input text to embed.

        Returns:
            List of floats (length = self.dimension).
        """
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        """Encode multiple texts into normalized embedding vectors.

        Args:
            texts: List of input texts.

        Returns:
            List of embedding vectors.
        """
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    @staticmethod
    def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
        """Compute cosine similarity between two normalized vectors.

        Since embeddings are L2-normalized, cosine similarity = dot product.

        Args:
            vec_a: First embedding vector.
            vec_b: Second embedding vector.

        Returns:
            Similarity score (typically between 0 and 1 for text).
        """
        a = np.array(vec_a, dtype=np.float32)
        b = np.array(vec_b, dtype=np.float32)
        return float(np.dot(a, b))


# ================================================================
# Module-level Singleton
# ================================================================
# Python caches imported modules, so this singleton persists across
# Streamlit re-runs and is shared by all pages/agents.
_embedder_instance: Embedder | None = None


def get_embedder() -> Embedder:
    """Get or create the singleton Embedder instance.

    Returns:
        Shared Embedder instance (model loaded once).
    """
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = Embedder()
    return _embedder_instance
