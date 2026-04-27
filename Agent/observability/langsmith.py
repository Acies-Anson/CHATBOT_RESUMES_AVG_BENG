from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Callable

try:
    from langsmith import Client, traceable as _traceable
    from langsmith.run_helpers import tracing_context as _tracing_context

    _client = Client()  # IMPORTANT: ensures traces are sent
except Exception:
    _traceable = None
    _tracing_context = None
    _client = None


def _to_bool(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def is_tracing_enabled() -> bool:
    return _to_bool(os.getenv("LANGCHAIN_TRACING_V2"))


def traceable(*args, **kwargs) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    if _traceable is None:
        def _noop(func: Callable[..., Any]) -> Callable[..., Any]:
            return func
        return _noop
    return _traceable(*args, **kwargs)


@contextmanager
def tracing_scope(
    project_name: str | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
):
    if _tracing_context is None or not is_tracing_enabled():
        yield
        return

    with _tracing_context(
        enabled=True,
        project_name=project_name,
        tags=tags or [],
        metadata=metadata or {},
    ):
        yield