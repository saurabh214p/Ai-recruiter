"""
RecruitAI - Data Models & Schemas
Pydantic models for structured data and LangGraph state definition.
"""

from pydantic import BaseModel, Field
from typing import Any
from typing_extensions import TypedDict


class ResumeData(BaseModel):
    """Structured resume data extracted by the Resume Agent."""

    student_name: str = Field(default="Unknown", description="Full name of the student")
    education: list[str] = Field(default_factory=list, description="Education entries")
    experience: list[str] = Field(default_factory=list, description="Work experience entries")
    skills: list[str] = Field(default_factory=list, description="Technical and soft skills")
    projects: list[str] = Field(default_factory=list, description="Project descriptions")
    summary: str = Field(default="", description="Brief professional summary")
    resume_path: str = Field(default="", description="Path to the uploaded resume PDF")


class JDData(BaseModel):
    """Structured job description data extracted by the JD Agent."""

    required_skills: list[str] = Field(default_factory=list, description="Mandatory skills")
    preferred_skills: list[str] = Field(default_factory=list, description="Nice-to-have skills")
    experience: str = Field(default="Not specified", description="Experience requirements")
    education: str = Field(default="Not specified", description="Education requirements")
    summary: str = Field(default="", description="Brief JD summary")


class CandidateMatch(BaseModel):
    """A candidate with computed match scores across multiple dimensions."""

    student_name: str = ""
    skills: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    summary: str = ""
    resume_path: str = ""
    similarity_score: float = Field(default=0.0, description="Embedding similarity (40%)")
    skill_match_score: float = Field(default=0.0, description="Skill match ratio (30%)")
    project_relevance_score: float = Field(default=0.0, description="Project relevance (15%)")
    experience_score: float = Field(default=0.0, description="Experience fit (10%)")
    education_score: float = Field(default=0.0, description="Education fit (5%)")
    final_score: float = Field(default=0.0, description="Weighted final score")


class CandidateResult(BaseModel):
    """Final result for display, including explanation."""

    student_name: str = ""
    match_percentage: float = 0.0
    skills: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    explanation: str = ""
    resume_path: str = ""
    # Score breakdown for detailed view
    similarity_score: float = 0.0
    skill_match_score: float = 0.0
    project_relevance_score: float = 0.0
    experience_score: float = 0.0
    education_score: float = 0.0


class RecruitmentState(TypedDict, total=False):
    """LangGraph state for the recruiter pipeline.

    Flow: JD Text -> JD Agent -> Retrieval Agent -> Ranking Agent -> Explanation Agent -> Results
    """

    jd_text: str                     # Raw job description text input
    jd_data: dict[str, Any]          # Parsed JD (JDData serialized as dict)
    candidates: list[dict[str, Any]] # Raw candidates from Qdrant search
    ranked_candidates: list[dict[str, Any]]  # Scored and ranked candidates
    results: list[dict[str, Any]]    # Final results with explanations
    error: str                       # Error message if pipeline fails
