import os
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
model_name = os.getenv("MODEL_NAME", "openai/gpt-4o-mini")

schema = """
Table: cleaned_data

Columns:
- occupation (text)
- name (text)
- email (text)
- phone_no (text)
- location (text)
- skills (text)
- experience (text)
- education (text)
- other_details (text)
- resume_id (text)
- email_valid (boolean)
- phone_valid (boolean)
"""

sql_prompt_template = """
You are an expert PostgreSQL query generator for resume search.

Database Schema:
{schema}

Rules:
- Return only one valid PostgreSQL SELECT query.
- Do not wrap the query in markdown or code fences.
- Do not explain your answer.
- Use only columns that exist in the schema.
- Use ILIKE for text filtering on name, skills, location, education, and occupation.
- Use = TRUE / FALSE for boolean fields.
- Use COUNT(*) and GROUP BY for count or breakdown questions.
- Use ORDER BY for ranking or top result questions.
- Do not include LIMIT; the retriever adds it.

User Question:
{question}

SQL Query:
"""

def generate_sql(question):
    prompt = sql_prompt_template.format(schema=schema.strip(), question=question.strip())

    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not set")

    payload = {
        "model": model_name,
        "temperature": 0,
        "messages": [{"role": "user", "content": prompt}],
    }

    request = Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            result = json.loads(body)
            return result["choices"][0]["message"]["content"].strip()

    except Exception as exc:
        raise RuntimeError(f"SQL generation failed: {exc}") from exc


def validate_sql(sql):
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT"]
    for word in forbidden:
        if word in sql.upper():
            raise ValueError("Unsafe query detected")
    return sql