RESUME_PARSING_PROMPT = """
You are an expert HR assistant. Extract information from the following resume text and return ONLY a valid JSON object.

Resume Text:
{resume_text}

Extract the following information and return as JSON:

{{
    "personal_detail": {{
        "full_name": "string",
        "email": "string",
        "contact_no": "string",
        "gender": "string or null",
        "nationality": "string or null"
    }},
    "address": {{
        "address": "string or null",
        "city": "string or null",
        "state": "string or null",
        "country": "string or null",
        "zip_code": "string or null"
    }},
    "education": [
        {{
            "degree": "string",
            "school": "string",
            "start_date": "string or null",
            "end_date": "string or null"
        }}
    ],
    "experience": [
        {{
            "job_title": "string",
            "company_name": "string",
            "start_date": "string or null",
            "end_date": "string or null",
            "projects": "string or null"
        }}
    ],
    "skills": ["string"],
    "certifications": ["string"]
}}

Important:
- Return ONLY valid JSON, no additional text
- If information is not found, use null
- For lists, return empty array [] if no items found
- Dates should be in string format
"""


JD_PARSING_PROMPT = """
You are an expert HR assistant. Extract information from the following job description text and return ONLY a valid JSON object.

Job Description Text:
{jd_text}

Extract the following information and return as JSON:

{{
    "job_detail": {{
        "job_position": "string",
        "job_type": "string or null",
        "job_shift": "string or null",
        "job_industry": "string or null",
        "closing_date": "string or null",
        "min_experience": "number or null",
        "max_experience": "number or null",
        "no_of_openings": "number or null",
        "required_education": ["string"],
        "job_description": "string"
    }},
    "salary_range": {{
        "min_amount": "number or null",
        "max_amount": "number or null"
    }},
    "job_location": {{
        "city": "string or null",
        "state": "string or null",
        "country": "string or null",
        "zip_code": "string or null"
    }},
    "required_skills": ["string"]
}}

Important:
- Return ONLY valid JSON, no additional text
- If information is not found, use null
- For lists, return empty array [] if no items found
- Experience should be in years (numbers)
- Salary amounts should be numbers
"""


def get_resume_prompt(resume_text: str) -> str:
    return RESUME_PARSING_PROMPT.format(resume_text=resume_text)


def get_jd_prompt(jd_text: str) -> str:
    return JD_PARSING_PROMPT.format(jd_text=jd_text)
