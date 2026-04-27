from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")

llm = ChatOpenAI(
    model="openai/gpt-4o-mini",
    temperature=0,
    openai_api_key=api_key,
    openai_api_base="https://openrouter.ai/api/v1"
)

schema = """
Table: cleaned_data

Columns:
id, name, email, phone_no, location, skills, experience, education, occupation, other_details
"""

def generate_sql(question):
    prompt = f"""
You are an expert PostgreSQL query generator.

Database Schema:
{schema}

Rules:
Only generate SQL query
No explanation
Use PostgreSQL syntax
Use ILIKE for text search
Only SELECT queries

User Question:
{question}

SQL Query:
"""
    response = llm.invoke(prompt)
    return response.content.strip()


def validate_sql(sql):
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT"]
    for word in forbidden:
        if word in sql.upper():
            raise ValueError("❌ Unsafe query detected!")
    return sql