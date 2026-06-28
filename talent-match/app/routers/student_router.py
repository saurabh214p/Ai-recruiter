"""
Student-facing endpoints.

Flow:
1. POST /student/register        -> create a student identity
2. POST /student/{id}/resume     -> upload PDF resume; triggers Resume Parser Agent immediately
3. GET  /student/{id}/resumes    -> list resumes + parse status for that student
"""
import os
import logging
import uuid

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import json

from app.db.database import get_db
from app.models.models import Student, Resume
from app.models.schemas import StudentCreate, StudentOut, ResumeOut
from app.services.pdf_extractor import extract_text_from_pdf
from app.agents.resume_parser_agent import parse_resume

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/student", tags=["student"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/register", response_model=StudentOut)
def register_student(payload: StudentCreate, db: Session = Depends(get_db)):
    existing = db.query(Student).filter(Student.email == payload.email).first()
    if existing:
        return existing

    student = Student(name=payload.name, email=payload.email)
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.post("/{student_id}/resume", response_model=ResumeOut)
def upload_resume(student_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found. Register first.")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are accepted.")

    # Save the uploaded file to disk with a unique name to avoid collisions
    unique_name = f"{student_id}_{uuid.uuid4().hex[:8]}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    # Step 1: extract raw text from the PDF
    try:
        raw_text = extract_text_from_pdf(file_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    resume = Resume(
        student_id=student_id,
        filename=file.filename,
        file_path=file_path,
        raw_text=raw_text,
        parse_status="pending",
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    # Step 2: run the Resume Parser Agent immediately (synchronous for this prototype)
    try:
        parsed = parse_resume(raw_text)
        resume.parsed_json = json.dumps(parsed)
        resume.parse_status = "parsed"
    except Exception as exc:
        logger.exception("Resume parsing failed for student_id=%s", student_id)
        resume.parse_status = "failed"
        resume.parse_error = str(exc)

    db.commit()
    db.refresh(resume)
    return resume


@router.get("/{student_id}/resumes", response_model=list[ResumeOut])
def list_resumes(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    return db.query(Resume).filter(Resume.student_id == student_id).all()
