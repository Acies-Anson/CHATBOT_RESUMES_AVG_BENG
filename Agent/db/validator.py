import logging
from typing import Final

import pandas as pd


LOGGER = logging.getLogger(__name__)

# Constants
MAX_ROWS_FOR_SUMMARIZATION: Final[int] = 10000


class ResultValidationError(ValueError):
    """Raised when query results fail validation."""


def validate_dataframe(df: pd.DataFrame) -> None:
    
    
    if df.empty:
        LOGGER.warning("Query returned 0 rows")
    
    if len(df) > MAX_ROWS_FOR_SUMMARIZATION:
        LOGGER.warning(
            "Large dataset returned: %d rows (max recommended: %d)",
            len(df),
            MAX_ROWS_FOR_SUMMARIZATION,
        )
    
    # Check for all-null columns
    null_cols = df.columns[df.isnull().all()].tolist()
    if null_cols:
        LOGGER.warning("Columns with all nulls: %s", null_cols)


def validate_summary(summary: str | None) -> None:
    """Validate that summary was successfully generated.
    
    Args:
        summary: Summary text to validate
    
    Raises:
        ResultValidationError: If summary is empty or None
    """
    if not summary or not summary.strip():
        raise ResultValidationError("Summary generation failed or returned empty result")