"""
Agent 3: Matcher / Ranker Agent

Takes a parsed job description + a list of parsed candidate resumes,
and produces a ranked top-5 list with scores and human-readable reasoning
for why each candidate fits (or doesn't fully fit).

Design note: we send ALL candidates to the LLM in a single call along with
the JD, and ask it to reason about and rank all of them together. This is
more consistent than scoring each resume independently in isolation,
because the model can compare candidates relative to each other.

For larger candidate pools (50+) this single-call approach would need to be
chunked/batched, but for a prototype this is the simplest correct design.
"""
from app.services.grok_client import call_grok_json

SYSTEM_PROMPT = """You are a Candidate Matching & Ranking Agent in a recruiting pipeline.
You will be given:
1. A structured job description (requirements, skills, experience level)
2. A list of structured candidate profiles (parsed from resumes), each with a student_id

Your job is to evaluate EVERY candidate against the job description and
return the TOP 5 best-fit candidates, ranked best to worst.

Scoring guidance:
- Weigh must-have skill overlap most heavily.
- Give partial credit for related/transferable skills (e.g. Django experience is
  relevant for a Flask role).
- Consider experience years relative to min_experience_years.
- Consider relevant projects as evidence of practical skill even if work history is thin
  (this matters a lot for student/fresher candidates).
- nice_to_have_skills should boost score but never be treated as mandatory.

If there are fewer than 5 candidates total, rank and return all of them.

Return a JSON object with EXACTLY this shape:
{
  "ranked_candidates": [
    {
      "student_id": number,
      "rank": number,                  // 1 = best fit
      "match_score": number,           // 0-100
      "matched_skills": [string],      // skills the candidate has that match the JD
      "missing_skills": [string],      // important JD skills the candidate lacks
      "reasoning": string              // 2-4 sentence explanation of the score, written for a recruiter to read
    }
  ]
}
"""


def rank_candidates(job_description_json: dict, candidates: list[dict]) -> dict:
    """
    candidates: list of dicts like {"student_id": int, "name": str, "profile": <parsed resume json>}
    Returns the raw LLM JSON output: {"ranked_candidates": [...]}
    """
    user_prompt = (
        "JOB DESCRIPTION (structured):\n"
        f"{job_description_json}\n\n"
        "CANDIDATES (structured resume profiles):\n"
        f"{candidates}\n\n"
        "Evaluate all candidates and return the top 5 ranked best to worst."
    )

    result = call_grok_json(SYSTEM_PROMPT, user_prompt, temperature=0.2)
    return result
