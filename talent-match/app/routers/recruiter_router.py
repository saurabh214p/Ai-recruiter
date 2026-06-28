"""
Recruiter-facing endpoints.

Flow:
1. POST /recruiter/job              -> submit a JD; this immediately runs the
                                        full LangGraph pipeline (parse JD -> rank
                                        all successfully-parsed candidate resumes)
                                        and returns the top 5 matches.
2. GET  /recruiter/job/{id}/matches -> re-fetch the most recent cached match result
                                        for a JD without re-running the agents.
3. GET  /recruiter/job/{id}/resume/{student_id} -> fetch full resume detail for one
                                        of the matched students (so a recruiter can
                                        view full profile + resume text).
"""
import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import JobDescription, Resume, Student, MatchResult
from app.models.schemas import JobDescriptionCreate, MatchResponse, RankedCandidate
from app.services.orchestrator import run_match_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recruiter", tags=["recruiter"])


def _build_candidate_pool(db: Session) -> list[dict]:
    """
    Pulls every successfully-parsed resume in the system into the shape
    the Matcher Agent expects: {"student_id", "name", "profile"}.
    Resumes that failed parsing are excluded since there's no structured
    profile to compare against the JD.
    """
    pool = []
    resumes = db.query(Resume).filter(Resume.parse_status == "parsed").all()

    for resume in resumes:
        student = db.query(Student).filter(Student.id == resume.student_id).first()
        if not student:
            continue
        pool.append({
            "student_id": student.id,
            "name": student.name,
            "profile": json.loads(resume.parsed_json),
        })
    return pool


@router.post("/job", response_model=MatchResponse)
def submit_job_and_match(payload: JobDescriptionCreate, db: Session = Depends(get_db)):
    job = JobDescription(
        title=payload.title,
        raw_text=payload.description,
        recruiter_name=payload.recruiter_name,
        parse_status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    candidate_pool = _build_candidate_pool(db)

    # Run the LangGraph pipeline: parse_jd -> rank_candidates
    final_state = run_match_pipeline(
        job_raw_text=payload.description,
        job_title=payload.title,
        candidate_pool=candidate_pool,
    )

    if final_state.get("job_parsed"):
        job.parsed_json = json.dumps(final_state["job_parsed"])
        job.parse_status = "parsed"
    else:
        job.parse_status = "failed"
        job.parse_error = final_state.get("error", "Unknown parsing error")
        db.commit()
        raise HTTPException(status_code=502, detail=job.parse_error)

    db.commit()

    if final_state.get("error"):
        raise HTTPException(status_code=502, detail=final_state["error"])

    ranked = final_state["ranked_result"]["ranked_candidates"]
    ranked = sorted(ranked, key=lambda c: c["rank"])[:5]

    # Enrich with name/email/resume_id for the recruiter UI, and cache the result
    enriched = []
    for c in ranked:
        student = db.query(Student).filter(Student.id == c["student_id"]).first()
        resume = (
            db.query(Resume)
            .filter(Resume.student_id == c["student_id"], Resume.parse_status == "parsed")
            .order_by(Resume.uploaded_at.desc())
            .first()
        )
        enriched.append({
            **c,
            "name": student.name if student else None,
            "email": student.email if student else None,
            "resume_id": resume.id if resume else None,
        })

    match_result = MatchResult(job_id=job.id, result_json=json.dumps(enriched))
    db.add(match_result)
    db.commit()

    return MatchResponse(
        job_id=job.id,
        job_title=job.title,
        total_candidates_considered=len(candidate_pool),
        top_candidates=[RankedCandidate(**c) for c in enriched],
    )


@router.get("/job/{job_id}/matches", response_model=MatchResponse)
def get_cached_matches(job_id: int, db: Session = Depends(get_db)):
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    match = (
        db.query(MatchResult)
        .filter(MatchResult.job_id == job_id)
        .order_by(MatchResult.created_at.desc())
        .first()
    )
    if not match:
        raise HTTPException(status_code=404, detail="No match results found for this job yet.")

    enriched = json.loads(match.result_json)
    return MatchResponse(
        job_id=job.id,
        job_title=job.title,
        total_candidates_considered=len(enriched),
        top_candidates=[RankedCandidate(**c) for c in enriched],
    )


@router.get("/job/{job_id}/resume/{student_id}")
def get_candidate_resume_detail(job_id: int, student_id: int, db: Session = Depends(get_db)):
    """Lets a recruiter drill into a specific matched candidate's full resume + parsed profile."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    resume = (
        db.query(Resume)
        .filter(Resume.student_id == student_id, Resume.parse_status == "parsed")
        .order_by(Resume.uploaded_at.desc())
        .first()
    )
    if not resume:
        raise HTTPException(status_code=404, detail="No parsed resume found for this student.")

    return {
        "student": {"id": student.id, "name": student.name, "email": student.email},
        "resume_raw_text": resume.raw_text,
        "resume_parsed_profile": json.loads(resume.parsed_json),
    }
