# Talent Match — Multi-Agent Resume/JD Matching System

A prototype multi-agent system where **students upload resumes** and **recruiters
submit job descriptions**, and an LLM-driven agent pipeline ranks and returns the
**top 5 best-fit students** for each job.

## Architecture

```
                STUDENT SIDE                                RECRUITER SIDE
        ┌───────────────────────┐                   ┌─────────────────────────┐
        │ /student page:        │                   │ /recruiter page:        │
        │ upload PDF resume     │                   │ submit job description  │
        └───────────┬───────────┘                   └────────────┬────────────┘
                     │                                            │
                     ▼                                            ▼
        ┌───────────────────────┐                   ┌─────────────────────────┐
        │ pdfplumber extracts   │                   │   LangGraph Pipeline:   │
        │ raw text from PDF     │                   │                         │
        └───────────┬───────────┘                   │  ┌───────────────────┐ │
                     ▼                               │  │ JD Parser Agent   │ │
        ┌───────────────────────┐                    │  └─────────┬─────────┘ │
        │ Resume Parser Agent   │                    │            ▼           │
        │ (Grok LLM call)       │                    │  ┌───────────────────┐ │
        │ -> structured JSON    │───stored in DB─────▶│  │ Matcher/Ranker    │ │
        └───────────┬───────────┘   (candidate pool)  │  │ Agent (Grok LLM)  │ │
                     ▼                                │  └─────────┬─────────┘ │
        ┌───────────────────────┐                     └────────────┼──────────-┘
        │ Stored in Postgres    │                                  ▼
        └───────────────────────┘                       Ranked ledger UI:
                                                          top 5 candidates
                                                          + scores + reasoning
```

### Frontend

Two plain HTML/CSS/JS pages, no build step, served directly by FastAPI as static files:

- **`/student`** — register (name + email, no password) and upload a PDF resume.
  Shows the parsed profile (skills, education, experience) once the Resume Parser
  Agent finishes.
- **`/recruiter`** — paste a job title + description, hit "Find top matches," and
  see a ranked ledger of the top 5 candidates. Each row shows rank, match score,
  and a one-line reasoning summary; clicking a row expands matched/missing skill
  tags.



### The 3 agents

| # | Agent | Trigger | File |
|---|-------|---------|------|
| 1 | **Resume Parser Agent** | On resume upload | `app/agents/resume_parser_agent.py` |
| 2 | **JD Parser Agent** | On JD submission | `app/agents/jd_parser_agent.py` |
| 3 | **Matcher/Ranker Agent** | After JD is parsed | `app/agents/matcher_agent.py` |

Agents 2 and 3 are wired together as a **LangGraph graph** (`app/services/orchestrator.py`)
because that flow has real sequencing: the JD must be parsed before candidates can be
ranked against it, and a failure at the parse step should short-circuit ranking.
Agent 1 is a single direct call from the upload endpoint — there's no branching needed there.

All three agents call **Grok (xAI)** via its OpenAI-compatible API
(`app/services/grok_client.py`), using the official `openai` Python SDK pointed at
`https://api.x.ai/v1`.

### Why an LLM for matching instead of plain keyword/embedding matching?

The Matcher Agent reasons about **transferable skills** (e.g. Django experience
counts toward a Flask role), weighs **project work** for students with thin resumes,
and writes **human-readable reasoning** a recruiter can actually read — not just a
similarity score.

## Project structure

```
talent-match/
├── app/
│   ├── main.py                      # FastAPI app entrypoint + page routes
│   ├── agents/
│   │   ├── resume_parser_agent.py   # Agent 1
│   │   ├── jd_parser_agent.py       # Agent 2
│   │   └── matcher_agent.py         # Agent 3
│   ├── routers/
│   │   ├── student_router.py        # /student/* API endpoints
│   │   └── recruiter_router.py      # /recruiter/* API endpoints
│   ├── services/
│   │   ├── grok_client.py           # Grok API wrapper
│   │   ├── pdf_extractor.py         # PDF -> raw text
│   │   └── orchestrator.py          # LangGraph pipeline (Agent 2 -> Agent 3)
│   ├── models/
│   │   ├── models.py                # SQLAlchemy ORM models
│   │   └── schemas.py                # Pydantic request/response schemas
│   └── db/
│       └── database.py              # Postgres (DATABASE_URL) / SQLite fallback setup
├── static/                           # Frontend — plain HTML/CSS/JS, no build step
│   ├── student.html                  # Student upload page
│   ├── recruiter.html                # Recruiter matching page
│   ├── css/styles.css                # Shared design tokens + components
│   └── js/
│       ├── student.js                # Register + upload + profile preview logic
│       └── recruiter.js              # JD submit + ranked ledger rendering logic
├── uploads/                          # uploaded resume PDFs (gitignored in practice)
├── requirements.txt
├── .env.example                      # copy to .env and fill in XAI_API_KEY + DATABASE_URL
└── README.md
```

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

```env
XAI_API_KEY=your-grok-api-key-here
DATABASE_URL=postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
```

- **`XAI_API_KEY`** — get one at https://accounts.x.ai
- **`DATABASE_URL`** — your hosted Postgres connection string from **Supabase** or
  **Render** (same pattern as your Spring Boot API). If you leave this blank, the
  app automatically falls back to a local SQLite file (`talent_match.db`) so it
  still runs with zero config.

`.env` is loaded automatically at startup (see `app/main.py`) — no need to
`export` variables manually, though that still works too if you prefer it.

**Getting a Postgres URL from Supabase**: create a project at
https://supabase.com → Project Settings → Database → Connection string (URI mode).

**Getting a Postgres URL from Render**: create a PostgreSQL instance at
https://render.com → copy the "External Database URL" from the instance dashboard.

### 3. Run the server

```bash
uvicorn app.main:app --reload
```

The app will be live at `http://127.0.0.1:8000`:

| Page | URL |
|------|-----|
| Student upload | `http://127.0.0.1:8000/student` |
| Recruiter matching | `http://127.0.0.1:8000/recruiter` |
| Interactive API docs (Swagger) | `http://127.0.0.1:8000/docs` |

On first run, tables are created automatically against whichever database
`DATABASE_URL` points to.

## Using it

### Student flow (UI)

1. Open `http://127.0.0.1:8000/student`
2. Enter your name and email, hit **Continue**
3. Upload a PDF resume — it's parsed immediately and you'll see your structured
   profile (skills, education, experience) appear below

### Recruiter flow (UI)

1. Open `http://127.0.0.1:8000/recruiter`
2. Enter a job title and paste the full job description
3. Hit **Find top matches** — this runs the full LangGraph pipeline (parse JD →
   rank all parsed candidate resumes) and shows a ranked ledger of the top 5
4. Click any row to expand matched/missing skill tags

### Raw API (for scripting / Swagger)

<details>
<summary>Click to expand API reference</summary>

**Student:**
1. `POST /student/register` — `{"name": "Jane Doe", "email": "jane@example.com"}`
2. `POST /student/{student_id}/resume` — multipart PDF upload
3. `GET /student/{student_id}/resumes` — check parse status

**Recruiter:**
1. `POST /recruiter/job`
   ```json
   {
     "title": "Backend Engineer Intern",
     "description": "We are looking for a backend intern skilled in Python, FastAPI, SQL...",
     "recruiter_name": "Acme Corp"
   }
   ```
2. `GET /recruiter/job/{job_id}/matches` — re-fetch cached results
3. `GET /recruiter/job/{job_id}/resume/{student_id}` — full resume detail for one candidate

</details>

## Notes on this prototype's scope

- **No auth** — registration is just name + email, by your choice. Add real auth
  (similar to your Spring Boot API) before any public deployment.
- **Synchronous agent calls** — resume parsing happens inline during upload, and
  JD parsing + ranking happens inline during job submission. For production, move
  these to a background task queue (Celery/RQ) so uploads don't block on LLM latency,
  and have the frontend poll for status instead.
- **Single-call ranking** — the Matcher Agent currently sends the entire candidate
  pool to the LLM in one call. This works well up to roughly 30-50 candidates; beyond
  that you'd want to chunk/batch and do a second pass to merge top candidates across
  batches.
- **PDF only** — resumes must be text-based PDFs (not scanned images). Scanned PDFs
  would need an OCR step (see `/mnt/skills/public/pdf/SKILL.md` reference to
  `pytesseract` + `pdf2image` if you want to add that later).
- **Frontend** is plain HTML/CSS/JS with no build step — easy to deploy alongside
  the API on Render as static files served by FastAPI, but if the UI grows in
  complexity later, a React rewrite would be a natural next step.
