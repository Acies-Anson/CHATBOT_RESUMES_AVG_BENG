# Agent 2: SQL Validation, Execution, and Insight Summarization

Agent 2 is a production-oriented backend/data pipeline that receives SQL from Agent 1, validates it for safety and correctness, executes it on SQL Server, and summarizes results using OpenRouter.

For complete database onboarding (including table creation and DB_URI formats), see `DATABASE_SETUP_GUIDE.md`.

## Features

- Strict SQL safety validation (read-only SELECT/CTE-only)
- Automatic TOP 100 enforcement when no TOP clause exists
- SQL Server execution via SQLAlchemy + pyodbc
- DataFrame-based result handling with pandas
- OpenRouter-based analytical summarization with model fallbacks
- LangGraph-style pipeline: validate -> execute -> summarize
- Retry logic for DB and LLM calls
- Deterministic local fallback summary when LLM is unavailable
- Test harness with normal + edge-case scenarios, including full `Orders` table dump

## Project Structure

agent2/
- agents/
  - agent.py
- db/
  - executor.py
  - validator.py
- llm/
  - summarizer.py
- graph/
  - graph.py
- tests/
  - test_harness.py
- DATABASE_SETUP_GUIDE.md
- requirements.txt
- README.md

Note: In this workspace, these folders already exist at the repository root.

## Tech Stack

- Python
- SQL Server (SSMS)
- SQLAlchemy + pyodbc
- OpenRouter API
- sqlglot
- pandas

## Quick Start

1. Create and activate a virtual environment.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```powershell
pip install -r requirements.txt
```

3. Configure environment variables.

Create `.env` in the project root and set:

- `OPENROUTER_API_KEY`
- `DB_URI`
- Optional observability via LangSmith:
  - `LANGSMITH_TRACING=true`
  - `LANGSMITH_API_KEY=<your_langsmith_api_key>`
  - Optional: `LANGSMITH_PROJECT=agent2`
  - Optional: `LANGSMITH_ENDPOINT=https://api.smith.langchain.com`
- Optional: `OPENROUTER_MODEL` for a single preferred model.
- Optional: `OPENROUTER_MODELS` as a comma-separated fallback model list.

4. Create database/table and verify your `DB_URI`.

See `DATABASE_SETUP_GUIDE.md` for the exact SQL scripts and connection examples.

## SQL Server Connection Notes

Use an ODBC connection string in `DB_URI`, for example:

```text
mssql+pyodbc://username:password@localhost/YourDatabase?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes
```

If using Windows Auth, use an appropriate trusted connection format and matching installed ODBC driver.

For LocalDB/named-instance examples, use `DATABASE_SETUP_GUIDE.md`.

## Run Test Harness

```powershell
.\.venv\Scripts\python.exe tests\test_harness.py
```

At startup, harness precheck prints:

- `DB=Connected ...` (or failure reason)
- `OpenRouter=Configured ...` (or missing key)
- `LangSmith=Enabled ...` (or disabled / missing key)

The harness runs Agent 1-like inputs and edge cases:

- Total revenue by region
- Top 5 products
- Customer spending
- Empty results
- Null values
- Malformed SQL
- Unsafe SQL
- Large dataset (TOP enforcement)
- Full Orders table dump

If LLM summarization fails for any reason, Agent 2 returns a deterministic summary from the query result data.

## Programmatic Usage

```python
from agents.agent import Agent2

agent = Agent2()
result = agent.run(
    sql="SELECT region, SUM(price * quantity) AS revenue FROM Orders GROUP BY region",
    question="What is total revenue by region?"
)
print(result)
```

Return format:

```json
{
  "data": [{"region": "West", "revenue": 1000.0}],
  "summary": "Direct answer: ...",
  "row_count": 1
}
```

## Validation Rules

- Allowed: single-statement read-only `SELECT` / `WITH ... SELECT`
- Rejected: `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`, `CREATE`, `MERGE`, `EXEC/EXECUTE`
- Rejected: `SELECT INTO`
- Enforced: `TOP 100` if no `TOP` is present

## Integration with Agent 1

This project is designed for immediate standalone testing and later integration. Agent 1 should provide:

- SQL query string
- User question

Then call:

- `Agent2.run(sql, question)`

## Production Notes

- Keep DB credentials in environment variables only
- Rotate API keys regularly
- Use `OPENROUTER_MODELS` to define approved fallback models per environment
- Enable LangSmith in non-local environments for end-to-end traceability
- Add schema-aware validation allowlists per environment for tighter security
- Add unit/integration tests against a staging SQL Server before production rollout

## LangSmith Monitoring Scope

When `LANGSMITH_TRACING=true`, traces are captured for:

- Agent entrypoint (`Agent2.run`)
- Graph orchestration and each node (`validate`, `execute`, `summarize`)
- SQL validation and SQL execution
- OpenRouter summarization calls and fallback summary path
