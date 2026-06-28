"""
Talent Match — Multi-Agent Resume/JD Matching Prototype

Run with:
    uvicorn app.main:app --reload

Then visit:
    http://127.0.0.1:8000/student    — student resume upload page
    http://127.0.0.1:8000/recruiter  — recruiter JD + ranked shortlist page
    http://127.0.0.1:8000/docs       — interactive Swagger API explorer

Architecture:
- FastAPI backend, hosted Postgres via DATABASE_URL (falls back to local SQLite
  if unset — see app/db/database.py), no auth (prototype scope)
- Plain HTML/CSS/JS frontend served as static files from /static, /student, /recruiter
- 3 LLM agents (Grok via xAI API):
    1. Resume Parser Agent   -> runs at upload time (app/agents/resume_parser_agent.py)
    2. JD Parser Agent       -> runs at JD submission time (app/agents/jd_parser_agent.py)
    3. Matcher/Ranker Agent  -> runs after JD parsing (app/agents/matcher_agent.py)
- Agents 2 and 3 are orchestrated as a LangGraph graph (app/services/orchestrator.py)
  since that flow has real sequencing/branching. Agent 1 is a single direct call
  triggered from the upload endpoint.

IMPORTANT: Set these before running (see .env.example):
    XAI_API_KEY   — your xAI/Grok API key
    DATABASE_URL  — your hosted Postgres connection string (Supabase/Render)
"""
import logging

from dotenv import load_dotenv

# Load .env BEFORE importing anything that reads environment variables
# (database engine creation and the Grok client both read env vars at import time).
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.db.database import engine, Base
from app.routers import student_router, recruiter_router

logging.basicConfig(level=logging.INFO)

# Create all tables on startup (fine for a prototype; use Alembic migrations for production)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Talent Match — Multi-Agent Resume/JD Matcher",
    description="Student resume upload + recruiter JD matching, powered by a LangGraph multi-agent pipeline.",
    version="0.1.0",
)

# Permissive CORS for local prototype use (e.g. a separate frontend on another port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(student_router.router)
app.include_router(recruiter_router.router)

# Serve CSS/JS assets (static/css, static/js) under /static
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def root():
    """Redirect the bare root to the student page — most visitors land here first."""
    return FileResponse("static/student.html")


@app.get("/student")
def student_page():
    return FileResponse("static/student.html")


@app.get("/recruiter")
def recruiter_page():
    return FileResponse("static/recruiter.html")


@app.get("/api")
def api_status():
    """Plain JSON health check, separate from the human-facing "/" route."""
    return {
        "status": "ok",
        "message": "Talent Match API is running. Visit /docs for the interactive API explorer.",
    }
