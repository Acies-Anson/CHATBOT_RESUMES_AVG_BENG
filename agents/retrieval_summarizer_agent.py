import psycopg2
from typing import Dict, Any, List
from agents.sql_agent import generate_sql, validate_sql
import re


class RetrievalSummarizerAgent:

    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config

    def connect(self):
        return psycopg2.connect(**self.db_config)

    def _clean_sql(self, sql: str) -> str:
        sql = sql.strip()
        sql = sql.replace("```sql", "").replace("```", "")
        if "SELECT" in sql.upper():
            sql = sql[sql.upper().find("SELECT"):]
        sql = sql.strip().rstrip(";").strip()
        sql = re.sub(r"\bLIMIT\s+\d+\b", "", sql, flags=re.IGNORECASE)

        return sql

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

            sql_query = f"""
            SELECT *, COUNT(*) OVER() AS total_count
            FROM ({base_query}) AS subquery
            LIMIT 10
            """

            results = self.run_query(sql_query)

        except Exception as e:
            print(" First attempt failed:", e)

            try:
                sql_query = """
                SELECT *, COUNT(*) OVER() AS total_count
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

        summary = self._summarize(results)

        return {
            "query": user_query,
            "sql": sql_query,
            "summary": summary,
            "results": results
        }

    def _summarize(self, results: List[Dict[str, Any]]) -> str:
        if not results:
            return "No matching candidates found."

        total = results[0].get("total_count", len(results))
        shown = len(results)

        preview = results[:5]

        bullet_lines = []
        for idx, row in enumerate(preview, start=1):
            name = row.get("name") or "Unknown"
            location = row.get("location") or "Unknown"
            skills = row.get("skills") or "N/A"
            bullet_lines.append(f"{idx}. {name} | {location} | {skills}")

        # Top locations
        location_count = {}
        for row in results:
            loc = (row.get("location") or "Unknown").strip() or "Unknown"
            location_count[loc] = location_count.get(loc, 0) + 1

        top_locations = sorted(location_count.items(), key=lambda x: x[1], reverse=True)[:3]
        location_text = ", ".join([f"{loc} ({count})" for loc, count in top_locations])

        return (
            f"I found {total} matching candidates.\n"
            f"Showing top {shown} results.\n\n"
            f"Top locations: {location_text}\n\n"
            "Examples:\n" + "\n".join(bullet_lines)
        )