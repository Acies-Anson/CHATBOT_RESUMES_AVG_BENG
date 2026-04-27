from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI

# -------------------------
# LOAD ENV VARIABLES
# -------------------------
load_dotenv()

# -------------------------
# CHECK API KEY
# -------------------------
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise ValueError("❌ API key not found! Check your .env file")

# -------------------------
# LLM (OPENROUTER)
# -------------------------
llm = ChatOpenAI(
    model="openai/gpt-4o-mini",
    temperature=0,
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

# -------------------------
# SCHEMA
# -------------------------
schema = """
Table: resumes

Columns:
- id (integer): unique candidate ID
- name (text): full name of candidate
- email (text): email address
- skills (text): comma-separated skills like Python, SQL
- experience_years (integer): total years of experience
- education (text): highest qualification
- location (text): current city
"""

# -------------------------
# GENERATE SQL FUNCTION
# -------------------------
def generate_sql(question):
    prompt = f"""
You are an expert PostgreSQL query generator.

Database Schema:
{schema}

Rules:
- Only generate SQL query
- No explanation
- Use PostgreSQL syntax
- Use ILIKE for text search
- Only SELECT queries
- Do not hallucinate columns

User Question:
{question}

SQL Query:
"""

    response = llm.invoke(prompt)
    return response.content.strip()

# -------------------------
# VALIDATION
# -------------------------
def validate_sql(sql):
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT"]
    for word in forbidden:
        if word in sql.upper():
            raise ValueError("❌ Unsafe query detected!")
    return sql

# -------------------------
# MAIN
# -------------------------
def main():
    print("✅ Agent 1 is ready! (type 'exit' to quit)")

    while True:
        user_input = input("\nAsk your question: ")

        if user_input.lower() == "exit":
            print("👋 Exiting...")
            break

        try:
            sql = generate_sql(user_input)
            sql = validate_sql(sql)

            print("\n🟢 Generated SQL:\n")
            print(sql)

        except Exception as e:
            print("❌ Error:", e)

# -------------------------
# ENTRY POINT
# -------------------------
if __name__ == "__main__":
    main()