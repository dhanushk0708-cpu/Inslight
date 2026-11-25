import json
import asyncio
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.dataset import Dataset
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.chat_repository import ChatRepository
from app.services.business_guard import BusinessContextGuard, GUARD_REJECTION_MESSAGE, NO_DATASET_MESSAGE
from app.services.rag_service import RAGService
from app.services.sql_service import SQLService, SQL_UNCONFIDENT_MESSAGE
from app.services.ai_service import ai_service
from app.services.dataset_service import DatasetService
from app.utils.helpers import parse_json, clean_sql, error_response
from app.utils.formatters import format_val
from app.core.logging import logger

SQL_PROMPT_TEMPLATE = """You are an expert SQL generator for Business Intelligence.
Generate a DuckDB SQL query to answer the user's business question.

DATABASE SCHEMA:
{schema}

TABLE NAME: {table}
AVAILABLE COLUMNS: {columns}

RULES:
1. ONLY use columns from the list above. Never invent columns.
2. Output strictly a single SELECT statement.
3. For monthly grouping, use: strftime(order_date, '%Y-%m') AS month (or date column).
4. For yearly grouping, use: strftime(order_date, '%Y') AS year.
5. Always alias aggregations (e.g. SUM(revenue) AS total_revenue, AVG(price) AS avg_price, COUNT(*) AS count).
6. Return ONLY the raw SQL query without markdown blocks, commentary, or backticks.

QUESTION: {question}
CONTEXT: {history}"""

CHART_PROMPT_TEMPLATE = """Design a dashboard presentation for this data. Return ONLY valid JSON:
{{
  "main_chart": {{
    "type": "bar" | "line" | "pie" | "area",
    "title": "Clear descriptive title",
    "x_axis": "Exact column name from DATA COLUMNS",
    "y_axis": "Exact numeric column name from DATA COLUMNS"
  }},
  "secondary_chart": {{
    "type": "pie" | "bar",
    "title": "Breakdown title",
    "x_axis": "Exact column name",
    "y_axis": "Exact column name"
  }} or null,
  "kpi_cards": [
    {{"label": "Metric Name", "value_column": "Exact column", "aggregation": "sum"|"avg"|"max"|"count", "format": "currency"|"number"|"percent"}}
  ]
}}

DATA COLUMNS: {columns}
SAMPLE DATA: {sample}
TOTAL ROWS: {rows}
QUESTION: {question}"""

STORY_PROMPT_TEMPLATE = """Write a 2-3 sentence executive summary of the business data.
Highlight numbers, totals, or trends directly. Never start with "the data shows". End with an actionable insight.
Express all monetary and financial values strictly in Indian Rupees (₹, Lakhs, Crores, or INR). Never use US dollars ($).

DATA SUMMARY: {summary}
QUESTION: {question}"""

SUGGEST_PROMPT_TEMPLATE = """Suggest 3 follow-up business analysis questions based on this dataset.
Return ONLY a JSON array of strings, e.g. ["Question 1", "Question 2", "Question 3"].

DATASET SCHEMA: {schema}
PREVIOUS QUESTION: {question}"""


class QueryService:
    @classmethod
    async def process_user_query(
        cls,
        db: Session,
        user: User,
        question: str,
        dataset_id: Optional[str] = None,
        session_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        End-to-End Orchestrated Query Pipeline:
        1. Resolve Dataset with Ownership Check
        2. Business Context Guard (5 layers)
        3. RAG Schema Extraction
        4. SQL Generation via LLM
        5. AST Validation with SQLGlot
        6. Execution on Isolated DuckDB
        7. Parallel Dashboard Synthesis (Charts, Story, Follow-ups)
        8. Chat History Persistence
        """
        conversation_history = conversation_history or []

        # 1. Resolve Dataset
        dataset = None
        if dataset_id:
            dataset = DatasetRepository.get_by_id(db, dataset_id, user_id=user.id)
            if not dataset:
                return error_response(f"Dataset '{dataset_id}' not found or access denied.")
        else:
            dataset = DatasetRepository.get_latest_for_user(db, user_id=user.id)

        has_dataset = dataset is not None

        # 2. Business Context Guard
        is_valid, rejection = await BusinessContextGuard.validate_query(question, has_dataset=has_dataset)
        if not is_valid:
            return error_response(rejection)

        if not dataset:
            return error_response(NO_DATASET_MESSAGE)

        # 3. RAG Schema Extraction
        rag_context = RAGService.build_dataset_context(dataset)
        columns = rag_context["columns"]
        table_name = dataset.table_name

        # History string
        hist_str = "\n".join(f"{m.get('role', 'user')}: {m.get('content', '')}" for m in conversation_history[-4:]) or "None"

        # 4. Generate SQL
        sql_prompt = SQL_PROMPT_TEMPLATE.format(
            schema=rag_context["formatted_schema"],
            table=table_name,
            columns=json.dumps(columns),
            question=question,
            history=hist_str
        )
        try:
            sql_raw = await ai_service.chat("You generate SQL for Business Intelligence.", sql_prompt, temp=0.0)
            sql = clean_sql(sql_raw)
        except Exception as e:
            logger.error(f"LLM SQL Generation failed: {e}")
            return error_response(SQL_UNCONFIDENT_MESSAGE)

        # 5. AST Validation with SQLGlot
        is_sql_valid, val_result = SQLService.validate_sql(sql, allowed_table=table_name, allowed_columns=columns)
        if not is_sql_valid:
            logger.warning(f"SQL rejected by SQLGlot: {val_result} for SQL: {sql}")
            return error_response(SQL_UNCONFIDENT_MESSAGE, suggestion=f"Available metrics: {', '.join(columns[:8])}")

        final_sql = val_result

        # 6. Execution on Isolated DuckDB
        try:
            conn = DatasetService.get_duckdb_connection(dataset.storage_path, read_only=True)
            results, result_columns = SQLService.execute_duckdb(conn, final_sql)
            conn.close()
        except Exception as e:
            logger.error(f"DuckDB execution error: {e}")
            return error_response(SQL_UNCONFIDENT_MESSAGE)

        if not results:
            return error_response("No records found matching your business query.", suggestion="Try broadening your filters or criteria.")

        # 7. Parallel Dashboard Synthesis
        sample_str = json.dumps(results[:3], default=str)
        summary_str = f"Question: {question}\nReturned {len(results)} rows.\nColumns: {result_columns}\nSample: {sample_str}"

        chart_task = ai_service.chat(
            "You are a BI dashboard designer.",
            CHART_PROMPT_TEMPLATE.format(columns=json.dumps(result_columns), sample=sample_str, rows=len(results), question=question),
            temp=0.1
        )
        story_task = ai_service.chat(
            "You are an executive business writer.",
            STORY_PROMPT_TEMPLATE.format(summary=summary_str, question=question),
            temp=0.2
        )
        suggest_task = ai_service.chat(
            "Suggest business follow-up questions.",
            SUGGEST_PROMPT_TEMPLATE.format(schema=rag_context["formatted_schema"], question=question),
            temp=0.4
        )

        chart_raw, narrative_raw, suggest_raw = await asyncio.gather(
            chart_task, story_task, suggest_task, return_exceptions=True
        )

        # Parse Chart Config
        try:
            dash_cfg = parse_json(chart_raw) if not isinstance(chart_raw, Exception) else {}
        except Exception:
            dash_cfg = {}

        # Parse Narrative
        narrative = narrative_raw if not isinstance(narrative_raw, Exception) else f"Found {len(results)} records."

        # Parse Suggestions
        try:
            followups = parse_json(suggest_raw)[:3] if not isinstance(suggest_raw, Exception) else []
        except Exception:
            followups = ["Show revenue by category", "Monthly trend over time"]

        # Build KPI Cards
        import pandas as pd
        df_res = pd.DataFrame(results)
        kpi_cards = []
        for kpi in dash_cfg.get("kpi_cards", []):
            col = kpi.get("value_column", "")
            if col in df_res.columns and df_res[col].notna().any():
                try:
                    val = float(df_res[col].sum())
                    kpi_cards.append({
                        "label": kpi.get("label", col.replace("_", " ").title()),
                        "value": format_val(val, kpi.get("format", "number")),
                        "trend": None,
                        "trend_direction": "neutral"
                    })
                except Exception:
                    pass

        if not kpi_cards:
            for c in df_res.select_dtypes(include=["number"]).columns[:3]:
                val = float(df_res[c].sum())
                is_money = any(k in c.lower() for k in ["revenue", "price", "cost", "amount", "profit"])
                kpi_cards.append({
                    "label": c.replace("_", " ").title(),
                    "value": format_val(val, "currency" if is_money else "number"),
                    "trend": None,
                    "trend_direction": "neutral"
                })

        # Build Chart configurations
        mc = dash_cfg.get("main_chart", {})
        x_ax = mc.get("x_axis", result_columns[0])
        y_ax = mc.get("y_axis", result_columns[-1] if len(result_columns) > 1 else result_columns[0])
        if x_ax not in result_columns:
            x_ax = result_columns[0]
        if y_ax not in result_columns:
            y_ax = result_columns[-1] if len(result_columns) > 1 else result_columns[0]

        chart_type = mc.get("type", "bar")
        if any(w in x_ax.lower() for w in ["month", "date", "year"]):
            chart_type = "line"

        main_chart = {
            "type": chart_type,
            "title": mc.get("title", question),
            "x_axis": x_ax,
            "y_axis": y_ax,
            "data": results,
            "series": mc.get("series"),
            "highlight": mc.get("highlight")
        }

        secondary_chart = None
        sc = dash_cfg.get("secondary_chart")
        if sc and isinstance(sc, dict):
            secondary_chart = {
                "type": sc.get("type", "pie"),
                "title": sc.get("title", "Breakdown"),
                "x_axis": sc.get("x_axis", x_ax),
                "y_axis": sc.get("y_axis", y_ax),
                "data": results
            }

        response_payload = {
            "kpi_cards": kpi_cards,
            "main_chart": main_chart,
            "secondary_chart": secondary_chart,
            "narrative": narrative,
            "suggested_followups": followups,
            "sql_query": final_sql,
            "error": None,
            "available_columns": columns,
            "data_quality": None,
            "session_id": session_id
        }

        # 8. Save Chat Message if session exists and belongs to authenticated user
        if session_id:
            try:
                session = ChatRepository.get_session(db, session_id=session_id, user_id=user.id)
                if session:
                    ChatRepository.add_message(db, session_id=session_id, role="user", content=question)
                    ChatRepository.add_message(
                        db,
                        session_id=session_id,
                        role="assistant",
                        content=narrative,
                        metadata_json=json.dumps(response_payload)
                    )
                else:
                    logger.warning(f"Unauthorized chat session access attempt: session_id {session_id} does not belong to user {user.id}")
            except Exception as e:
                logger.warning(f"Failed to persist chat message: {e}")

        return response_payload
