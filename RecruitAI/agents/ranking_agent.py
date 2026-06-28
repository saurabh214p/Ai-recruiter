"""
RecruitAI - Ranking Agent (LangGraph Node)
Computes weighted multi-dimensional match scores and ranks candidates.

Scoring Weights:
    40% — Embedding Similarity (from Qdrant cosine score)
    30% — Skill Match (programmatic set intersection)
    15% — Project Relevance (embedding similarity)
    10% — Experience Fit (embedding similarity)
     5% — Education Fit (embedding similarity)
"""

import logging
from typing import Any

import numpy as np

from embeddings.embedder import Embedder
from models.schemas import RecruitmentState

logger = logging.getLogger(__name__)

# Scoring weights from requirements
WEIGHTS: dict[str, float] = {
    "embedding_similarity": 0.40,
    "skill_match": 0.30,
    "project_relevance": 0.15,
    "experience": 0.10,
    "education": 0.05,
}


class RankingAgent:
    """Computes multi-dimensional match scores and ranks candidates.

    Uses a hybrid approach:
    - Embedding similarity from Qdrant (semantic match)
    - Programmatic skill matching (precise skill overlap)
    - Embedding-based scoring for projects, experience, education

    No extra LLM calls — all scoring is computed locally for speed.
    """

    def __init__(self, embedder: Embedder):
        """Initialize with an Embedder for text similarity computation.

        Args:
            embedder: Embedder instance for generating comparison vectors.
        """
        self.embedder = embedder

    def _compute_skill_match(
        self, candidate_skills: list[str], jd_data: dict[str, Any]
    ) -> float:
        """Compute skill overlap ratio between candidate and JD.

        Uses fuzzy substring matching to handle variations like
        'JavaScript' vs 'javascript' or 'React.js' vs 'React'.

        Returns:
            Score between 0.0 and 1.0.
        """
        all_jd_skills = set(
            s.lower().strip()
            for s in (
                jd_data.get("required_skills", [])
                + jd_data.get("preferred_skills", [])
            )
            if s.strip()
        )
        candidate_skill_set = set(
            s.lower().strip() for s in candidate_skills if s.strip()
        )

        if not all_jd_skills:
            return 0.5  # Neutral score when JD doesn't specify skills

        # Fuzzy matching: check if JD skill is substring of candidate skill or vice versa
        matches = 0
        for jd_skill in all_jd_skills:
            for c_skill in candidate_skill_set:
                if jd_skill in c_skill or c_skill in jd_skill:
                    matches += 1
                    break

        return min(matches / len(all_jd_skills), 1.0)

    def _compute_text_similarity(self, text_a: str, text_b: str) -> float:
        """Compute embedding-based cosine similarity between two texts.

        Returns:
            Clamped score between 0.0 and 1.0.
        """
        if not text_a.strip() or not text_b.strip():
            return 0.0

        emb_a = self.embedder.encode(text_a)
        emb_b = self.embedder.encode(text_b)

        similarity = Embedder.cosine_similarity(emb_a, emb_b)
        return max(0.0, min(float(similarity), 1.0))

    def rank(
        self,
        candidates: list[dict[str, Any]],
        jd_data: dict[str, Any],
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Score and rank candidates against the job description.

        Args:
            candidates: Candidate dicts from Qdrant search (with 'score' field).
            jd_data: Parsed JD data dictionary.
            top_k: Number of top candidates to return.

        Returns:
            Top-k candidates sorted by final_score descending,
            each augmented with individual dimension scores.
        """
        logger.info(f"Ranking Agent: Scoring {len(candidates)} candidates")

        # Prepare JD text representations for comparisons
        jd_summary = jd_data.get("summary", "")
        jd_experience = jd_data.get("experience", "")
        jd_education = jd_data.get("education", "")

        scored_candidates: list[dict[str, Any]] = []

        for i, candidate in enumerate(candidates):
            name = candidate.get("student_name", f"Candidate-{i+1}")

            # 1. Embedding Similarity (40%) — from Qdrant cosine score
            sim_score = float(candidate.get("score", 0.0))

            # 2. Skill Match (30%) — programmatic set intersection
            skill_score = self._compute_skill_match(
                candidate.get("skills", []), jd_data
            )

            # 3. Project Relevance (15%) — embedding similarity
            projects_text = " . ".join(candidate.get("projects", []))
            project_score = self._compute_text_similarity(
                projects_text, jd_summary
            )

            # 4. Experience Fit (10%) — embedding similarity
            experience_text = " . ".join(candidate.get("experience", []))
            exp_score = self._compute_text_similarity(
                experience_text, jd_experience
            )

            # 5. Education Fit (5%) — embedding similarity
            education_text = " . ".join(candidate.get("education", []))
            edu_score = self._compute_text_similarity(
                education_text, jd_education
            )

            # Weighted final score
            final_score = (
                WEIGHTS["embedding_similarity"] * sim_score
                + WEIGHTS["skill_match"] * skill_score
                + WEIGHTS["project_relevance"] * project_score
                + WEIGHTS["experience"] * exp_score
                + WEIGHTS["education"] * edu_score
            )

            scored_candidate = {
                **candidate,
                "similarity_score": round(sim_score, 4),
                "skill_match_score": round(skill_score, 4),
                "project_relevance_score": round(project_score, 4),
                "experience_score": round(exp_score, 4),
                "education_score": round(edu_score, 4),
                "final_score": round(final_score, 4),
                "match_percentage": round(final_score * 100, 1),
            }
            scored_candidates.append(scored_candidate)

            logger.debug(
                f"  [{i+1}] {name}: sim={sim_score:.3f} skill={skill_score:.3f} "
                f"proj={project_score:.3f} exp={exp_score:.3f} "
                f"edu={edu_score:.3f} → final={final_score:.3f}"
            )

        # Sort by final score descending and take top K
        scored_candidates.sort(key=lambda x: x["final_score"], reverse=True)
        top = scored_candidates[:top_k]

        if top:
            logger.info(
                f"Ranking Agent: Top {len(top)} — "
                + ", ".join(
                    f"{c.get('student_name', '?')} ({c['match_percentage']}%)"
                    for c in top
                )
            )

        return top

    def __call__(self, state: RecruitmentState) -> dict[str, Any]:
        """LangGraph node: Rank candidates and update pipeline state.

        Args:
            state: Graph state with 'candidates' and 'jd_data'.

        Returns:
            State update with 'ranked_candidates' or 'error'.
        """
        if state.get("error"):
            return {}

        try:
            ranked = self.rank(
                candidates=state["candidates"],
                jd_data=state["jd_data"],
                top_k=5,
            )
            return {"ranked_candidates": ranked}
        except Exception as e:
            logger.error(f"Ranking Agent node error: {e}")
            return {"error": str(e)}
