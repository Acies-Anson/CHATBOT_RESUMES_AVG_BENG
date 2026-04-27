# from dotenv import load_dotenv
# import os
# import requests
# import json
# from langchain_openai import ChatOpenAI

# # -------------------------
# # LOAD ENV VARIABLES
# # -------------------------
# load_dotenv()

# API_KEY = os.getenv("OPENROUTER_API_KEY")
# MODEL = os.getenv("MODEL_NAME", "openai/gpt-4o-mini")

# if not API_KEY:
#     raise ValueError("❌ API key not found! Check your .env file")

# # -------------------------
# # OPTIONAL: RAW API CALL (DEBUG / TEST)
# # -------------------------
# def call_openrouter(prompt):
#     response = requests.post(
#         url="https://openrouter.ai/api/v1/chat/completions",
#         headers={
#             "Authorization": f"Bearer {API_KEY}",
#             "Content-Type": "application/json",
#         },
#         data=json.dumps({
#             "model": MODEL,
#             "messages": [
#                 {"role": "user", "content": prompt}
#             ]
#         })
#     )

#     result = response.json()

#     if "choices" not in result:
#         print("⚠️ API failed:", result)
#         return None

#     return result['choices'][0]['message']['content']


# # -------------------------
# # LLM (LANGCHAIN)
# # -------------------------
# llm = ChatOpenAI(
#     model=MODEL,
#     temperature=0,
#     openai_api_key=API_KEY,
#     openai_api_base="https://openrouter.ai/api/v1"
# )

# # -------------------------
# # SCHEMA
# # -------------------------
# schema = """
# Table: cleaned_data

# Columns:
# - id (integer): auto-increment primary key
# - name (varchar): full name of candidate
# - email (varchar): email address
# - phone_no (varchar): phone number
# - location (varchar): current city
# - skills (varchar): comma-separated skills like Python, SQL
# - experience (varchar): experience details (e.g., '5 years', '3+ years')
# - education (varchar): highest qualification
# - occupation (varchar): current job role or profession
# - other_details (varchar): additional information about the candidate
# """

# # -------------------------
# # GENERATE SQL FUNCTION
# # -------------------------
# def generate_sql(question):
#     prompt = f"""
# You are an expert PostgreSQL query generator.

# Database Schema:
# {schema}

# Rules:
# - Only generate SQL query
# - No explanation
# - Use PostgreSQL syntax
# - Use ILIKE for text search
# - Only SELECT queries
# - Do not hallucinate columns

# User Question:
# {question}

# SQL Query:
# """
#     response = llm.invoke(prompt)
#     return response.content.strip()

# # -------------------------
# # VALIDATION
# # -------------------------
# def validate_sql(sql):
#     forbidden = ["DROP", "DELETE", "UPDATE", "INSERT"]
#     for word in forbidden:
#         if word in sql.upper():
#             raise ValueError("❌ Unsafe query detected!")
#     return sql

# # -------------------------
# # MAIN
# # -------------------------
# def main():
#     print("✅ Agent 1 is ready! (type 'exit' to quit)")

#     while True:
#         user_input = input("\nAsk your question: ")

#         if user_input.lower() == "exit":
#             print("👋 Exiting...")
#             break

#         try:
#             print("\n" + "=" * 50)
#             print("🟡 USER QUESTION:")
#             print(user_input)

#             # Generate SQL using LLM
#             sql = generate_sql(user_input)
#             sql = validate_sql(sql)

#             print("\n🟢 GENERATED SQL:")
#             print(sql)

#             # OPTIONAL: debug raw API call
#             # debug_response = call_openrouter(user_input)
#             # print("\n🔵 RAW API RESPONSE:")
#             # print(debug_response)

#             print("=" * 50)

#         except Exception as e:
#             print("❌ Error:", e)


# # -------------------------
# # ENTRY POINT
# # -------------------------
# if __name__ == "__main__":
#     main()

from agents.sql_agent import generate_sql, validate_sql

def call_openrouter(prompt):
    try:
        sql = generate_sql(prompt)
        sql = validate_sql(sql)
        return sql
    except Exception as e:
        return f"Error: {str(e)}"