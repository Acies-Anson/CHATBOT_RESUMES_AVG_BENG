import psycopg2
import re
from typing import Dict, Any, List

from agents.sql_agent import generate_sql, validate_sql


class RetrievalSummarizerAgent:

    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config

    def connect(self):
        return psycopg2.connect(**self.db_config)

    # Clean SQL properly
    def _clean_sql(self, sql: str) -> str:
        sql = sql.strip()

        # remove markdown/code blocks
        sql = re.sub(r"```.*?```", "", sql, flags=re.DOTALL)

        # extract SELECT query
        match = re.search(r"(SELECT .*?)(;|$)", sql, re.IGNORECASE | re.DOTALL)
        if match:
            sql = match.group(1)

        # remove LIMIT if present
        sql = re.sub(r"\bLIMIT\s+\d+\b", "", sql, flags=re.IGNORECASE)

        return sql.strip()

    def run_query(self, sql_query: str) -> List[Dict]:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_query)
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]

    def handle(self, user_query: str):

        try:
            raw_sql = generate_sql(user_query)

            base_query = self._clean_sql(raw_sql)
            base_query = validate_sql(base_query)

            results = self.run_query(base_query)
            sql_query = base_query

            #Retry with relaxed query if empty
            if not results:
                relaxed_query = f"""
                SELECT name, location, skills, experience
                FROM cleaned_data
                WHERE skills ILIKE '%{user_query}%'
                   OR occupation ILIKE '%{user_query}%'
                LIMIT 10
                """
                results = self.run_query(relaxed_query)
                sql_query = relaxed_query

        except Exception as e:
            print("First attempt failed:", e)

            try:
                sql_query = """
                SELECT name, location, skills, experience
                FROM cleaned_data
                LIMIT 10
                """
                results = self.run_query(sql_query)

            except Exception as retry_error:
                return {
                    "query": user_query,
                    "sql": "FAILED",
                    "summary": f"Query failed: {str(retry_error)}",
                    "results": []
                }

        # Build a narrative summary and a short preview of the results
        summary = self._summarize(results, user_query)

        preview = []
        for row in results[:5]:
            preview.append({
                "name": row.get("name") or "Unknown",
                "location": row.get("location") or "Unknown",
                "skills": row.get("skills") or "N/A",
            })

        return {
            "query": user_query,
            "sql": sql_query,
            "summary": summary,
            "results": preview,
            "total_matches": results[0].get("total_count", len(results)) if results else 0,
        }

    def _truncate(self, text: str, max_len: int = 80) -> str:
        if not text:
            return "N/A"
        text = text.replace("\n", " ").strip()
        return text[:max_len] + ("..." if len(text) > max_len else "")


    def _summarize(self, results: List[Dict[str, Any]], user_query: str) -> str:
        """Return a concise narrative summary describing the retrieval results.

        The summary emphasizes counts and top breakdowns rather than dumping rows.
        """

        if not results:
            return "No matching candidates found for your query."

        total = results[0].get("total_count", len(results)) if results else 0

        # Detect grouped/count-style results (e.g., COUNT(*) GROUP BY field)
        # If rows look like {'location': 'X', 'count': 10} or similar, format accordingly.
        first_row = results[0]
        numeric_keys = [k for k, v in first_row.items() if isinstance(v, (int, float))]
        non_numeric_keys = [k for k in first_row.keys() if k not in numeric_keys]

        if numeric_keys and non_numeric_keys:
            # Use the first non-numeric key as the group column, first numeric as count
            group_col = non_numeric_keys[0]
            count_col = numeric_keys[0]

            groups = []
            for row in results[:10]:
                groups.append(f"{row.get(group_col)} ({row.get(count_col)})")

            total_groups = len(results)
            return (
                f"Found {total_groups} groups for '{group_col}'. "
                f"Top groups: {', '.join(groups)}."
            )

        # Aggregate top locations and skills for regular result sets
        location_count = {}
        skill_count = {}
        for row in results:
            loc = (row.get("location") or "Unknown").strip() or "Unknown"
            location_count[loc] = location_count.get(loc, 0) + 1

            skills = row.get("skills") or ""
            for s in [s.strip().lower() for s in skills.split(",") if s.strip()]:
                skill_count[s] = skill_count.get(s, 0) + 1

        top_locations = sorted(location_count.items(), key=lambda x: x[1], reverse=True)[:3]
        top_skills = sorted(skill_count.items(), key=lambda x: x[1], reverse=True)[:5]

        loc_text = ", ".join([f"{loc} ({count})" for loc, count in top_locations]) or "N/A"
        skill_text = ", ".join([f"{skill} ({count})" for skill, count in top_skills]) or "N/A"

        # Example names for context
        example_names = [row.get("name") or "Unknown" for row in results[:3]]

        # Special case: if user asked about email, phrase it
        if "email" in (user_query or "").lower():
            return (
                f"Found {total} candidates related to email in the dataset. "
                f"Example candidates: {', '.join(example_names)}. "
                "These candidates may require email verification or correction."
            )

        summary_parts = []
        summary_parts.append(f"Found {total} matching candidates.")
        summary_parts.append(f"Top locations: {loc_text}.")
        summary_parts.append(f"Top skills: {skill_text}.")
        if example_names:
            summary_parts.append(f"Example candidates: {', '.join(example_names)}.")
        summary_parts.append("This is a summary of the retrieval; use the preview to inspect a few candidates.")

        return " ".join(summary_parts)