import logging
from typing import TypedDict

import pandas as pd
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

from db.executor import SQLExecutor
from llm.summarizer import summarize
from observability.langsmith import traceable

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


def execute_node(state: State) -> dict:
    """Execute SQL query and return dataframe."""
    return _execute_node_impl(state)


@traceable(name="graph.execute_sql", run_type="tool")
def _execute_node_impl(state: State) -> dict:
    dataframe = _get_executor().run(state["sql"])
    LOGGER.info("Query execution complete. Rows returned: %s", len(dataframe))
    return {"dataframe": dataframe}


def summarize_node(state: State) -> dict:
    """Summarize query results."""
    return _summarize_node_impl(state)


@traceable(name="graph.summarize", run_type="tool")
def _summarize_node_impl(state: State) -> dict:
    summary = summarize(state["dataframe"], state["question"])
    return {"summary": summary}


def build_graph():
    """Build a LangGraph workflow for SQL execution and summarization.
    
    Agent2 assumes SQL queries are already validated and safe (handled by Agent1).
    This graph only handles execution and summarization.
    """
    graph = StateGraph(State)
    
    # Add nodes
    graph.add_node("execute", execute_node)
    graph.add_node("summarize", summarize_node)
    
    # Define flow: execute → summarize → END
    graph.set_entry_point("execute")
    graph.add_edge("execute", "summarize")
    graph.add_edge("summarize", END)
    
    return graph.compile()
