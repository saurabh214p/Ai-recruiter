# 🎯 RecruitAI — AI-Powered Campus Recruitment Platform

An intelligent recruitment platform that matches students with job descriptions using semantic search, multi-dimensional scoring, and AI-generated explanations.

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Resume Upload** | Students upload PDF resumes, parsed by PyMuPDF |
| **AI Extraction** | LLM extracts skills, projects, experience, education |
| **Semantic Embedding** | SentenceTransformer generates dense vectors |
| **Vector Search** | Qdrant finds semantically similar candidates |
| **Multi-Dimensional Ranking** | 5 weighted scoring dimensions |
| **AI Explanations** | Recruiter-friendly match justifications |
| **LangGraph Pipeline** | Orchestrated agent workflow |

## 🏗️ Architecture

```
Student Flow:
PDF → Extract Text → Resume Agent (LLM) → Embedding → Store in Qdrant

Recruiter Flow (LangGraph):
JD Text → JD Agent → Retrieval Agent → Ranking Agent → Explanation Agent → Top 5 Results
```

### Scoring Weights
| Dimension | Weight | Method |
|-----------|--------|--------|
| Embedding Similarity | 40% | Qdrant cosine score |
| Skill Match | 30% | Programmatic set intersection |
| Project Relevance | 15% | Embedding similarity |
| Experience Fit | 10% | Embedding similarity |
| Education Fit | 5% | Embedding similarity |

## 📁 Project Structure

```
RecruitAI/
├── app.py                    # Main Streamlit entry point
├── requirements.txt          # Python dependencies
├── .env.example              # Environment config template
├── prompts.py                # LLM prompt templates
├── README.md
├── pages/
│   ├── student.py            # Student upload portal
│   └── recruiter.py          # Recruiter search portal
├── agents/
│   ├── resume_agent.py       # Resume parsing agent
│   ├── jd_agent.py           # Job description parsing agent
│   ├── retrieval_agent.py    # Vector search agent
│   ├── ranking_agent.py      # Multi-dimensional scoring agent
│   ├── explanation_agent.py  # Match explanation agent
│   └── graph.py              # LangGraph pipeline orchestration
├── embeddings/
│   ├── embedder.py           # SentenceTransformer wrapper
│   └── qdrant_db.py          # Qdrant vector DB manager
├── parser/
│   └── pdf_parser.py         # PyMuPDF PDF text extraction
├── utils/
│   └── helper.py             # Shared utilities (LLM, JSON, etc.)
├── models/
│   └── schemas.py            # Pydantic models & LangGraph state
└── data/
    └── uploaded_resumes/     # Stored PDF files
```

## 🚀 Quick Start

### 1. Clone & Install

```bash
cd "agentic ai/RecruitAI"
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your API key
# Default: Gemini (free tier)
# Get key at: https://aistudio.google.com/apikey
```

### 3. Run the App

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## ⚙️ Configuration

### LLM Provider

Edit `.env` to switch between providers:

```env
# Option 1: Google Gemini (FREE)
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your-key-here
GEMINI_MODEL=gemini-2.0-flash

# Option 2: OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4o-mini
```

### Embedding Model

Default: `BAAI/bge-small-en-v1.5` (384 dimensions, fast & accurate)

```env
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
EMBEDDING_DIMENSION=384
```

## 🔧 Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Streamlit |
| LLM Orchestration | LangGraph + LangChain |
| LLM | Google Gemini / OpenAI (configurable) |
| Vector Database | Qdrant (in-memory) |
| Embeddings | SentenceTransformers (BAAI/bge-small-en-v1.5) |
| PDF Parsing | PyMuPDF |
| Data Validation | Pydantic |
| Environment | python-dotenv |

## 📌 Notes

- **Qdrant runs in-memory** — data is lost when the app restarts. This is by design for the MVP.
- **No authentication** — this is a demo/MVP application.
- **First run** will download the embedding model (~130 MB) — subsequent runs use the cached version.
- The Gemini free tier has rate limits — if you hit them, wait a minute or switch to OpenAI.

## 📄 License

MIT
