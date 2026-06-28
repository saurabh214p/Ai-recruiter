"""
RecruitAI - Resume Agent
Extracts structured information from resume text using an LLM.

Responsibilities:
- Parse raw resume text
- Extract name, education, experience, skills, projects
- Generate a professional summary
- Return validated ResumeData
"""

import logging
from typing import Any

from langchain_core.messages import HumanMessage

from models.schemas import ResumeData
from prompts import RESUME_EXTRACTION_PROMPT
from utils.helper import extract_json_from_response

logger = logging.getLogger(__name__)


class ResumeAgent:
    """Parses raw resume text into structured ResumeData using an LLM.

    The agent sends the resume text to the LLM with a structured
    extraction prompt and validates the response into a Pydantic model.
    """

    def __init__(self, llm):
        """Initialize with a LangChain LLM instance.

        Args:
            llm: Any LangChain BaseChatModel (Gemini, OpenAI, etc.)
        """
        self.llm = llm

    def extract(self, resume_text: str) -> ResumeData:
        """Extract structured data from raw resume text.

        Args:
            resume_text: Plain text extracted from a PDF resume.

        Returns:
            ResumeData with all fields populated.

        Raises:
            ValueError: If resume text is empty.
            RuntimeError: If LLM call or JSON parsing fails.
        """
        if not resume_text.strip():
            raise ValueError("Resume text is empty — cannot extract data")

        logger.info("Resume Agent: Starting structured extraction")

        # Truncate very long resumes to stay within context window
        prompt = RESUME_EXTRACTION_PROMPT.format(
            resume_text=resume_text[:8000]
        )

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            raw_output = response.content
            logger.debug(f"Resume Agent raw response: {raw_output[:300]}…")

            # Parse JSON from LLM response
            parsed: dict[str, Any] = extract_json_from_response(raw_output)

            # Validate and create Pydantic model
            resume_data = ResumeData(**parsed)

            logger.info(
                f"Resume Agent: Extracted profile for '{resume_data.student_name}' — "
                f"{len(resume_data.skills)} skills, "
                f"{len(resume_data.projects)} projects, "
                f"{len(resume_data.experience)} experience entries"
            )
            return resume_data

        except ValueError as e:
            logger.error(f"Resume Agent JSON parsing failed: {e}")
            raise RuntimeError(f"Failed to parse LLM response: {e}") from e
        except Exception as e:
            logger.error(f"Resume Agent failed: {e}")
            raise RuntimeError(f"Resume extraction failed: {e}") from e
