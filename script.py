import os
import json
from pathlib import Path
from dotenv import load_dotenv
from agents.retrieval_summarizer_agent import RetrievalSummarizerAgent

env_path = Path(__file__).resolve().parent / "agents" / ".env"
load_dotenv(env_path)

def get_db_config():
    return {
        "host": os.getenv("NEON_HOST"),
        "port": int(os.getenv("NEON_PORT", 5432)),
        "dbname": os.getenv("NEON_DBNAME"),
        "user": os.getenv("NEON_USER"),
        "password": os.getenv("NEON_PASSWORD"),
        "sslmode": "require",
    }


def _store_latest_result(payload: dict) -> str:
    output_dir = Path(__file__).resolve().parent / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "latest_retrieval.json"
    output_file.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return str(output_file)


def call_openrouter(prompt: str) -> dict:
    """Main app entry: user prompt -> SQL retrieval -> summary + sql + rows payload."""
    try:
        agent = RetrievalSummarizerAgent(get_db_config())
        result = agent.handle(prompt)
        payload = result if isinstance(result, dict) else {
            "query": prompt,
            "sql": "N/A",
            "summary": str(result),
            "results": [],
        }
        payload["stored_at"] = _store_latest_result(payload)
        return payload
    except Exception as e:
        error_payload = {
            "query": prompt,
            "sql": "FAILED",
            "summary": f"Error: {str(e)}",
            "results": [],
        }
        error_payload["stored_at"] = _store_latest_result(error_payload)
        return error_payload