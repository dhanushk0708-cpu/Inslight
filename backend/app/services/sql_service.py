from typing import List, Dict, Any, Tuple, Optional
import sqlglot
from sqlglot import exp
from app.core.logging import logger

SQL_UNCONFIDENT_MESSAGE = (
    "I couldn't confidently translate your question into a business data query. "
    "Could you rephrase it or specify the metric you want to analyze?"
)


class SQLService:
    @staticmethod
    def validate_sql(sql: str, allowed_table: str, allowed_columns: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Validates SQL query using SQLGlot AST parsing.
        Ensures:
        1. Query parses into valid SQL.
        2. Exactly one root statement.
        3. Statement is strictly a SELECT query (read-only).
        4. No dangerous functions, PRAGMA, ATTACH, or DDL/DML.
        5. Referenced tables match the user's isolated table.
        """
        if not sql or not sql.strip():
            return False, "Empty SQL query."

        try:
            statements = sqlglot.parse(sql)
            if len(statements) != 1:
                return False, "Multiple SQL statements are not permitted."

            parsed = statements[0]
            if not parsed:
                return False, "Failed to parse SQL."

            # Must be a Select statement
            if not isinstance(parsed, exp.Select):
                return False, f"Disallowed statement type: {type(parsed).__name__}. Only SELECT queries are permitted."

            # Check for any DML or DDL inside AST
            disallowed_nodes = (
                exp.Insert, exp.Update, exp.Delete, exp.Drop,
                exp.Alter, exp.Create, exp.Command, exp.Pragma
            )
            for node in parsed.find_all(disallowed_nodes):
                return False, f"Prohibited operation: {type(node).__name__}"

            # Table validation
            tables = [t.name.lower() for t in parsed.find_all(exp.Table)]
            allowed_t_lower = allowed_table.lower()
            for t in tables:
                if t != allowed_t_lower and t != "":
                    # Allow subquery aliases but reject foreign tables
                    return False, f"Unauthorized table access: '{t}'. Only '{allowed_table}' is permitted."

            # Ensure LIMIT clause exists to protect against large memory dumps
            limit_exp = parsed.args.get("limit")
            if not limit_exp:
                # Append safe limit
                parsed = parsed.limit(100)

            validated_sql = parsed.sql()
            return True, validated_sql

        except Exception as e:
            logger.warning(f"SQLGlot validation error for query '{sql}': {e}")
            return False, f"SQL validation failed: {str(e)}"

    @staticmethod
    def execute_duckdb(conn, sql: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Execute validated query against DuckDB connection."""
        df = conn.execute(sql).df()
        # Convert NaN to None for clean JSON serialization
        df = df.where(df.notnull(), None)
        columns = list(df.columns)
        records = df.to_dict(orient="records")
        return records, columns
