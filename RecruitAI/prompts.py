"""
RecruitAI - Prompt Templates
All LLM prompt templates used by the agents.

Each prompt is designed to return structured JSON for reliable parsing.
Prompts use double curly braces {{ }} for literal braces in the output format
and single curly braces { } for Python .format() placeholders.
"""

# ============================================================
# Resume Agent Prompt
# ============================================================
RESUME_EXTRACTION_PROMPT = """You are an expert resume parser and information extractor.

Analyze the following resume text and extract structured information.

Resume Text:
---
{resume_text}
---

Extract the following fields and return as a JSON object:
{{
    "student_name": "Full name of the candidate",
    "education": ["List of education entries, e.g., 'B.Tech Computer Science, XYZ University, 2024'"],
    "experience": ["List of work experience entries, e.g., 'Software Intern at ABC Corp (3 months) - Worked on REST APIs'"],
    "skills": ["List of ALL technical and soft skills mentioned"],
    "projects": ["List of project descriptions, each as 'Project Name - brief description'"],
    "summary": "A concise 2-3 sentence professional summary of the candidate"
}}

Rules:
1. Extract ALL skills mentioned, including programming languages, frameworks, tools, and soft skills.
2. For projects, include the project name and a brief one-line description.
3. For experience, include company name, role, duration, and key responsibilities.
4. If a field is not found in the resume, use an empty list [] or empty string "".
5. Return ONLY valid JSON. No markdown, no explanation, no extra text.
6. The summary should highlight the candidate's key strengths, skills, and focus areas."""


# ============================================================
# JD Agent Prompt
# ============================================================
JD_EXTRACTION_PROMPT = """You are an expert job description analyzer.

Analyze the following job description and extract structured information.

Job Description:
---
{jd_text}
---

Extract the following fields and return as a JSON object:
{{
    "required_skills": ["List of mandatory/required technical skills and tools"],
    "preferred_skills": ["List of preferred/nice-to-have skills"],
    "experience": "Experience requirement as a string, e.g., '2+ years in backend development'",
    "education": "Education requirement as a string, e.g., 'B.Tech/B.E. in Computer Science or related field'",
    "summary": "A concise 2-3 sentence summary of what the role involves and what kind of candidate is ideal"
}}

Rules:
1. Differentiate clearly between required and preferred skills.
2. Include programming languages, frameworks, tools, databases, cloud platforms, and methodologies.
3. If experience is not explicitly specified, use "Not specified".
4. If education is not explicitly specified, use "Not specified".
5. Return ONLY valid JSON. No markdown, no explanation, no extra text."""


# ============================================================
# Explanation Agent Prompt
# ============================================================
EXPLANATION_PROMPT = """You are a recruitment advisor generating candidate match explanations.

Given a Job Description and a Candidate profile, generate a concise, recruiter-friendly explanation
of why this candidate is a good (or partial) match for the role.

**Job Description:**
- Summary: {jd_summary}
- Required Skills: {required_skills}
- Preferred Skills: {preferred_skills}

**Candidate Profile:**
- Name: {student_name}
- Skills: {candidate_skills}
- Projects: {candidate_projects}
- Experience: {candidate_experience}
- Education: {candidate_education}
- Overall Match Score: {match_score}%

Generate a brief explanation using bullet points that covers:
1. ✅ Matching required skills the candidate has
2. ⭐ Any preferred skills the candidate also has
3. 🚀 Relevant project experience that demonstrates practical ability
4. 📋 Notable strengths or standout qualities
5. ⚠️ Any missing required skills or gaps

Keep it concise (4-6 bullet points). Be specific — reference actual skill names and project names.
Do NOT wrap in JSON. Return plain text with bullet points only."""


# ============================================================
# Ranking Batch Prompt (optional, for LLM-based scoring)
# ============================================================
RANKING_BATCH_PROMPT = """You are evaluating candidates against a job description.

Job Description:
- Required Skills: {required_skills}
- Preferred Skills: {preferred_skills}
- Experience Required: {experience}
- Education Required: {education}
- Summary: {summary}

For each candidate below, score these dimensions from 0.0 to 1.0:
- project_relevance: How relevant are the candidate's projects to this role?
- experience_fit: How well does the candidate's experience match the requirements?
- education_fit: How well does the candidate's education match the requirements?

Candidates:
{candidates_text}

Return a JSON array with one object per candidate:
[
    {{
        "student_name": "Name",
        "project_relevance": 0.0,
        "experience_fit": 0.0,
        "education_fit": 0.0
    }}
]

Rules:
1. Score strictly between 0.0 and 1.0.
2. Be fair and consistent across all candidates.
3. Return ONLY valid JSON array. No markdown, no explanation."""
