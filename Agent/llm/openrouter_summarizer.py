import os
import json
import logging
import requests
import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from observability.langsmith import traceable

load_dotenv()
LOGGER = logging.getLogger(__name__)


# -------------------------------
# RESPONSE SCHEMA
# -------------------------------
class SummarySchema(BaseModel):
    direct_answer: str
    key_trends: list[str] = Field(default_factory=list)  # keeping name for compatibility
    anomalies: list[str] = Field(default_factory=list)
    concise_summary: str


# -------------------------------
# UTIL: CLEAN JSON RESPONSE
# -------------------------------
def _clean_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    return text.strip()


# -------------------------------
# MAIN SUMMARIZER CLASS
# -------------------------------
class OpenRouterSummarizer:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY missing")

        self.url = "https://openrouter.ai/api/v1/chat/completions"

        configured_models = os.getenv("OPENROUTER_MODELS", "").strip()
        if configured_models:
            self.models = [m.strip() for m in configured_models.split(",") if m.strip()]
        else:
            self.models = [
                os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b").strip(),
                "meta-llama/llama-3.1-8b-instruct",
                "mistralai/mistral-7b-instruct",
            ]

        self.models = list(dict.fromkeys([m for m in self.models if m]))

    # -------------------------------
    # CALL LLM
    # -------------------------------
    @traceable(name="llm.openrouter_call", run_type="llm")
    def _call_model(self, model: str, prompt: str) -> str:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        res = requests.post(self.url, headers=headers, json=payload, timeout=30)

        if res.status_code != 200:
            raise RuntimeError(f"HTTP {res.status_code}: {res.text}")

        return res.json()["choices"][0]["message"]["content"]

    # -------------------------------
    # RESUME-FOCUSED PROMPT
    # -------------------------------
    def _build_prompt(self, question: str, df: pd.DataFrame) -> str:
        df = df.fillna("NULL")

        return f"""
You are an expert HR analyst reviewing structured resume data.

Your task is to analyze candidate information and provide hiring insights.

--------------------------------
USER QUESTION:
{question}
--------------------------------

DATASET:
- Total Candidates: {len(df)}
- Fields: {list(df.columns)}

SAMPLE DATA (first 10 rows):
{json.dumps(df.head(10).to_dict(orient="records"), default=str)}

--------------------------------
ANALYSIS INSTRUCTIONS:

1. DIRECT ANSWER:
   - Clearly answer the question using the dataset.
   - Mention candidate names, roles, experience, or skills where relevant.

2. KEY INSIGHTS:
   Focus on recruitment-related insights:
   • Candidates with highest experience
   • Strong technical skill sets
   • Skill distribution (e.g., Python, ML, Web)
   • Role distribution (Engineer, Analyst, etc.)
   • Potentially suitable candidates for roles

3. ANOMALIES / DATA ISSUES:
   Identify:
   • Missing values (NULL fields)
   • Incomplete profiles (missing skills, experience, etc.)
   • Inconsistent or unusual entries

4. SUMMARY:
   - Provide a short hiring-oriented summary (1–2 lines)

--------------------------------
STRICT RULES:
- Use ONLY the provided dataset
- Do NOT assume anything outside the data
- Keep insights relevant to hiring/resume analysis
- Be concise and factual

--------------------------------
OUTPUT FORMAT (STRICT JSON):
{{
  "direct_answer": "...",
  "key_trends": ["..."],
  "anomalies": ["..."],
  "concise_summary": "..."
}}
"""

    # -------------------------------
    # MAIN SUMMARIZE FUNCTION
    # -------------------------------
    @traceable(name="llm.openrouter_summarize", run_type="chain")
    def summarize(self, question: str, df: pd.DataFrame) -> str:
        if df.empty:
            return "No rows returned."

        prompt = self._build_prompt(question, df)

        last_error = None
        content = ""

        for model in self.models:
            try:
                content = self._call_model(model, prompt)
                LOGGER.info("Model used: %s", model)
                break
            except Exception as exc:
                last_error = exc
                LOGGER.warning("Model failed (%s): %s", model, exc)
                continue

        if not content:
            raise RuntimeError(f"All models failed. Last error: {last_error}")

        # -------------------------------
        # PARSE RESPONSE
        # -------------------------------
        try:
            parsed = SummarySchema.model_validate_json(_clean_json(content))

            return (
                f"Direct answer: {parsed.direct_answer}\n"
                f"Key insights: {', '.join(parsed.key_trends) or 'None'}\n"
                f"Anomalies: {', '.join(parsed.anomalies) or 'None'}\n"
                f"Summary: {parsed.concise_summary}"
            )

        except Exception:
            LOGGER.warning("JSON parsing failed, returning raw output")
            return content.strip()