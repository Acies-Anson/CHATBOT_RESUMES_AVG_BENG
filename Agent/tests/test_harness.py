from __future__ import annotations

import os
import json
import logging
import traceback
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.agent import Agent2

load_dotenv()
print("\nTRACE DEBUG:")
print("LANGCHAIN_TRACING_V2 =", os.getenv("LANGCHAIN_TRACING_V2"))
print("LANGCHAIN_PROJECT =", os.getenv("LANGCHAIN_PROJECT"))
print("LANGCHAIN_API_KEY =", "SET" if os.getenv("LANGCHAIN_API_KEY") else "MISSING")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")


def _masked_key_prefix(value: str | None) -> str:
    if not value:
        return "missing"
    cleaned = value.strip()
    if not cleaned:
        return "missing"
    return f"{cleaned[:6]}... (len={len(cleaned)})"


def _db_status(db_uri: str) -> str:
    try:
        engine = create_engine(db_uri, future=True)
        with engine.connect() as connection:
            row = connection.execute(text("SELECT @@SERVERNAME AS server_name, DB_NAME() AS db_name")).mappings().first()
        if not row:
            return "DB=Connected (server/db not returned)"
        return f"DB=Connected server={row['server_name']} db={row['db_name']}"
    except Exception as exc:  # noqa: BLE001
        return f"DB=Failed ({exc})"


def _openrouter_status() -> str:
    key = os.getenv("OPENROUTER_API_KEY")
    key_signal = _masked_key_prefix(key)
    if not key or not key.strip():
        return "OpenRouter=Blocked (missing OPENROUTER_API_KEY)"

    models = os.getenv("OPENROUTER_MODELS", "").strip() or os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b")
    return f"OpenRouter=Configured models={models} key={key_signal}"


def _langsmith_status() -> str:
    enabled = (os.getenv("LANGCHAIN_TRACING_V2") or "").strip().lower() in {"1", "true", "yes", "on"}
    if not enabled:
        return "LangSmith=Disabled (set LANGCHAIN_TRACING_V2=true to enable)"

    key = os.getenv("LANGCHAIN_API_KEY")
    key_signal = _masked_key_prefix(key)
    if not key or not key.strip():
        return "LangSmith=Blocked (missing LANGCHAIN_API_KEY)"

    project = os.getenv("LANGCHAIN_PROJECT", "agent2")
    endpoint = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    return f"LangSmith=Enabled project={project} endpoint={endpoint} key={key_signal}"

def run_harness() -> None:
    db_uri = os.getenv("DB_URI")
    if not db_uri:
        raise EnvironmentError("DB_URI is missing. Configure .env before running the harness.")

    print("\n" + "=" * 80, flush=True)
    print("PRECHECK", flush=True)
    print("-" * 80, flush=True)
    print(_db_status(db_uri), flush=True)
    print(_openrouter_status(), flush=True)
    print(_langsmith_status(), flush=True)

    agent = Agent2()

    tests = [
        {
            "name": "Total revenue by region",
            "question": "What is total revenue by region?",
            "sql": "SELECT region, SUM(price * quantity) AS revenue FROM Orders GROUP BY region ORDER BY revenue DESC",
        },
        {
            "name": "Top 5 products",
            "question": "Which 5 products sold the most units?",
            "sql": "SELECT TOP 5 product, SUM(quantity) AS total_units FROM Orders GROUP BY product ORDER BY total_units DESC",
        },
        {
            "name": "Customer spending",
            "question": "Which customers spend the most?",
            "sql": "SELECT customer_id, SUM(price * quantity) AS lifetime_spend FROM Orders GROUP BY customer_id ORDER BY lifetime_spend DESC",
        },
        {
            "name": "Empty results edge case",
            "question": "Any orders for impossible product id?",
            "sql": "SELECT order_id, product FROM Orders WHERE product = '__definitely_missing__'",
        },
        {
            "name": "Null values edge case",
            "question": "Show records that contain nulls in critical fields.",
            "sql": "SELECT customer_id, region, price, quantity FROM Orders WHERE customer_id IS NULL OR region IS NULL OR price IS NULL OR quantity IS NULL",
        },
        {
            "name": "Malformed SQL edge case",
            "question": "This should fail validation.",
            "sql": "SELEC customer_id FORM Orders",
        },
        {
            "name": "Unsafe SQL edge case",
            "question": "This should fail safety checks.",
            "sql": "DELETE FROM Orders",
        },
        {
            "name": "Large dataset edge case",
            "question": "Validate automatic TOP 100 protection.",
            "sql": "SELECT * FROM Orders",
        },
        {
            "name": "Full Orders table dump",
            "question": "Show all rows in Orders so we can verify local DB connectivity.",
            "sql": "SELECT order_id, order_date, customer_id, region, product, price, quantity FROM Orders ORDER BY order_id",
            "print_full_table": True,
        },
    ]

    for case in tests:
        print("\n" + "=" * 80, flush=True)
        print(f"TEST: {case['name']}", flush=True)
        print("-" * 80, flush=True)
        try:
            result = agent.run(case["sql"], case["question"])
            print(f"Rows returned: {result['row_count']}", flush=True)
            if case.get("print_full_table"):
                print("Data (full table):", flush=True)
                for idx, row in enumerate(result["data"], start=1):
                    print(f"{idx:>3}: {json.dumps(row, default=str, ensure_ascii=True)}", flush=True)
            print("Summary:", flush=True)
            print(result["summary"], flush=True)
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR: {exc}", flush=True)
            print(traceback.format_exc(), flush=True)


if __name__ == "__main__":
    run_harness()
