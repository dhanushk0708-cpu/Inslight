import re
import json
from typing import Any, Dict


def parse_json(text: str) -> Any:
    """Extract and parse JSON from markdown code blocks or raw strings."""
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        text = m.group(1)
    m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if m:
        text = m.group(1)
    return json.loads(text.strip())


def clean_sql(text: str) -> str:
    """Extract clean SQL string from markdown or commentary."""
    text = re.sub(r"```(?:sql)?\s*", "", text)
    text = re.sub(r"```", "", text)
    text = text.strip().rstrip(";").strip()
    m = re.search(r"(SELECT\s)", text, re.IGNORECASE)
    if m:
        text = text[m.start():]
    return text


def error_response(msg: str, suggestion: str = None, columns: list = None) -> Dict[str, Any]:
    """Build standardized query error response."""
    return {
        "kpi_cards": [],
        "main_chart": {"type": "bar", "title": "", "data": [], "x_axis": "", "y_axis": ""},
        "secondary_chart": None,
        "narrative": "",
        "suggested_followups": [],
        "sql_query": None,
        "error": msg,
        "suggestion": suggestion,
        "available_columns": columns,
        "data_quality": None,
    }
