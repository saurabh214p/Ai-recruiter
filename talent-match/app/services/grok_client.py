"""
Thin wrapper around the xAI Grok API.

Grok exposes an OpenAI-compatible endpoint, so we use the `openai` SDK
pointed at xAI's base_url. This keeps our agent code simple and lets us
swap providers later (Claude, OpenAI, etc.) by only touching this file.

Set your key as an environment variable before running the app:
    export XAI_API_KEY="your-key-here"      (Mac/Linux)
    setx XAI_API_KEY "your-key-here"        (Windows)

We deliberately do NOT hardcode a key anywhere in this codebase.
"""
import os
import json
import logging

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logger = logging.getLogger(__name__)

XAI_API_KEY = os.getenv("XAI_API_KEY", "")  # left blank intentionally — set this yourself
XAI_BASE_URL = "https://api.x.ai/v1"
GROK_MODEL = "grok-4.3"

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        if not XAI_API_KEY:
            logger.warning(
                "XAI_API_KEY is not set. Calls to Grok will fail until you export it."
            )
        _client = OpenAI(api_key=XAI_API_KEY, base_url=XAI_BASE_URL)
    return _client


def call_grok_json(system_prompt: str, user_prompt: str, temperature: float = 0.2) -> dict:
    """
    Calls Grok and expects a strict JSON object back.
    Used by all three agents (resume parser, JD parser, matcher) since
    they all need structured, parseable output rather than free text.

    Raises on API failure or invalid JSON — callers are expected to catch
    and record this as a parse_status="failed" row rather than crash the request.
    """
    client = get_client()

    response = client.chat.completions.create(
        model=GROK_MODEL,
        temperature=temperature,
        messages=[
            {
                "role": "system",
                "content": system_prompt
                + "\n\nYou must respond with ONLY a valid JSON object. "
                  "No markdown formatting, no ```json fences, no preamble, no explanation outside the JSON.",
            },
            {"role": "user", "content": user_prompt},
        ],
    )

    content = response.choices[0].message.content.strip()

    # Defensive cleanup in case the model wraps output in code fences anyway
    if content.startswith("```"):
        content = content.strip("`")
        if content.lower().startswith("json"):
            content = content[4:]
        content = content.strip()

    return json.loads(content)
