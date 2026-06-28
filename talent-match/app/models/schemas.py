"""
Pydantic schemas — request/response shapes for the API layer.
Kept separate from SQLAlchemy ORM models (app/models/models.py) on purpose,
so DB structure and API contract can evolve independently.
"""
from typing import Optional
from pydantic import BaseModel, EmailStr


# ---------- Student side ----------

class StudentCreate(BaseModel):
    name: str
    email: EmailStr


class StudentOut(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True


class ResumeOut(BaseModel):
    id: int
    student_id: int
    filename: str
    parse_status: str
    parse_error: Optional[str] = None
    parsed_json: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- Recruiter side ----------

class JobDescriptionCreate(BaseModel):
    title: str
    description: str
    recruiter_name: Optional[str] = None


class JobDescriptionOut(BaseModel):
    id: int
    title: str
    parse_status: str
    parse_error: Optional[str] = None

    class Config:
        from_attributes = True


class RankedCandidate(BaseModel):
    student_id: int
    rank: int
    match_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    reasoning: str
    name: Optional[str] = None
    email: Optional[str] = None
    resume_id: Optional[int] = None


class MatchResponse(BaseModel):
    job_id: int
    job_title: str
    total_candidates_considered: int
    top_candidates: list[RankedCandidate]
