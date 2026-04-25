import os
import json
import logging
import requests
import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()
LOGGER = logging.getLogger(__name__)


class SummarySchema(BaseModel):
    direct_answer: str
    key_trends: list[str] = Field(default_factory=list)
    anomalies: list[str] = Field(default_factory=list)
    concise_summary: str


def _clean_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    return text.strip()


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

        # Preserve order while removing duplicates/empties.
        self.models = list(dict.fromkeys([m for m in self.models if m]))

    def _call_model(self, model: str, prompt: str) -> str:
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
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

    def _build_prompt(self, question: str, df: pd.DataFrame) -> str:
        return f"""
You are a senior data analyst.

Question:
{question}

Rows: {len(df)}
Columns: {list(df.columns)}

Sample:
{json.dumps(df.head(10).to_dict(orient="records"), default=str)}

Return STRICT JSON:
{{
  "direct_answer": "...",
  "key_trends": ["..."],
  "anomalies": ["..."],
  "concise_summary": "..."
}}
"""

    def summarize(self, question: str, df: pd.DataFrame) -> str:
        if df.empty:
            return "No rows returned."

        prompt = self._build_prompt(question, df)
        last_error: Exception | None = None
        content = ""

        for model in self.models:
            try:
                content = self._call_model(model, prompt)
                LOGGER.info("OpenRouter model used: %s", model)
                break
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                LOGGER.warning("OpenRouter model failed (%s): %s", model, exc)
                continue

        if not content:
            raise RuntimeError(f"All OpenRouter models failed. Last error: {last_error}")

        try:
            parsed = SummarySchema.model_validate_json(_clean_json(content))

            return (
                f"Direct answer: {parsed.direct_answer}\n"
                f"Key trends: {', '.join(parsed.key_trends) or 'None'}\n"
                f"Anomalies: {', '.join(parsed.anomalies) or 'None'}\n"
                f"Summary: {parsed.concise_summary}"
            )

        except Exception:
            # fallback to raw text if JSON parsing fails
            return content.strip()