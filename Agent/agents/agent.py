from __future__ import annotations

import os
from typing import Any

import pandas as pd

from graph.graph import build_graph
from observability.langsmith import traceable, tracing_scope


class Agent2:
    def __init__(self):
        self.graph = build_graph()

    @traceable(name="agent2.run", run_type="chain")
    def run(self, sql: str, question: str) -> dict[str, Any]:
        if not sql or not sql.strip():
            raise ValueError("sql is required")
        if not question or not question.strip():
            raise ValueError("question is required")

        project_name = (os.getenv("LANGCHAIN_PROJECT") or "agent2").strip() or "agent2"

        with tracing_scope(
            project_name=project_name,
            tags=["agent2", "pipeline"],
            metadata={"question_length": len(question), "sql_length": len(sql)},
        ):
            result = self.graph.invoke({
                "sql": sql,
                "question": question,
            })

        dataframe: pd.DataFrame = result.get("dataframe", pd.DataFrame())

        return {
            "data": dataframe.to_dict(orient="records"),
            "summary": result.get("summary", "No summary generated."),
            "row_count": int(len(dataframe)),
        }
