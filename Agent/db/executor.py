import os
import time
import logging

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from observability.langsmith import traceable

load_dotenv()


LOGGER = logging.getLogger(__name__)


class SQLExecutor:
    def __init__(self, db_uri: str | None = None, retries: int = 3, retry_delay_seconds: float = 1.5):
        resolved_db_uri = db_uri or os.getenv("DB_URI")
        if not resolved_db_uri:
            raise ValueError("DB_URI is required. Set it in environment variables or pass db_uri.")

        self.engine: Engine = create_engine(
            resolved_db_uri,
            pool_pre_ping=True,
            pool_recycle=1800,
            future=True,
        )
        self.retries = max(1, retries)
        self.retry_delay_seconds = max(0.0, retry_delay_seconds)

    @traceable(name="db.execute_sql", run_type="tool")
    def run(self, query: str) -> pd.DataFrame:
        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        last_error: Exception | None = None
        for attempt in range(1, self.retries + 1):
            try:
                with self.engine.connect() as connection:
                    frame = pd.read_sql_query(text(query), con=connection)
                return frame
            except SQLAlchemyError as exc:
                last_error = exc
                LOGGER.warning(
                    "SQL execution failed on attempt %s/%s: %s",
                    attempt,
                    self.retries,
                    exc,
                )
                if attempt < self.retries:
                    time.sleep(self.retry_delay_seconds)

        raise RuntimeError(f"Failed to execute query after {self.retries} attempts.") from last_error
