"""
Agent 1: Resume Parser Agent

Takes raw resume text (extracted from PDF) and converts it into a
structured JSON profile: contact info, skills, experience, education,
projects, certifications. This structured form is what the Matcher
Agent later compares against a job description.
"""
from app.services.grok_client import call_grok_json

SYSTEM_PROMPT = """You are a Resume Parser Agent in a recruiting pipeline.
Your job is to read raw resume text (extracted from a PDF, so spacing/formatting
may be imperfect) and extract a clean, structured profile.

Extract ONLY information that is actually present in the text. Do not invent
details. If a field is not present, use an empty string, empty list, or null
as appropriate.

Return a JSON object with EXACTLY this shape:
{
  "full_name": string,
  "email": string,
  "phone": string,
  "summary": string,                  // 1-3 sentence professional summary, written by you based on the resume
  "total_experience_years": number,   // your best estimate based on work history dates, 0 if fresher/no experience
  "skills": [string],                 // technical and soft skills, deduplicated, normalized casing (e.g. "Python" not "python")
  "education": [
    {"degree": string, "institution": string, "year": string, "gpa_or_grade": string}
  ],
  "work_experience": [
    {"role": string, "company": string, "duration": string, "description": string}
  ],
  "projects": [
    {"name": string, "description": string, "tech_stack": [string]}
  ],
  "certifications": [string]
}
"""


def parse_resume(raw_text: str) -> dict:
    """
    Calls the LLM to parse resume text into structured JSON.
    Raises (json.JSONDecodeError, KeyError, openai errors) on failure —
    caller is responsible for catching and marking parse_status="failed".
    """
    user_prompt = f"Resume text:\n\n{raw_text}"
    parsed = call_grok_json(SYSTEM_PROMPT, user_prompt, temperature=0.1)
    return parsed
