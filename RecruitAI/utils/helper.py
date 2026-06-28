"""
RecruitAI - Utility Helpers
LLM initialization, JSON extraction, file management, and logging setup.

This module provides shared utilities used by agents, embeddings,
and Streamlit pages. It does NOT depend on Streamlit.
"""

import json
import logging
import os
import re
import uuid
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Load .env from project root
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env", override=True)

logger = logging.getLogger(__name__)

# ---- Project Paths ----
PROJECT_ROOT = Path(__file__).parent.parent
UPLOAD_DIR = PROJECT_ROOT / "data" / "uploaded_resumes"


def setup_logging(level: int = logging.INFO) -> None:
    """Configure application-wide logging format and level."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(name)-30s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def get_llm():
    """Create and return the configured LLM instance.

    Reads LLM_PROVIDER from environment to select between
    'groq' (default), 'gemini', and 'openai'.

    Returns:
        A LangChain BaseChatModel instance.

    Raises:
        ValueError: If provider is unsupported or API key is missing.
    """
    provider = os.getenv("LLM_PROVIDER", "groq").lower().strip()

    if provider == "groq":
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key or api_key.startswith("your-"):
            raise ValueError(
                "GROQ_API_KEY is not configured. "
                "Get a free API key at: https://console.groq.com/keys\n"
                "Then set it in your .env file."
            )
        from langchain_groq import ChatGroq

        model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        logger.info(f"Initializing Groq LLM: {model_name}")
        return ChatGroq(
            model=model_name,
            api_key=api_key,
            temperature=0.1,
        )

    elif provider == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY", "")
        if not api_key or api_key.startswith("your-"):
            raise ValueError(
                "GOOGLE_API_KEY is not configured. "
                "Get a free API key at: https://aistudio.google.com/apikey\n"
                "Then set it in your .env file."
            )
        from langchain_google_genai import ChatGoogleGenerativeAI

        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        logger.info(f"Initializing Gemini LLM: {model_name}")
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.1,
        )

    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key or api_key.startswith("your-"):
            raise ValueError(
                "OPENAI_API_KEY is not configured. Set it in your .env file."
            )
        from langchain_openai import ChatOpenAI

        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        logger.info(f"Initializing OpenAI LLM: {model_name}")
        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            temperature=0.1,
        )

    else:
        raise ValueError(
            f"Unsupported LLM_PROVIDER: '{provider}'. "
            "Supported values: 'groq', 'gemini', 'openai'."
        )


def extract_json_from_response(text: str) -> Any:
    """Extract and parse JSON from an LLM response string.

    Handles common LLM output patterns:
    1. Pure JSON response
    2. JSON wrapped in ```json ... ``` code blocks
    3. JSON embedded within surrounding text

    Args:
        text: Raw LLM response string.

    Returns:
        Parsed JSON object (dict or list).

    Raises:
        ValueError: If no valid JSON can be extracted.
    """
    text = text.strip()

    # Strategy 1: Direct JSON parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Extract from ```json ... ``` code blocks
    code_block_pattern = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
    matches = re.findall(code_block_pattern, text, re.DOTALL)
    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue

    # Strategy 3: Find outermost JSON object { ... } or array [ ... ]
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start_idx = text.find(start_char)
        if start_idx == -1:
            continue
        depth = 0
        for i in range(start_idx, len(text)):
            if text[i] == start_char:
                depth += 1
            elif text[i] == end_char:
                depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start_idx : i + 1])
                except json.JSONDecodeError:
                    break

    raise ValueError(
        f"Could not extract valid JSON from LLM response:\n{text[:500]}..."
    )


def save_uploaded_file(uploaded_file, filename: str | None = None) -> str:
    """Save a Streamlit UploadedFile to the upload directory.

    Args:
        uploaded_file: Streamlit UploadedFile object with .name and .getbuffer().
        filename: Optional custom filename. Auto-generates a unique name if None.

    Returns:
        Absolute path to the saved file as a string.
    """
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    if filename is None:
        # Prefix with short UUID to avoid name collisions
        unique_prefix = uuid.uuid4().hex[:8]
        safe_name = re.sub(r"[^\w.\-]", "_", uploaded_file.name)
        filename = f"{unique_prefix}_{safe_name}"

    file_path = UPLOAD_DIR / filename

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    logger.info(f"Saved uploaded file: {file_path}")
    return str(file_path)


def build_embedding_text(data: dict[str, Any]) -> str:
    """Build a rich text representation for embedding generation.

    Combines multiple fields into a single text string that gives
    the embedding model comprehensive semantic context.

    Args:
        data: Dictionary containing resume or JD fields.

    Returns:
        Concatenated text suitable for embedding.
    """
    parts: list[str] = []

    if data.get("summary"):
        parts.append(str(data["summary"]))

    if data.get("skills"):
        skills = data["skills"]
        if isinstance(skills, list):
            parts.append(f"Skills: {', '.join(skills)}")
        else:
            parts.append(f"Skills: {skills}")

    if data.get("required_skills"):
        parts.append(f"Required Skills: {', '.join(data['required_skills'])}")

    if data.get("preferred_skills"):
        parts.append(f"Preferred Skills: {', '.join(data['preferred_skills'])}")

    if data.get("projects"):
        projects = data["projects"]
        if isinstance(projects, list):
            parts.append(f"Projects: {' | '.join(projects)}")
        else:
            parts.append(f"Projects: {projects}")

    if data.get("experience"):
        exp = data["experience"]
        if isinstance(exp, list):
            parts.append(f"Experience: {' | '.join(exp)}")
        else:
            parts.append(f"Experience: {exp}")

    if data.get("education"):
        edu = data["education"]
        if isinstance(edu, list):
            parts.append(f"Education: {' | '.join(edu)}")
        else:
            parts.append(f"Education: {edu}")

    return " . ".join(parts) if parts else ""
