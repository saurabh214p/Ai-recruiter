"""
RecruitAI - Job Description Agent (LangGraph Node)
Extracts structured information from job descriptions using an LLM.

Responsibilities:
- Parse raw JD text
- Extract required skills, preferred skills, experience, education
- Generate a JD summary
- Return structured JDData as a dict (for LangGraph state)
"""

import logging
from typing import Any

from langchain_core.messages import HumanMessage

from models.schemas import JDData, RecruitmentState
from prompts import JD_EXTRACTION_PROMPT
from utils.helper import extract_json_from_response

logger = logging.getLogger(__name__)


class JDAgent:
    """Parses raw job description text into structured JDData.

    Functions both as a standalone callable and as a LangGraph node
    (via __call__) that updates the pipeline state.
    """

    def __init__(self, llm):
        """Initialize with a LangChain LLM instance.

        Args:
            llm: Any LangChain BaseChatModel (Gemini, OpenAI, etc.)
        """
        self.llm = llm

    def extract(self, jd_text: str) -> dict[str, Any]:
        """Extract structured data from a job description.

        Args:
            jd_text: Raw job description text.

        Returns:
            JDData fields as a dictionary.

        Raises:
            ValueError: If JD text is empty.
            RuntimeError: If LLM call or parsing fails.
        """
        if not jd_text.strip():
            raise ValueError("Job description text is empty")

        logger.info("JD Agent: Starting structured extraction")

        prompt = JD_EXTRACTION_PROMPT.format(jd_text=jd_text[:8000])

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            raw_output = response.content
            logger.debug(f"JD Agent raw response: {raw_output[:300]}…")

            parsed: dict[str, Any] = extract_json_from_response(raw_output)

            # Validate through Pydantic, then export as dict for state
            jd_data = JDData(**parsed)

            logger.info(
                f"JD Agent: Extracted {len(jd_data.required_skills)} required skills, "
                f"{len(jd_data.preferred_skills)} preferred skills"
            )
            return jd_data.model_dump()

        except ValueError as e:
            logger.error(f"JD Agent JSON parsing failed: {e}")
            raise RuntimeError(f"Failed to parse LLM response: {e}") from e
        except Exception as e:
            logger.error(f"JD Agent failed: {e}")
            raise RuntimeError(f"JD extraction failed: {e}") from e

    def __call__(self, state: RecruitmentState) -> dict[str, Any]:
        """LangGraph node: Parse the JD and update pipeline state.

        Args:
            state: Current graph state containing 'jd_text'.

        Returns:
            State update dict with 'jd_data' or 'error'.
        """
        try:
            jd_data = self.extract(state["jd_text"])
            return {"jd_data": jd_data}
        except Exception as e:
            logger.error(f"JD Agent node error: {e}")
            return {"error": str(e)}
