import psycopg2
import re
import json
from typing import Dict, Any, List

from langchain_openai import ChatOpenAI
from agents.sql_agent import generate_sql, validate_sql, schema, api_key, model_name


class RetrievalSummarizerAgent:

    def __init__(self, db_config: str):
        self.db_config = db_config

    def connect(self):
        return psycopg2.connect(self.db_config)

    # Clean SQL properly
    def _clean_sql(self, sql: str) -> str:
        sql = sql.strip()

        # remove markdown/code blocks
        sql = re.sub(r"```.*?```", "", sql, flags=re.DOTALL)

        # extract SELECT query — use greedy match to preserve WHERE/GROUP BY clauses
        match = re.search(r"(SELECT .+?)(;|\s*$)", sql, re.IGNORECASE | re.DOTALL)
        if match:
            sql = match.group(1).strip()

        # remove LIMIT if present
        sql = re.sub(r"\bLIMIT\s+\d+\b", "", sql, flags=re.IGNORECASE)

        return sql.strip()

    def _extract_columns_from_sql(self, sql: str) -> List[str]:
        """Extract only the columns the user explicitly asked for in the SELECT clause.
        Returns empty list if SELECT * is used or if only aggregates with no alias exist
        (meaning no filtering should be applied — return all result columns).
        """
        sql = sql.strip()
        match = re.search(r"SELECT\s+(.*?)\s+FROM", sql, re.IGNORECASE | re.DOTALL)
        if not match:
            return []

        select_clause = match.group(1).strip()

        # If SELECT *, return empty list — no filtering needed
        if select_clause == "*":
            return []

        columns = []
        for col in select_clause.split(","):
            col = col.strip()

            # Handle aliases like "COUNT(*) AS total_count" — take alias
            alias_match = re.search(r"\bAS\s+(\w+)$", col, re.IGNORECASE)
            if alias_match:
                columns.append(alias_match.group(1).lower())
                continue

            # Handle aggregate functions like COUNT(*), COUNT(DISTINCT x), SUM(x)
            # These have no alias — psycopg2 returns them as "count", "sum", etc.
            agg_match = re.match(r"(\w+)\s*\(", col, re.IGNORECASE)
            if agg_match:
                columns.append(agg_match.group(1).lower())  # e.g. "count", "sum", "avg"
                continue

            # Plain column — strip table prefix like "t.name" -> "name"
            bare = col.split(".")[-1].strip().lower()
            if bare:
                columns.append(bare)

        return columns

    def run_query(self, sql_query: str) -> List[Dict]:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_query)
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]

    def handle(self, user_query: str):

        sql_query = None
        results = []

        # --- Step 1: Generate and run LLM SQL ---
        try:
            raw_sql = generate_sql(user_query)
            sql_query = self._clean_sql(raw_sql)
            sql_query = validate_sql(sql_query)
            results = self.run_query(sql_query)

        except Exception as e:
            print(f"Primary SQL failed: {e}")
            sql_query = None

        # --- Step 2: If primary failed or returned nothing, ask LLM to relax the query ---
        if not results:
            try:
                relaxed_prompt = f"""
The following query returned no results:
"{user_query}"

Rewrite it as a more relaxed PostgreSQL SELECT query using ILIKE with wildcards on relevant columns.
Use only this schema:
{schema}
Return only the SQL query, no explanation.
"""
                raw_relaxed = generate_sql(relaxed_prompt)
                relaxed_sql = self._clean_sql(raw_relaxed)
                relaxed_sql = validate_sql(relaxed_sql)
                results = self.run_query(relaxed_sql)
                sql_query = relaxed_sql
                print(f"Relaxed query used: {relaxed_sql}")

            except Exception as e:
                print(f"Relaxed SQL also failed: {e}")

        # --- Step 3: Hard fallback — return raw data if both attempts fail ---
        if not results and sql_query is None:
            try:
                sql_query = "SELECT * FROM cleaned_data LIMIT 10"
                results = self.run_query(sql_query)
            except Exception as final_error:
                return {
                    "query": user_query,
                    "sql": "FAILED",
                    "summary": f"Query failed: {str(final_error)}",
                    "results": []
                }

        # --- Step 4: Build summary ---
        summary = self._summarize(results, user_query)

        # --- Step 5: Filter columns to only what was requested in SQL ---
        requested_columns = self._extract_columns_from_sql(sql_query)

        # --- Step 6: Filter rows dynamically based on user query context ---
        rows_to_preview = self._filter_rows(results, user_query)

        # --- Step 7: Build preview with only requested columns ---
        preview = []
        for row in rows_to_preview:
            filtered_row = {
                key: (self._truncate(str(value)) if isinstance(value, str) else value)
                if value is not None else "N/A"
                for key, value in row.items()
                if not requested_columns or key.lower() in requested_columns
            }
            preview.append(filtered_row)

        return {
            "query": user_query,
            "sql": sql_query,
            "summary": summary,
            "results": preview,
            "total_matches": results[0].get("total_count", len(results)) if results else 0,
        }

    def _filter_rows(self, results: List[Dict], user_query: str) -> List[Dict]:
        """Dynamically filter rows based on any identifier mentioned in the user query.
        Supports: resume_id, any id column, name, email, phone.
        Falls back to returning all rows if no specific identifier is found.
        """
        if not results:
            return results

        # --- ID-based filter (resume_id = 3, id is 5, etc.) ---
        id_match = re.search(
            r"\b(?:resume[_\s]?id|candidate[_\s]?id|id)\s*[=:is]?\s*(\d+)",
            user_query, re.IGNORECASE
        )
        if id_match:
            asked_id = id_match.group(1).strip()
            matched = [
                row for row in results
                if any(str(v).strip() == asked_id for k, v in row.items() if "id" in k.lower())
            ]
            return matched if matched else results

        # --- Name-based filter ---
        name_match = re.search(
            r"\b(?:of|for|about|named?|called)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)",
            user_query, re.IGNORECASE
        )
        if name_match:
            asked_name = name_match.group(1).strip().lower()
            matched = [
                row for row in results
                if asked_name in (row.get("name") or "").lower()
            ]
            return matched if matched else results

        # --- Email-based filter ---
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", user_query)
        if email_match:
            asked_email = email_match.group(0).strip().lower()
            matched = [
                row for row in results
                if asked_email in (row.get("email") or "").lower()
            ]
            return matched if matched else results

        # --- No specific identifier — return all rows ---
        return results

    def _truncate(self, text: str, max_len: int = 80) -> str:
        if not text:
            return "N/A"
        text = text.replace("\n", " ").strip()
        return text[:max_len] + ("..." if len(text) > max_len else "")

    def _summarize(self, results: List[Dict[str, Any]], user_query: str) -> str:
        """Use LLM to generate a concise natural language summary of the retrieval results."""

        if not results:
            return "No matching results found for your query."

        # Limit data sent to LLM to avoid token overflow — send max 20 rows
        sample = results[:20]
        data_str = json.dumps(sample, indent=2, default=str)

        prompt = f"""You are a data analyst assistant summarizing database query results.

User asked: "{user_query}"

Retrieved {len(results)} result(s). Here is the data:
{data_str}

Write a concise, natural language summary of these results that directly answers the user's question.
- If it's a count or aggregate, state the number clearly.
- If it's a list of people, highlight key patterns (locations, skills, occupations).
- If it's a single person, summarize their profile.
- Keep it under 5 sentences.
- Do not mention SQL or technical details.
"""

        try:
            llm = ChatOpenAI(
                openai_api_key=api_key,
                openai_api_base="https://openrouter.ai/api/v1",
                model=model_name,
                temperature=0
            )
            response = llm.invoke(prompt)
            return response.content.strip()

        except Exception as e:
            print(f"LLM summarization failed: {e}")
            # Fallback to basic summary if LLM fails
            return f"Retrieved {len(results)} result(s) for your query."