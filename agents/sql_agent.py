import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
model_name = os.getenv("MODEL_NAME", "openai/gpt-4o-mini")

# LangSmith setup
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "true")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "resume_chatbot")

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
- Return only a valid PostgreSQL SELECT query.
- No markdown, no explanations, no text before or after the query.
- Use ILIKE '%keyword%' for text search.
- For aggregates or counts, use COUNT(), COUNT(DISTINCT), or SUM() as appropriate.
- For GROUP BY queries, include the group column and an aggregate.
- Do not include LIMIT; the system will handle pagination.

User question:
{question}

SQL Query:
"""

def generate_sql(question: str) -> str:
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not set")

    llm = ChatOpenAI(
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        model=model_name,
        temperature=0
    )

    prompt = sql_prompt_template.format(
        schema=schema.strip(),
        question=question.strip()
    )

    response = llm.invoke(prompt)
    return response.content.strip()


def validate_sql(sql: str) -> str:
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]
    for word in forbidden:
        if word in sql.upper():
            raise ValueError("Unsafe query detected")
    return sql