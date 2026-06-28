"""
RecruitAI - Recruiter Portal Page
Paste JD → LangGraph pipeline → Display Top 5 matched candidates

This page handles the recruiter flow, running the full LangGraph
pipeline and displaying richly formatted candidate cards.
"""

import sys
from pathlib import Path

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import logging

from agents.graph import build_recruitment_graph
from embeddings.embedder import get_embedder
from embeddings.qdrant_db import get_qdrant_manager
from utils.helper import get_llm, setup_logging

setup_logging()
logger = logging.getLogger(__name__)

# ================================================================
# Custom CSS for Candidate Cards
# ================================================================
st.markdown(
    """
    <style>
    .candidate-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .candidate-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.15);
        border-color: #6366f1;
    }
    .match-badge {
        display: inline-block;
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        color: white;
        padding: 0.4rem 1rem;
        border-radius: 25px;
        font-weight: 700;
        font-size: 1.1rem;
    }
    .match-badge.high { background: linear-gradient(135deg, #059669 0%, #10b981 100%); }
    .match-badge.medium { background: linear-gradient(135deg, #d97706 0%, #f59e0b 100%); }
    .match-badge.low { background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%); }
    .skill-tag {
        display: inline-block;
        background: linear-gradient(135deg, #1e3a5f 0%, #2d1b69 100%);
        color: #a5b4fc;
        padding: 0.25rem 0.6rem;
        border-radius: 20px;
        font-size: 0.78rem;
        margin: 0.12rem;
        border: 1px solid #4338ca40;
    }
    .score-bar-container {
        display: flex;
        align-items: center;
        margin: 0.3rem 0;
    }
    .score-label {
        color: #94a3b8;
        font-size: 0.8rem;
        min-width: 120px;
    }
    .score-bar-bg {
        flex: 1;
        background: #1e293b;
        border-radius: 10px;
        height: 8px;
        overflow: hidden;
        margin: 0 0.5rem;
    }
    .score-bar-fill {
        height: 100%;
        border-radius: 10px;
        transition: width 0.5s ease;
    }
    .score-value {
        color: #e2e8f0;
        font-size: 0.8rem;
        min-width: 40px;
        text-align: right;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ================================================================
# Page Header
# ================================================================
st.markdown(
    """
    <div style="text-align: center; padding: 0.5rem 0 1.5rem 0;">
        <h1 style="
            background: linear-gradient(135deg, #f59e0b 0%, #ef4444 50%, #ec4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 0.3rem;
        ">💼 Recruiter Portal</h1>
        <p style="color: #94a3b8; font-size: 1.1rem;">
            Paste a job description and discover the best-matching candidates
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

# ================================================================
# Database Status Check
# ================================================================
try:
    qdrant = get_qdrant_manager()
    resume_count = qdrant.get_count()
except Exception:
    resume_count = 0

if resume_count == 0:
    st.warning(
        "⚠️ **No resumes in the database yet.** "
        "Students need to upload resumes before you can search for candidates. "
        "Navigate to the **Student Portal** to upload resumes first.",
        icon="⚠️",
    )

# Show count in sidebar
with st.sidebar:
    st.markdown("### 📈 Database Stats")
    st.metric("Resumes Available", resume_count)
    st.caption("Students must upload resumes before matching.")

# ================================================================
# Job Description Input
# ================================================================
st.markdown("### 📝 Job Description")

jd_text = st.text_area(
    "Paste the Job Description below",
    height=250,
    placeholder=(
        "Example: We are looking for a Software Engineer with 2+ years "
        "of experience in Python, Django, REST APIs, and PostgreSQL. "
        "Experience with Docker, CI/CD, and cloud platforms (AWS/GCP) "
        "is preferred. B.Tech/B.E. in Computer Science required."
    ),
    key="recruiter_jd_input",
)

# ================================================================
# Find Candidates Pipeline
# ================================================================
col_btn, col_status = st.columns([1, 2])

with col_btn:
    find_clicked = st.button(
        "🔍 Find Top Candidates",
        type="primary",
        use_container_width=True,
        disabled=(not jd_text.strip()) or (resume_count == 0),
        key="find_candidates_btn",
    )

with col_status:
    if not jd_text.strip():
        st.caption("⬅️ Paste a job description to get started")
    elif resume_count == 0:
        st.caption("⬅️ Upload resumes in the Student Portal first")

if find_clicked and jd_text.strip():
    st.markdown("---")

    # Pipeline progress
    progress_bar = st.progress(0, text="Initializing pipeline...")

    try:
        # ---- Initialize Resources ----
        progress_bar.progress(5, text="⚙️ Loading AI models...")
        llm = get_llm()
        embedder = get_embedder()
        qdrant = get_qdrant_manager()

        # ---- Build & Run LangGraph Pipeline ----
        progress_bar.progress(15, text="🔧 Building recruitment pipeline...")
        graph = build_recruitment_graph(llm, embedder, qdrant)

        progress_bar.progress(20, text="📋 JD Agent: Analyzing job description...")
        
        # Invoke the full pipeline
        with st.spinner("🔄 Running AI pipeline — this may take 30-60 seconds..."):
            result = graph.invoke({"jd_text": jd_text})

        # Check for errors
        if result.get("error"):
            st.error(f"❌ Pipeline Error: {result['error']}", icon="🔥")
            progress_bar.empty()
            st.stop()

        progress_bar.progress(100, text="✅ Pipeline complete!")

        candidates = result.get("results", [])

        if not candidates:
            st.warning(
                "No matching candidates found. Try broadening the job requirements.",
                icon="🔍",
            )
            st.stop()

        # ============================================================
        # Display JD Analysis
        # ============================================================
        jd_data = result.get("jd_data", {})
        if jd_data:
            with st.expander("📋 Parsed Job Description", expanded=False):
                col_req, col_pref = st.columns(2)
                with col_req:
                    st.markdown("**Required Skills:**")
                    for skill in jd_data.get("required_skills", []):
                        st.markdown(f"- ✅ {skill}")
                with col_pref:
                    st.markdown("**Preferred Skills:**")
                    for skill in jd_data.get("preferred_skills", []):
                        st.markdown(f"- ⭐ {skill}")
                st.markdown(f"**Experience:** {jd_data.get('experience', 'N/A')}")
                st.markdown(f"**Education:** {jd_data.get('education', 'N/A')}")

        # ============================================================
        # Display Top Candidates
        # ============================================================
        st.markdown(
            f"""
            <div style="text-align: center; margin: 1.5rem 0;">
                <h2 style="
                    background: linear-gradient(135deg, #06b6d4 0%, #8b5cf6 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    font-size: 1.8rem;
                    font-weight: 700;
                ">🏆 Top {len(candidates)} Matching Candidates</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for rank, candidate in enumerate(candidates, start=1):
            match_pct = candidate.get("match_percentage", 0)
            name = candidate.get("student_name", f"Candidate {rank}")

            # Determine badge color class
            if match_pct >= 70:
                badge_class = "high"
            elif match_pct >= 50:
                badge_class = "medium"
            else:
                badge_class = "low"

            # Rank medal
            medals = {1: "🥇", 2: "🥈", 3: "🥉"}
            medal = medals.get(rank, f"#{rank}")

            # Skills as tags
            skills = candidate.get("skills", [])
            skills_html = " ".join(
                f'<span class="skill-tag">{s}</span>' for s in skills[:15]
            )
            if len(skills) > 15:
                skills_html += f' <span class="skill-tag">+{len(skills)-15} more</span>'

            # Score breakdown bars
            scores = [
                ("Similarity", candidate.get("similarity_score", 0), "#6366f1"),
                ("Skill Match", candidate.get("skill_match_score", 0), "#8b5cf6"),
                ("Projects", candidate.get("project_relevance_score", 0), "#06b6d4"),
                ("Experience", candidate.get("experience_score", 0), "#10b981"),
                ("Education", candidate.get("education_score", 0), "#f59e0b"),
            ]
            score_bars_html = ""
            for label, score, color in scores:
                pct = int(score * 100)
                score_bars_html += f"""
                <div class="score-bar-container">
                    <span class="score-label">{label}</span>
                    <div class="score-bar-bg">
                        <div class="score-bar-fill" style="width: {pct}%; background: {color};"></div>
                    </div>
                    <span class="score-value">{pct}%</span>
                </div>
                """

            # Build the full card
            st.markdown(
                f"""
                <div class="candidate-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <h3 style="color: #e2e8f0; margin: 0; font-size: 1.3rem;">
                            {medal} {name}
                        </h3>
                        <span class="match-badge {badge_class}">
                            {match_pct:.1f}% Match
                        </span>
                    </div>
                    <div style="margin-bottom: 1rem;">
                        {skills_html}
                    </div>
                    <div style="
                        background: #0f172a;
                        border-radius: 10px;
                        padding: 0.8rem;
                        margin-bottom: 1rem;
                    ">
                        <p style="color: #64748b; font-size: 0.75rem; margin: 0 0 0.3rem 0; text-transform: uppercase; letter-spacing: 0.05em;">
                            Score Breakdown
                        </p>
                        {score_bars_html}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Projects & Explanation in expandable sections (using Streamlit widgets)
            with st.expander(f"📖 Details & AI Explanation — {name}", expanded=(rank == 1)):
                det_col1, det_col2 = st.columns(2)

                with det_col1:
                    st.markdown("**🚀 Projects:**")
                    projects = candidate.get("projects", [])
                    if projects:
                        for p in projects:
                            st.markdown(f"- {p}")
                    else:
                        st.caption("No project data available")

                with det_col2:
                    st.markdown("**💼 Experience:**")
                    experience = candidate.get("experience", [])
                    if experience:
                        for e in experience:
                            st.markdown(f"- {e}")
                    else:
                        st.caption("No experience data available")

                st.markdown("---")
                st.markdown("**💡 AI Explanation:**")
                explanation = candidate.get("explanation", "No explanation available.")
                st.markdown(explanation)

    except ValueError as e:
        progress_bar.empty()
        st.error(f"❌ Configuration Error: {e}", icon="⚙️")
        logger.error(f"Configuration error: {e}")
    except RuntimeError as e:
        progress_bar.empty()
        st.error(f"❌ Pipeline Error: {e}", icon="🔥")
        logger.error(f"Pipeline error: {e}")
    except Exception as e:
        progress_bar.empty()
        st.error(f"❌ Unexpected Error: {e}", icon="💥")
        logger.exception("Unexpected error in recruiter pipeline")
