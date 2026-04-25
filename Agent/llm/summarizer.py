import logging

import pandas as pd

from llm.openrouter_summarizer import OpenRouterSummarizer
from observability.langsmith import traceable


LOGGER = logging.getLogger(__name__)


@traceable(name="llm.deterministic_fallback", run_type="tool")
def _deterministic_fallback(df: pd.DataFrame) -> str:
    if df.empty:
        return "No data returned."

    insights: list[str] = []

    for col in df.select_dtypes(include="number").columns:
        insights.append(
            f"{col}: mean={df[col].mean():.2f}, max={df[col].max()}, min={df[col].min()}"
        )

    for col in df.select_dtypes(include="object").columns:
        top = df[col].value_counts().head(1)
        if not top.empty:
            insights.append(f"{col}: top={top.index[0]} ({top.iloc[0]})")

    return (
        "Direct answer: LLM unavailable.\n"
        f"Key trends: {'; '.join(insights) if insights else 'No strong trends'}\n"
        f"Summary: Based on {len(df)} rows."
    )


@traceable(name="llm.summarize", run_type="llm")
def summarize(df: pd.DataFrame, question: str) -> str:
    try:
        return OpenRouterSummarizer().summarize(question, df)
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("LLM failed; using deterministic fallback: %s", exc)
        return _deterministic_fallback(df)
