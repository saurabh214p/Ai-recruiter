"""
RecruitAI - Explanation Agent (LangGraph Node)
Generates recruiter-friendly explanations for candidate matches.

Responsibilities:
- Analyze candidate profile vs JD requirements
- Highlight matching and missing skills
- Reference specific projects and experience
- Produce clear, actionable bullet points
"""

import logging
from typing import Any

from langchain_core.messages import HumanMessage

from models.schemas import RecruitmentState
from prompts import EXPLANATION_PROMPT

logger = logging.getLogger(__name__)


class ExplanationAgent:
    """Generates human-readable match explanations using an LLM.

    For each ranked candidate, produces a recruiter-friendly
    summary with bullet points covering strengths, matches,
    and gaps relative to the job description.
    """

    def __init__(self, llm):
        """Initialize with a LangChain LLM instance.

        Args:
            llm: Any LangChain BaseChatModel.
        """
        self.llm = llm

    def explain(
        self,
        candidate: dict[str, Any],
        jd_data: dict[str, Any],
    ) -> str:
        """Generate an explanation for a single candidate match.

        Args:
            candidate: Scored candidate data dict.
            jd_data: Parsed job description data dict.

        Returns:
            Recruiter-friendly explanation string with bullet points.
        """
        prompt = EXPLANATION_PROMPT.format(
            jd_summary=jd_data.get("summary", "N/A"),
            required_skills=", ".join(jd_data.get("required_skills", [])),
            preferred_skills=", ".join(jd_data.get("preferred_skills", [])),
            student_name=candidate.get("student_name", "Unknown"),
            candidate_skills=", ".join(candidate.get("skills", [])),
            candidate_projects=" | ".join(candidate.get("projects", [])),
            candidate_experience=" | ".join(candidate.get("experience", [])),
            candidate_education=" | ".join(candidate.get("education", [])),
            match_score=candidate.get("match_percentage", 0),
        )

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()
        except Exception as e:
            logger.error(
                f"Explanation generation failed for "
                f"'{candidate.get('student_name', '?')}': {e}"
            )
            return "⚠️ Explanation could not be generated due to an error."

    def explain_batch(
        self,
        candidates: list[dict[str, Any]],
        jd_data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Generate explanations for multiple ranked candidates.

        Calls the LLM once per candidate. For the typical Top 5,
        this is 5 LLM calls which completes in a few seconds.

        Args:
            candidates: List of ranked candidate dicts.
            jd_data: Parsed JD data dict.

        Returns:
            Same candidates with 'explanation' field added.
        """
        logger.info(
            f"Explanation Agent: Generating explanations "
            f"for {len(candidates)} candidates"
        )

        results: list[dict[str, Any]] = []

        for i, candidate in enumerate(candidates, start=1):
            name = candidate.get("student_name", f"Candidate-{i}")
            logger.info(f"  [{i}/{len(candidates)}] Explaining match for '{name}'")

            explanation = self.explain(candidate, jd_data)

            result = {
                **candidate,
                "explanation": explanation,
            }
            results.append(result)

        logger.info("Explanation Agent: All explanations generated")
        return results

    def __call__(self, state: RecruitmentState) -> dict[str, Any]:
        """LangGraph node: Generate explanations and update pipeline state.

        Args:
            state: Graph state with 'ranked_candidates' and 'jd_data'.

        Returns:
            State update with 'results' or 'error'.
        """
        if state.get("error"):
            return {}

        try:
            results = self.explain_batch(
                candidates=state["ranked_candidates"],
                jd_data=state["jd_data"],
            )
            return {"results": results}
        except Exception as e:
            logger.error(f"Explanation Agent node error: {e}")
            return {"error": str(e)}
