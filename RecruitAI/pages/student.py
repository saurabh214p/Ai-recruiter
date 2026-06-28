"""
RecruitAI - Student Portal Page
Upload resume → Parse PDF → Extract data → Generate embedding → Store in Qdrant

This page handles the complete student onboarding flow with
real-time progress indicators and a polished display of extracted data.
"""

import sys
from pathlib import Path

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import logging

from parser.pdf_parser import PDFParser
from agents.resume_agent import ResumeAgent
from embeddings.embedder import get_embedder
from embeddings.qdrant_db import get_qdrant_manager
from utils.helper import get_llm, save_uploaded_file, build_embedding_text, setup_logging

setup_logging()
logger = logging.getLogger(__name__)

# ================================================================
# Page Header
# ================================================================
st.markdown(
    """
    <div style="text-align: center; padding: 0.5rem 0 1.5rem 0;">
        <h1 style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 0.3rem;
        ">🎓 Student Portal</h1>
        <p style="color: #94a3b8; font-size: 1.1rem;">
            Upload your resume and let AI extract your profile for recruiter matching
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

# ================================================================
# Resume Upload Section
# ================================================================
col_upload, col_info = st.columns([2, 1])

with col_upload:
    uploaded_file = st.file_uploader(
        "📄 Upload your Resume (PDF only)",
        type=["pdf"],
        help="Supported format: PDF. Maximum recommended size: 10 MB.",
        key="student_resume_upload",
    )

with col_info:
    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
            border: 1px solid #4338ca;
            border-radius: 12px;
            padding: 1.2rem;
            margin-top: 0.5rem;
        ">
            <h4 style="color: #a5b4fc; margin: 0 0 0.5rem 0;">📋 What happens next?</h4>
            <ol style="color: #c7d2fe; font-size: 0.85rem; padding-left: 1.2rem; margin: 0;">
                <li>PDF text is extracted</li>
                <li>AI analyzes your resume</li>
                <li>Skills & projects are identified</li>
                <li>Profile is stored for matching</li>
            </ol>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ================================================================
# Processing Pipeline
# ================================================================
if uploaded_file is not None:
    st.markdown("")

    # Show file details
    file_size_kb = uploaded_file.size / 1024
    st.info(
        f"📎 **{uploaded_file.name}** — {file_size_kb:.1f} KB",
        icon="📎",
    )

    if st.button(
        "🚀 Process Resume",
        type="primary",
        use_container_width=True,
        key="process_resume_btn",
    ):
        # Pipeline progress tracking
        progress_bar = st.progress(0, text="Starting pipeline...")
        status_container = st.empty()

        try:
            # ---- Step 1: Save File ----
            progress_bar.progress(10, text="💾 Saving uploaded file...")
            file_path = save_uploaded_file(uploaded_file)
            logger.info(f"File saved: {file_path}")

            # ---- Step 2: Extract Text ----
            progress_bar.progress(25, text="📝 Extracting text from PDF...")
            resume_text = PDFParser.extract_text(file_path)

            if not resume_text.strip():
                st.error(
                    "❌ No text could be extracted from this PDF. "
                    "Please ensure it's not an image-only or scanned PDF."
                )
                st.stop()

            st.success(
                f"✅ Extracted {len(resume_text)} characters from PDF",
                icon="📝",
            )

            # ---- Step 3: AI Resume Analysis ----
            progress_bar.progress(45, text="🤖 AI is analyzing your resume...")
            llm = get_llm()
            agent = ResumeAgent(llm=llm)
            resume_data = agent.extract(resume_text)
            resume_data.resume_path = file_path

            st.success(
                f"✅ AI extracted profile for **{resume_data.student_name}**",
                icon="🤖",
            )

            # ---- Step 4: Generate Embedding ----
            progress_bar.progress(70, text="🧮 Generating semantic embedding...")
            embedder = get_embedder()
            embedding_text = build_embedding_text(resume_data.model_dump())
            embedding = embedder.encode(embedding_text)

            st.success(
                f"✅ Generated {len(embedding)}-dimensional embedding",
                icon="🧮",
            )

            # ---- Step 5: Store in Qdrant ----
            progress_bar.progress(90, text="💾 Storing profile in vector database...")
            qdrant = get_qdrant_manager()

            # Check for duplicates
            if qdrant.check_duplicate(resume_data.student_name):
                st.warning(
                    f"⚠️ A profile for '{resume_data.student_name}' already exists. "
                    "Uploading a new version.",
                    icon="⚠️",
                )

            payload = resume_data.model_dump()
            point_id = qdrant.upsert_resume(payload, embedding)

            progress_bar.progress(100, text="✅ Pipeline complete!")

            total_count = qdrant.get_count()

            st.success(
                f"🎉 Profile stored successfully! "
                f"(ID: {point_id[:8]}… | Total resumes in DB: {total_count})",
                icon="🎉",
            )

            # ============================================================
            # Display Extracted Profile
            # ============================================================
            st.markdown("---")
            st.markdown(
                """
                <h2 style="
                    background: linear-gradient(135deg, #06b6d4 0%, #8b5cf6 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    font-size: 1.6rem;
                    font-weight: 700;
                ">📊 Extracted Profile</h2>
                """,
                unsafe_allow_html=True,
            )

            # Name & Summary Card
            st.markdown(
                f"""
                <div style="
                    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                    border: 1px solid #334155;
                    border-radius: 16px;
                    padding: 1.5rem;
                    margin: 1rem 0;
                ">
                    <h3 style="color: #e2e8f0; margin: 0 0 0.5rem 0;">
                        👤 {resume_data.student_name}
                    </h3>
                    <p style="color: #94a3b8; font-size: 0.95rem; line-height: 1.6;">
                        {resume_data.summary}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Skills, Education, Experience, Projects in columns
            col1, col2 = st.columns(2)

            with col1:
                # Skills
                st.markdown("#### 🛠️ Skills")
                if resume_data.skills:
                    skills_html = " ".join(
                        f'<span style="'
                        f"display: inline-block; "
                        f"background: linear-gradient(135deg, #1e3a5f 0%, #2d1b69 100%); "
                        f"color: #a5b4fc; "
                        f"padding: 0.3rem 0.7rem; "
                        f"border-radius: 20px; "
                        f"font-size: 0.82rem; "
                        f"margin: 0.15rem; "
                        f"border: 1px solid #4338ca50; "
                        f'">{skill}</span>'
                        for skill in resume_data.skills
                    )
                    st.markdown(skills_html, unsafe_allow_html=True)
                else:
                    st.caption("No skills extracted")

                # Education
                st.markdown("#### 🎓 Education")
                for edu in resume_data.education:
                    st.markdown(f"- {edu}")
                if not resume_data.education:
                    st.caption("No education data extracted")

            with col2:
                # Experience
                st.markdown("#### 💼 Experience")
                for exp in resume_data.experience:
                    st.markdown(f"- {exp}")
                if not resume_data.experience:
                    st.caption("No experience data extracted")

                # Projects
                st.markdown("#### 🚀 Projects")
                for proj in resume_data.projects:
                    st.markdown(f"- {proj}")
                if not resume_data.projects:
                    st.caption("No projects extracted")

        except ValueError as e:
            progress_bar.empty()
            st.error(f"❌ Configuration Error: {e}", icon="⚙️")
            logger.error(f"Configuration error: {e}")
        except RuntimeError as e:
            progress_bar.empty()
            st.error(f"❌ Processing Error: {e}", icon="🔥")
            logger.error(f"Processing error: {e}")
        except Exception as e:
            progress_bar.empty()
            st.error(f"❌ Unexpected Error: {e}", icon="💥")
            logger.exception(f"Unexpected error during resume processing")

# ================================================================
# Sidebar Stats
# ================================================================
with st.sidebar:
    st.markdown("### 📈 Database Stats")
    try:
        qdrant = get_qdrant_manager()
        count = qdrant.get_count()
        st.metric("Resumes Stored", count)
    except Exception:
        st.caption("Database not initialized yet")
