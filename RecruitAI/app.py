"""
RecruitAI - Main Application Entry Point
AI-Powered Campus Recruitment Platform

Run with:
    streamlit run app.py
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path for all page imports
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from utils.helper import setup_logging

# Initialize logging before anything else
setup_logging()

# ================================================================
# Page Configuration (MUST be the first Streamlit command)
# ================================================================
st.set_page_config(
    page_title="RecruitAI — AI Campus Recruitment",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ================================================================
# Global Custom CSS
# ================================================================
st.markdown(
    """
    <style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* Global font */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%);
    }
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #a5b4fc;
    }

    /* Button styling */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        border: none;
        border-radius: 10px;
        font-weight: 600;
        padding: 0.6rem 1.5rem;
        transition: all 0.3s ease;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
    }

    /* Progress bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #6366f1, #8b5cf6, #06b6d4);
    }

    /* Divider */
    hr {
        border-color: #334155;
    }

    /* File uploader */
    [data-testid="stFileUploader"] {
        border-radius: 12px;
    }

    /* Expander */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #a5b4fc;
    }

    /* Metric styling */
    [data-testid="stMetricValue"] {
        color: #6366f1;
        font-size: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ================================================================
# Home Page Content
# ================================================================
def home_page():
    """Render the landing page with hero section and feature overview."""

    # Hero Section
    st.markdown(
        """
        <div style="
            text-align: center;
            padding: 3rem 1rem;
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #312e81 100%);
            border-radius: 24px;
            border: 1px solid #4338ca30;
            margin-bottom: 2rem;
        ">
            <h1 style="
                background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 30%, #06b6d4 60%, #10b981 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-size: 3.5rem;
                font-weight: 800;
                margin-bottom: 0.5rem;
                line-height: 1.2;
            ">🎯 RecruitAI</h1>
            <p style="
                color: #94a3b8;
                font-size: 1.3rem;
                max-width: 600px;
                margin: 0 auto;
                line-height: 1.6;
            ">
                AI-Powered Campus Recruitment Platform<br>
                <span style="color: #64748b; font-size: 1rem;">
                    Smart resume matching • Semantic search • Intelligent ranking
                </span>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Feature Cards
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            <div style="
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                border: 1px solid #334155;
                border-radius: 16px;
                padding: 2rem;
                height: 100%;
                transition: transform 0.2s ease;
            ">
                <h2 style="color: #a5b4fc; font-size: 1.5rem; margin-bottom: 1rem;">
                    🎓 For Students
                </h2>
                <ul style="color: #94a3b8; line-height: 2; padding-left: 1.2rem;">
                    <li>Upload your PDF resume</li>
                    <li>AI extracts skills, projects & experience</li>
                    <li>Profile is embedded and stored</li>
                    <li>Get discovered by recruiters automatically</li>
                </ul>
                <p style="
                    color: #6366f1;
                    font-size: 0.85rem;
                    margin-top: 1rem;
                    font-weight: 600;
                ">Navigate to Student Portal →</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div style="
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                border: 1px solid #334155;
                border-radius: 16px;
                padding: 2rem;
                height: 100%;
                transition: transform 0.2s ease;
            ">
                <h2 style="color: #fbbf24; font-size: 1.5rem; margin-bottom: 1rem;">
                    💼 For Recruiters
                </h2>
                <ul style="color: #94a3b8; line-height: 2; padding-left: 1.2rem;">
                    <li>Paste any job description</li>
                    <li>AI analyzes required skills & qualifications</li>
                    <li>Semantic search finds best matches</li>
                    <li>Top 5 candidates with explanations</li>
                </ul>
                <p style="
                    color: #f59e0b;
                    font-size: 0.85rem;
                    margin-top: 1rem;
                    font-weight: 600;
                ">Navigate to Recruiter Portal →</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # How It Works Section
    st.markdown("")
    st.markdown(
        """
        <div style="
            text-align: center;
            margin: 2rem 0 1rem 0;
        ">
            <h2 style="
                color: #e2e8f0;
                font-size: 1.5rem;
                font-weight: 700;
            ">⚙️ How It Works</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(5)
    steps = [
        ("📄", "Upload", "Student uploads PDF resume"),
        ("🤖", "AI Parse", "LLM extracts structured data"),
        ("🧮", "Embed", "Generate semantic vectors"),
        ("🔍", "Search", "Find matching candidates"),
        ("🏆", "Rank", "Multi-dimensional scoring"),
    ]
    for col, (icon, title, desc) in zip(cols, steps):
        with col:
            st.markdown(
                f"""
                <div style="
                    text-align: center;
                    background: #0f172a;
                    border: 1px solid #1e293b;
                    border-radius: 12px;
                    padding: 1.2rem 0.5rem;
                ">
                    <div style="font-size: 2rem; margin-bottom: 0.3rem;">{icon}</div>
                    <div style="color: #e2e8f0; font-weight: 600; font-size: 0.9rem;">{title}</div>
                    <div style="color: #64748b; font-size: 0.75rem; margin-top: 0.3rem;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Tech Stack Footer
    st.markdown("")
    st.markdown(
        """
        <div style="
            text-align: center;
            padding: 1.5rem;
            background: #0f172a;
            border-radius: 12px;
            border: 1px solid #1e293b;
            margin-top: 1rem;
        ">
            <p style="color: #64748b; font-size: 0.8rem; margin: 0;">
                Built with
                <span style="color: #a5b4fc;">Streamlit</span> •
                <span style="color: #a5b4fc;">LangGraph</span> •
                <span style="color: #a5b4fc;">LangChain</span> •
                <span style="color: #a5b4fc;">Qdrant</span> •
                <span style="color: #a5b4fc;">SentenceTransformers</span> •
                <span style="color: #a5b4fc;">Gemini / OpenAI</span>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ================================================================
# Navigation Setup (Streamlit 1.36+ multi-page navigation)
# ================================================================
pg = st.navigation(
    {
        "Home": [
            st.Page(home_page, title="Home", icon="🏠", default=True),
        ],
        "Portals": [
            st.Page("pages/student.py", title="Student Portal", icon="🎓"),
            st.Page("pages/recruiter.py", title="Recruiter Portal", icon="💼"),
        ],
    }
)

# Run the selected page
pg.run()
