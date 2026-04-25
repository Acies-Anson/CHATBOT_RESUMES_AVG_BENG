import re
from typing import Final

import sqlglot
from observability.langsmith import traceable


class SQLValidationError(ValueError):
    """Raised when incoming SQL fails safety or syntax checks."""


FORBIDDEN_KEYWORDS: Final[tuple[str, ...]] = (
    "drop",
    "delete",
    "update",
    "insert",
    "alter",
    "truncate",
    "create",
    "merge",
    "exec",
    "execute",
)


def _strip_comments(sql: str) -> str:
    # Remove both single-line and block comments before keyword checks.
    without_block = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    return re.sub(r"--.*?$", " ", without_block, flags=re.MULTILINE)


def _find_outer_select_position(sql: str) -> int:
    lowered = sql.lower()
    depth = 0
    in_single = False
    in_double = False

    i = 0
    while i < len(sql):
        char = sql[i]

        if char == "'" and not in_double:
            in_single = not in_single
            i += 1
            continue

        if char == '"' and not in_single:
            in_double = not in_double
            i += 1
            continue

        if in_single or in_double:
            i += 1
            continue

        if char == "(":
            depth += 1
            i += 1
            continue

        if char == ")" and depth > 0:
            depth -= 1
            i += 1
            continue

        if depth == 0 and lowered.startswith("select", i):
            before_ok = i == 0 or not lowered[i - 1].isalnum()
            after_idx = i + len("select")
            after_ok = after_idx >= len(lowered) or not lowered[after_idx].isalnum()
            if before_ok and after_ok:
                return i

        i += 1

    return -1


def _enforce_top_limit(sql: str, limit: int) -> str:
    if re.search(r"\btop\s*(\(|\d)", sql, flags=re.IGNORECASE):
        return sql

    select_idx = _find_outer_select_position(sql)
    if select_idx < 0:
        raise SQLValidationError("Could not locate top-level SELECT statement.")

    insert_idx = select_idx + len("SELECT")
    tail = sql[insert_idx:]
    distinct_match = re.match(r"(\s+DISTINCT\b)", tail, flags=re.IGNORECASE)
    if distinct_match:
        insert_idx += len(distinct_match.group(1))

    return f"{sql[:insert_idx]} TOP {limit}{sql[insert_idx:]}"


@traceable(name="db.validate_sql", run_type="tool")
def validate_sql(query: str, default_top_limit: int = 100) -> str:
    if not query or not query.strip():
        raise SQLValidationError("SQL query cannot be empty.")

    stripped_query = query.strip().rstrip(";")
    stripped_no_comments = _strip_comments(stripped_query)

    if re.search(r"\b(" + "|".join(FORBIDDEN_KEYWORDS) + r")\b", stripped_no_comments, flags=re.IGNORECASE):
        raise SQLValidationError("Only read-only SELECT queries are allowed.")

    parsed_statements = sqlglot.parse(stripped_query, read="tsql")
    if len(parsed_statements) != 1:
        raise SQLValidationError("Only a single SQL statement is allowed.")

    first_token = stripped_no_comments.lstrip().split(maxsplit=1)[0].lower() if stripped_no_comments.strip() else ""
    if first_token not in {"select", "with"}:
        raise SQLValidationError("Only SELECT queries are allowed.")

    if re.search(r"\binto\b", stripped_no_comments, flags=re.IGNORECASE):
        raise SQLValidationError("SELECT INTO is not allowed.")

    sql_with_limit = _enforce_top_limit(stripped_query, default_top_limit)

    # Final parse pass ensures generated SQL remains valid T-SQL.
    sqlglot.parse_one(sql_with_limit, read="tsql")
    return sql_with_limit
