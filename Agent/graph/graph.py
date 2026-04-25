import logging
from typing import TypedDict

import pandas as pd
from dotenv import load_dotenv

from db.executor import SQLExecutor
from db.validator import validate_sql
from llm.summarizer import summarize

load_dotenv()


LOGGER = logging.getLogger(__name__)


_EXECUTOR: SQLExecutor | None = None


def _get_executor() -> SQLExecutor:
    global _EXECUTOR
    if _EXECUTOR is None:
        _EXECUTOR = SQLExecutor()
    return _EXECUTOR


class State(TypedDict):
    sql: str
    question: str
    dataframe: pd.DataFrame
    summary: str


class _Pipeline:
    def invoke(self, state):
        current_state = dict(state)
        current_state.update(validate_node(current_state))
        current_state.update(execute_node(current_state))
        current_state.update(summarize_node(current_state))
        return current_state


def validate_node(state):
    validated_sql = validate_sql(state["sql"])
    return {"sql": validated_sql}


def execute_node(state):
    dataframe = _get_executor().run(state["sql"])
    LOGGER.info("Query execution complete. Rows returned: %s", len(dataframe))
    return {"dataframe": dataframe}


def summarize_node(state):
    summary = summarize(state["dataframe"], state["question"])
    return {"summary": summary}


def build_graph():
    return _Pipeline()
