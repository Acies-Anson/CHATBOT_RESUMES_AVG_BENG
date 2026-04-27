import os
import json
from urllib.request import Request, urlopen
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

Schema:
{schema}

Rules:
- Return a single valid PostgreSQL SELECT query only.
- Do not include explanations or markdown.
- Prefer explicit columns (avoid SELECT *).
- Use ILIKE '%keyword%' for text filters.
- Combine multiple skills with AND.
- Include a location filter if the user specifies location.
- For "top" or "best" requests, ORDER BY experience DESC.
- For counts, use COUNT(*) and GROUP BY as needed.
- Do not include LIMIT; the caller will add it.

User question:
{question}

SQL Query:
"""

# Example (count by location):
# Question: Count candidates by location
# SQL: SELECT location AS group_field, COUNT(*) AS count
#      FROM cleaned_data
#      GROUP BY location
#      ORDER BY count DESC

def generate_sql(question: str) -> str:
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not set")

    prompt = sql_prompt_template.format(
        schema=schema.strip(),
        question=question.strip()
    )

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

    with urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8")
        result = json.loads(body)

    return result["choices"][0]["message"]["content"].strip()


def validate_sql(sql: str) -> str:
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]
    for word in forbidden:
        if word in sql.upper():
            raise ValueError("Unsafe query detected")
    return sql