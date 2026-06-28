"""
Agent 2: JD Parser Agent

Takes a raw job description (pasted by a recruiter) and extracts a
structured set of requirements: required skills, nice-to-have skills,
experience level, role responsibilities. This is what the Matcher Agent
uses as the "target" to score candidates against.
"""
from app.services.grok_client import call_grok_json

SYSTEM_PROMPT = """You are a Job Description Parser Agent in a recruiting pipeline.
Your job is to read a raw job description and extract a clean, structured
set of hiring requirements.

Extract ONLY information that is actually present or strongly implied by the text.
Do not invent requirements that aren't there.

Return a JSON object with EXACTLY this shape:
{
  "job_title": string,
  "summary": string,                       // 1-2 sentence summary of the role, written by you
  "must_have_skills": [string],            // explicitly required / non-negotiable skills, normalized casing
  "nice_to_have_skills": [string],         // preferred but optional skills
  "min_experience_years": number,          // 0 if entry-level/fresher role or not specified
  "education_requirements": [string],      // e.g. "Bachelor's in Computer Science or related field"
  "key_responsibilities": [string],
  "seniority_level": string                // one of: "intern", "entry", "mid", "senior", "lead", "unspecified"
}
"""


def parse_job_description(raw_text: str) -> dict:
    """
    Calls the LLM to parse a job description into structured JSON.
    Raises on failure — caller marks parse_status="failed".
    """
    user_prompt = f"Job description text:\n\n{raw_text}"
    parsed = call_grok_json(SYSTEM_PROMPT, user_prompt, temperature=0.1)
    return parsed
