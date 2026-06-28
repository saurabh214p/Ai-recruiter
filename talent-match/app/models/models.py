"""
ORM models for the Talent Match prototype.

Tables:
- Student: basic student identity
- Resume: one uploaded PDF resume per student (raw text + LLM-parsed structured JSON)
- JobDescription: a JD submitted by a recruiter (raw text + LLM-parsed structured JSON)
- MatchResult: cached ranking output for a given JD (top 5 students + reasoning),
  so a recruiter can revisit results without re-running the agents every time.
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    resumes = relationship("Resume", back_populates="student", cascade="all, delete-orphan")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)

    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)

    raw_text = Column(Text, nullable=False)          # extracted PDF text
    parsed_json = Column(Text, nullable=True)         # structured output from Resume Parser Agent (JSON string)
    parse_status = Column(String, default="pending")  # pending | parsed | failed
    parse_error = Column(Text, nullable=True)

    uploaded_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="resumes")


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    recruiter_name = Column(String, nullable=True)
    title = Column(String, nullable=False)
    raw_text = Column(Text, nullable=False)
    parsed_json = Column(Text, nullable=True)         # structured output from JD Parser Agent (JSON string)
    parse_status = Column(String, default="pending")
    parse_error = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class MatchResult(Base):
    __tablename__ = "match_results"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=False)
    result_json = Column(Text, nullable=False)  # ranked top-5 list with scores + reasoning (JSON string)
    created_at = Column(DateTime, default=datetime.utcnow)
