from __future__ import annotations

from typing import Any

import pandas as pd

from graph.graph import build_graph


class Agent2:
    def __init__(self):
        self.graph = build_graph()

    def run(self, sql: str, question: str) -> dict[str, Any]:
        if not sql or not sql.strip():
            raise ValueError("sql is required")
        if not question or not question.strip():
            raise ValueError("question is required")

        result = self.graph.invoke({
            "sql": sql,
            "question": question
        })

        dataframe: pd.DataFrame = result.get("dataframe", pd.DataFrame())

        return {
            "data": dataframe.to_dict(orient="records"),
            "summary": result.get("summary", "No summary generated."),
            "row_count": int(len(dataframe)),
        }
