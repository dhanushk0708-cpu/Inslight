"""
DASH.AI Backend - Complete AI BI Co-Pilot
Fixed: Smart column handling, SQL aliases, fallback queries
"""

import os
import io
import re
import json
import sqlite3
import requests
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


class QueryRequest(BaseModel):
    question: str
    conversation_history: Optional[List[Dict[str, str]]] = []


class WhatIfRequest(BaseModel):
    price_change: float = 0.0
    cost_change: float = 0.0
    units_change: float = 0.0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATABASE MANAGER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.table_name = "sales_data"
        self.schema_info = ""
        self.df: Optional[pd.DataFrame] = None
        self.column_aliases: Dict[str, str] = {}

    def load_default(self):
        paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sample_sales.csv"),
            os.path.join(os.getcwd(), "data", "sample_sales.csv"),
            "data/sample_sales.csv",
            "backend/data/sample_sales.csv",
        ]
        for p in paths:
            if os.path.exists(p):
                print(f"[OK] CSV: {p}")
                self.load_csv(p)
                return
        print(f"[WARN] CSV not found")

    def load_csv(self, filepath: str, table_name: str = "sales_data"):
        self.table_name = table_name
        self.df = pd.read_csv(filepath)
        self._process()

    def load_bytes(self, file_bytes: bytes, filename: str):
        self.table_name = filename.replace(".csv", "").replace(" ", "_").lower()
        self.df = pd.read_csv(io.BytesIO(file_bytes))
        self._process()

    def _process(self):
        self.df.columns = [c.strip().lower().replace(" ", "_") for c in self.df.columns]
        for col in self.df.columns:
            if "date" in col.lower():
                try:
                    self.df[col] = pd.to_datetime(self.df[col]).dt.strftime("%Y-%m-%d")
                except Exception:
                    pass
        self.df.to_sql(self.table_name, self.conn, if_exists="replace", index=False)
        self.schema_info = self._schema()
        self._build_aliases()
        print(f"[OK] {len(self.df)} rows → '{self.table_name}'")

    def _build_aliases(self):
        if self.df is None:
            return
        self.column_aliases = {}
        amap = {
            "sales": ["revenue", "total_sales", "amount"],
            "total_sales": ["revenue"],
            "revenue": ["sales", "amount", "total_revenue"],
            "profit": ["net_profit", "margin", "earnings"],
            "cost": ["expense", "total_cost", "cogs"],
            "quantity": ["units_sold", "qty", "units"],
            "units": ["units_sold", "quantity"],
            "price": ["unit_price", "selling_price"],
            "product": ["product_name", "product_category"],
            "category": ["product_category"],
            "region": ["area", "territory"],
            "name": ["product_name", "salesperson"],
        }
        actual = list(self.df.columns)
        for kw, possibles in amap.items():
            if kw not in actual:
                for p in possibles:
                    if p in actual:
                        self.column_aliases[kw] = p
                        break
        for c in actual:
            self.column_aliases[c] = c

    def _schema(self) -> str:
        cursor = self.conn.execute(f"PRAGMA table_info({self.table_name})")
        cols = cursor.fetchall()
        lines = [f"Table: {self.table_name}", f"ALL AVAILABLE COLUMNS (use ONLY these):"]
        for col in cols:
            try:
                samples = self.conn.execute(f"SELECT DISTINCT [{col[1]}] FROM {self.table_name} LIMIT 8").fetchall()
                s = ", ".join(str(r[0]) for r in samples)
            except Exception:
                s = "N/A"
            lines.append(f"  - {col[1]} ({col[2]}) → examples: {s}")
        cnt = self.conn.execute(f"SELECT COUNT(*) FROM {self.table_name}").fetchone()[0]
        lines.append(f"\nTotal rows: {cnt}")
        return "\n".join(lines)

    def execute(self, sql: str) -> Tuple[List[Dict], List[str]]:
        cursor = self.conn.execute(sql)
        columns = [d[0] for d in cursor.description]
        rows = cursor.fetchall()
        results = []
        for row in rows:
            d = {}
            for i, col in enumerate(columns):
                val = row[i]
                # Clean column names: remove SQL function wrappers
                clean_col = col
                # SUM(revenue) → total_revenue, etc
                func_match = re.match(r'(SUM|AVG|COUNT|MAX|MIN)\((\w+)\)', col, re.IGNORECASE)
                if func_match:
                    func_name = func_match.group(1).lower()
                    col_name = func_match.group(2)
                    clean_col = f"{func_name}_{col_name}" if func_name != "sum" else f"total_{col_name}"
                d[clean_col] = val
            results.append(d)

        clean_columns = list(results[0].keys()) if results else columns
        return results, clean_columns


db = DatabaseManager()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LLM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class LLM:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.3-70b-versatile"
        if self.api_key:
            print("[OK] Groq key loaded")

    def chat(self, system: str, user: str, temp: float = 0.1) -> str:
        if not self.api_key:
            raise Exception("GROQ_API_KEY not set")
        r = requests.post(self.url, headers={
            "Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"
        }, json={
            "model": self.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": temp, "max_tokens": 4096,
        }, timeout=30)
        if r.status_code != 200:
            raise Exception(f"Groq error {r.status_code}: {r.text[:200]}")
        return r.json()["choices"][0]["message"]["content"].strip()


llm = LLM()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PROMPTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SQL_PROMPT = """You are a SQLite SQL query generator.

DATABASE SCHEMA:
{schema}

TABLE NAME: {table}

CRITICAL RULES:
1. ONLY use column names that exist in the schema above
2. The table has these EXACT columns: {columns}
3. There is NO column called "sales" - use "revenue" instead
4. There is NO column called "quantity" - use "units_sold" instead
5. There is NO column called "category" - use "product_category" instead
6. There is NO column called "product" alone - use "product_name" or "product_category"
7. ALWAYS use aliases for aggregated columns: SUM(revenue) AS total_revenue
8. For monthly data use: strftime('%Y-%m', date) AS month
9. For yearly data use: strftime('%Y', date) AS year
10. ALWAYS include ORDER BY
11. LIMIT 50
12. Return ONLY the SQL query - no markdown, no backticks, no explanation

COMMON QUERY PATTERNS:
- "total sales" or "total revenue" → SELECT region, SUM(revenue) AS total_revenue FROM {table} GROUP BY region ORDER BY total_revenue DESC
- "this year sales" → SELECT strftime('%Y-%m', date) AS month, SUM(revenue) AS total_revenue FROM {table} WHERE strftime('%Y', date) = '2024' GROUP BY month ORDER BY month
- "monthly trend" → SELECT strftime('%Y-%m', date) AS month, SUM(revenue) AS total_revenue, SUM(profit) AS total_profit FROM {table} GROUP BY month ORDER BY month
- "by product" → SELECT product_name, SUM(revenue) AS total_revenue FROM {table} GROUP BY product_name ORDER BY total_revenue DESC
- "by category" → SELECT product_category, SUM(revenue) AS total_revenue FROM {table} GROUP BY product_category ORDER BY total_revenue DESC
- "top products" → SELECT product_name, SUM(profit) AS total_profit FROM {table} GROUP BY product_name ORDER BY total_profit DESC LIMIT 10

USER QUESTION: {question}
CONTEXT: {history}"""

SQL_FIX_PROMPT = """Fix this SQL query. The error was: {error}

TABLE: {table}
AVAILABLE COLUMNS: {columns}

FAILED SQL: {failed_sql}

RULES:
- Only use columns from the list above
- Use proper aliases: SUM(col) AS total_col
- Return ONLY the fixed SQL, nothing else"""

CHART_PROMPT = """Design a dashboard for this data. Return JSON:
{{
  "main_chart": {{
    "type": "bar"|"line"|"pie"|"area",
    "title": "title",
    "x_axis": "EXACT column name from data",
    "y_axis": "EXACT column name from data",
    "series": null
  }},
  "secondary_chart": {{
    "type": "pie"|"bar",
    "title": "title",
    "x_axis": "EXACT column name",
    "y_axis": "EXACT column name"
  }} or null,
  "kpi_cards": [
    {{"label": "Display Name", "value_column": "EXACT column name", "aggregation": "sum", "format": "currency"}}
  ]
}}

CRITICAL: x_axis, y_axis, and value_column MUST be exact column names from DATA COLUMNS below.
DO NOT use original table column names - use the result column names.

DATA COLUMNS: {columns}
SAMPLE DATA: {sample}
ROWS: {rows}
QUESTION: {question}

Return ONLY JSON."""

STORY_PROMPT = """Write 2-3 sentence executive insight about this data.
Include specific numbers ($X.XM, XX%). Mention trends. End with actionable insight.
Never say "the data shows". Max 3 sentences.

DATA: {data_summary}
QUESTION: {question}

Return ONLY the narrative text."""

SUGGEST_PROMPT = """Suggest 3 follow-up questions about this data as JSON array.
Schema columns: {schema}
Previous: {question}
Return ONLY: ["q1", "q2", "q3"]"""

PROFILE_PROMPT = """Generate 3 CXO business questions for this dataset as JSON array.
DATASET: {info}
Return ONLY: ["q1", "q2", "q3"]"""

DEEP_DIVE_PROMPT = """Analyze this P&L data. Return JSON:
{{
  "top_profit_drivers": [{{"name": "x", "profit": 123, "margin_pct": 25, "trend": "up"}}],
  "loss_risk_areas": [{{"name": "x", "issue": "desc", "loss_amount": 123, "severity": "high"}}],
  "root_cause_analysis": "2-3 sentences with specific numbers",
  "recommendations": [{{"action": "do this", "expected_impact": "$X increase", "priority": "high"}}]
}}
DATA: {data_summary}
Return ONLY JSON."""

WHATIF_PROMPT = """Analyze this scenario in 2-3 sentences with numbers:
Current: Revenue=${current_revenue:,.0f}, Cost=${current_cost:,.0f}, Profit=${current_profit:,.0f}
Changes: Price {price_change:+}%, Cost {cost_change:+}%, Units {units_change:+}%
Projected: Profit=${new_profit:,.0f} (change: ${profit_diff:,.0f}, {profit_pct_change:+.1f}%)
Return ONLY text."""

ANOMALY_PROMPT = """Analyze anomalies. Return JSON array:
[{{"metric":"what","description":"plain English","severity":"high|medium|low","suggestion":"action"}}]
DATA: {data_summary}
ANOMALIES: {anomalies}
Max 5. Return ONLY JSON array."""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def parse_json(text: str):
    m = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if m: text = m.group(1)
    m = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', text)
    if m: text = m.group(1)
    return json.loads(text)


def clean_sql(text: str) -> str:
    text = re.sub(r'```(?:sql)?\s*', '', text)
    text = re.sub(r'```', '', text)
    text = text.strip().rstrip(";").strip()
    m = re.search(r'(SELECT\s)', text, re.IGNORECASE)
    if m: text = text[m.start():]
    return text


def format_val(val: float, fmt: str = "number") -> str:
    if fmt == "currency":
        if abs(val) >= 1e6: return f"${val/1e6:,.1f}M"
        if abs(val) >= 1e3: return f"${val/1e3:,.1f}K"
        return f"${val:,.0f}"
    if fmt == "percent": return f"{val:.1f}%"
    if abs(val) >= 1e6: return f"{val/1e6:,.1f}M"
    if abs(val) >= 1e3: return f"{val/1e3:,.1f}K"
    return f"{val:,.0f}"


def error_response(msg, suggestion=None, columns=None):
    return {
        "kpi_cards": [], "main_chart": {"type":"bar","title":"","data":[],"x_axis":"","y_axis":""},
        "secondary_chart": None, "narrative": "", "suggested_followups": [],
        "sql_query": None, "error": msg, "suggestion": suggestion,
        "available_columns": columns, "data_quality": None,
    }


def build_fallback_query(question: str) -> Optional[str]:
    """Build a smart fallback SQL based on keywords in the question"""
    q = question.lower()
    t = db.table_name

    if any(w in q for w in ["this year", "yearly", "year sales", "annual"]):
        return f"SELECT strftime('%Y-%m', date) AS month, SUM(revenue) AS total_revenue, SUM(profit) AS total_profit, SUM(units_sold) AS total_units FROM {t} WHERE strftime('%Y', date) = '2024' GROUP BY month ORDER BY month"

    if any(w in q for w in ["monthly", "month", "trend", "over time"]):
        return f"SELECT strftime('%Y-%m', date) AS month, SUM(revenue) AS total_revenue, SUM(profit) AS total_profit FROM {t} GROUP BY month ORDER BY month"

    if any(w in q for w in ["region", "by region", "regional"]):
        return f"SELECT region, SUM(revenue) AS total_revenue, SUM(profit) AS total_profit, SUM(units_sold) AS total_units FROM {t} GROUP BY region ORDER BY total_revenue DESC"

    if any(w in q for w in ["category", "categories", "by category"]):
        return f"SELECT product_category, SUM(revenue) AS total_revenue, SUM(profit) AS total_profit FROM {t} GROUP BY product_category ORDER BY total_revenue DESC"

    if any(w in q for w in ["product", "top product", "best product", "by product"]):
        return f"SELECT product_name, SUM(revenue) AS total_revenue, SUM(profit) AS total_profit, SUM(units_sold) AS total_units FROM {t} GROUP BY product_name ORDER BY total_revenue DESC LIMIT 10"

    if any(w in q for w in ["total sales", "total revenue", "overall", "summary", "sales"]):
        return f"SELECT region, SUM(revenue) AS total_revenue, SUM(profit) AS total_profit, SUM(cost) AS total_cost, SUM(units_sold) AS total_units FROM {t} GROUP BY region ORDER BY total_revenue DESC"

    if any(w in q for w in ["profit", "profitable", "margin"]):
        return f"SELECT product_name, SUM(revenue) AS total_revenue, SUM(profit) AS total_profit, ROUND(SUM(profit)*100.0/SUM(revenue),1) AS margin_pct FROM {t} GROUP BY product_name ORDER BY total_profit DESC LIMIT 10"

    if any(w in q for w in ["salesperson", "sales person", "seller", "who sold"]):
        return f"SELECT salesperson, SUM(revenue) AS total_revenue, SUM(profit) AS total_profit, SUM(units_sold) AS total_units FROM {t} GROUP BY salesperson ORDER BY total_revenue DESC"

    if any(w in q for w in ["compare", "comparison", "versus", "vs"]):
        return f"SELECT product_category, region, SUM(revenue) AS total_revenue, SUM(profit) AS total_profit FROM {t} GROUP BY product_category, region ORDER BY total_revenue DESC LIMIT 20"

    # Default: show by region
    return f"SELECT region, SUM(revenue) AS total_revenue, SUM(profit) AS total_profit, SUM(cost) AS total_cost FROM {t} GROUP BY region ORDER BY total_revenue DESC"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SMART SQL EXECUTOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def smart_execute(sql: str, question: str, max_retries: int = 3):
    """Execute SQL with automatic retry, fix, and fallback"""

    for attempt in range(max_retries):
        try:
            upper = sql.upper().strip()
            if not upper.startswith("SELECT"):
                sql = build_fallback_query(question) or f"SELECT * FROM {db.table_name} LIMIT 20"

            for danger in ["DROP","DELETE","UPDATE","INSERT","ALTER","TRUNCATE"]:
                if danger in upper:
                    return None, None, sql, f"Blocked: {danger}"

            results, columns = db.execute(sql)

            if results and len(results) > 0:
                # Check if results have valid numeric data
                df_check = pd.DataFrame(results)
                num_cols = df_check.select_dtypes(include=["number"]).columns
                has_valid_numbers = False
                for nc in num_cols:
                    if df_check[nc].notna().any() and df_check[nc].sum() != 0:
                        has_valid_numbers = True
                        break

                if has_valid_numbers:
                    return results, columns, sql, None

                # Has rows but no valid numbers — try fallback
                if attempt < max_retries - 1:
                    sql = build_fallback_query(question) or sql
                    continue

                return results, columns, sql, None

            # No results — try fallback
            if attempt < max_retries - 1:
                fallback = build_fallback_query(question)
                if fallback and fallback != sql:
                    sql = fallback
                    continue

            return [], columns or [], sql, None

        except Exception as e:
            err = str(e)
            print(f"[SQL Attempt {attempt+1}] {err}")

            if attempt < max_retries - 1:
                # Try keyword-based fallback first
                fallback = build_fallback_query(question)
                if fallback:
                    sql = fallback
                    continue

                # Try LLM fix
                try:
                    cols = list(db.df.columns) if db.df is not None else []
                    fix_raw = llm.chat(
                        SQL_FIX_PROMPT.format(schema=db.schema_info, table=db.table_name, columns=json.dumps(cols), failed_sql=sql, error=err),
                        "Fix SQL"
                    )
                    sql = clean_sql(fix_raw)
                except Exception:
                    sql = build_fallback_query(question) or f"SELECT * FROM {db.table_name} LIMIT 20"

    return None, None, sql, "Could not execute query after retries"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN PIPELINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def process_query(question: str, history: list = None) -> dict:
    if not db.schema_info or db.df is None:
        return error_response("No data loaded. Upload a CSV first.")

    history = history or []
    hist_str = "\n".join(f"{m.get('role','user')}: {m.get('content','')}" for m in history[-6:]) or "None"
    cols_list = list(db.df.columns)

    try:
        # Step 1: Generate SQL
        try:
            sql_raw = llm.chat(
                SQL_PROMPT.format(
                    schema=db.schema_info, table=db.table_name,
                    columns=json.dumps(cols_list), question=question, history=hist_str
                ),
                question
            )
            sql = clean_sql(sql_raw)
        except Exception:
            sql = build_fallback_query(question) or f"SELECT * FROM {db.table_name} LIMIT 20"

        print(f"[SQL] {sql}")

        # Step 1.5: Execute with smart retry
        results, columns, final_sql, exec_error = smart_execute(sql, question)

        if exec_error or not results:
            # Last resort fallback
            fallback = build_fallback_query(question)
            if fallback:
                try:
                    results, columns = db.execute(fallback)
                    final_sql = fallback
                except Exception:
                    pass

            if not results:
                return error_response(
                    "Couldn't find matching data. Try a different question.",
                    f"Available columns: {', '.join(cols_list)}",
                    columns=cols_list
                )

        # Step 2: Design Dashboard
        try:
            chart_raw = llm.chat(
                CHART_PROMPT.format(
                    columns=json.dumps(columns), sample=json.dumps(results[:3], default=str),
                    rows=len(results), question=question
                ),
                "Design dashboard."
            )
            dash_cfg = parse_json(chart_raw)
        except Exception:
            # Smart fallback chart config
            x_col = columns[0]
            y_col = None
            for c in columns[1:]:
                if any(isinstance(results[0].get(c), (int, float)) for _ in [1]):
                    try:
                        if results[0].get(c) is not None and isinstance(results[0][c], (int, float)):
                            y_col = c
                            break
                    except Exception:
                        pass
            if not y_col and len(columns) > 1:
                y_col = columns[1]
            elif not y_col:
                y_col = columns[0]

            dash_cfg = {
                "main_chart": {"type": "bar", "title": question, "x_axis": x_col, "y_axis": y_col},
                "secondary_chart": None, "kpi_cards": []
            }

        # Step 3: Narrative
        df = pd.DataFrame(results)
        summary = f"Question: {question}\nRows: {len(results)}, Columns: {columns}\n"
        for col in df.select_dtypes(include=["number"]).columns[:4]:
            if df[col].notna().any():
                summary += f"  {col}: total={df[col].sum():,.0f}, avg={df[col].mean():,.0f}\n"
        summary += f"Sample: {json.dumps(results[:2], default=str)}"

        try:
            narrative = llm.chat(STORY_PROMPT.format(data_summary=summary, question=question), "Insight.", temp=0.3)
        except Exception:
            narrative = f"Query returned {len(results)} records. Review the charts for detailed insights."

        # Step 4: Follow-ups
        try:
            sug = llm.chat(SUGGEST_PROMPT.format(question=question, schema=db.schema_info), "Suggest.", temp=0.5)
            followups = parse_json(sug)[:3]
        except Exception:
            followups = ["Show monthly revenue trends", "Top products by profit", "Compare regions"]

        # Build KPIs
        kpi_cards = []
        for kpi in dash_cfg.get("kpi_cards", []):
            try:
                col = kpi.get("value_column", "")
                if col in df.columns and df[col].notna().any():
                    agg = {"sum": df[col].sum(), "avg": df[col].mean(), "max": df[col].max(), "count": df[col].count()}
                    val = agg.get(kpi.get("aggregation", "sum"), df[col].sum())
                    if pd.notna(val) and val != 0:
                        kpi_cards.append({
                            "label": kpi.get("label", col.replace("_", " ").title()),
                            "value": format_val(float(val), kpi.get("format", "number")),
                            "trend": None, "trend_direction": "neutral"
                        })
            except Exception:
                continue

        # Auto-generate KPIs if none from LLM
        if not kpi_cards:
            for col in df.select_dtypes(include=["number"]).columns[:4]:
                val = df[col].sum()
                if pd.notna(val) and val != 0:
                    is_money = any(k in col.lower() for k in ["revenue","cost","profit","price","amount","total"])
                    kpi_cards.append({
                        "label": col.replace("_", " ").title(),
                        "value": format_val(float(val), "currency" if is_money else "number"),
                        "trend": None, "trend_direction": "neutral"
                    })

        # Validate chart axes
        mc = dash_cfg.get("main_chart", {})
        x_ax = mc.get("x_axis", columns[0])
        y_ax = mc.get("y_axis", columns[-1] if len(columns) > 1 else columns[0])
        if x_ax not in columns: x_ax = columns[0]
        if y_ax not in columns:
            # Find first numeric column
            for c in columns:
                if c != x_ax and results and isinstance(results[0].get(c), (int, float)):
                    y_ax = c
                    break
            else:
                y_ax = columns[-1] if len(columns) > 1 else columns[0]

        main_chart = {
            "type": mc.get("type", "bar"), "title": mc.get("title", question),
            "x_axis": x_ax, "y_axis": y_ax,
            "series": mc.get("series"), "data": results, "highlight": mc.get("highlight")
        }

        secondary_chart = None
        sc = dash_cfg.get("secondary_chart")
        if sc:
            sx = sc.get("x_axis", columns[0])
            sy = sc.get("y_axis", y_ax)
            if sx not in columns: sx = columns[0]
            if sy not in columns: sy = y_ax
            secondary_chart = {"type": sc.get("type","pie"), "title": sc.get("title","Breakdown"), "x_axis": sx, "y_axis": sy, "data": results}

        # Data quality check
        dq = None
        missing = {}
        for c in df.columns:
            n = int(df[c].isnull().sum())
            if n > 0: missing[c] = n
        if missing:
            dq = {"missing_in_query": missing, "total_rows": len(results)}

        return {
            "kpi_cards": kpi_cards, "main_chart": main_chart, "secondary_chart": secondary_chart,
            "narrative": narrative, "suggested_followups": followups, "sql_query": final_sql,
            "error": None, "available_columns": cols_list, "data_quality": dq
        }

    except Exception as e:
        return error_response(f"Error: {str(e)}", f"Try: 'Show revenue by region'", columns=cols_list)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DEEP DIVE / WHAT-IF / ANOMALY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_deep_dive() -> dict:
    if db.df is None: return {"error": "No data"}
    df = db.df.copy()
    parts = []

    if "product_category" in df.columns and "revenue" in df.columns:
        ag = {"revenue":("revenue","sum")}
        if "cost" in df.columns: ag["cost"]=("cost","sum")
        if "profit" in df.columns: ag["profit"]=("profit","sum")
        parts.append(f"By category:\n{df.groupby('product_category').agg(**ag).reset_index().to_string()}")

    if "region" in df.columns and "revenue" in df.columns:
        ag2 = {"revenue":("revenue","sum")}
        if "profit" in df.columns: ag2["profit"]=("profit","sum")
        parts.append(f"\nBy region:\n{df.groupby('region').agg(**ag2).reset_index().to_string()}")

    if "product_name" in df.columns and "profit" in df.columns:
        ag3 = {"revenue":("revenue","sum"),"profit":("profit","sum")}
        if "cost" in df.columns: ag3["cost"]=("cost","sum")
        p = df.groupby("product_name").agg(**ag3).reset_index()
        p["margin_pct"] = (p["profit"]/p["revenue"]*100).round(1)
        parts.append(f"\nBy product:\n{p.to_string()}")

    try:
        result = parse_json(llm.chat(DEEP_DIVE_PROMPT.format(data_summary="\n".join(parts)), "Analyze.", temp=0.2))
    except Exception as e:
        result = {"root_cause_analysis": f"Analysis: {e}", "recommendations": [], "top_profit_drivers": [], "loss_risk_areas": []}

    if "date" in df.columns and "revenue" in df.columns:
        df["_m"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m")
        ag = {"revenue":("revenue","sum")}
        if "cost" in df.columns: ag["cost"]=("cost","sum")
        if "profit" in df.columns: ag["profit"]=("profit","sum")
        result["monthly_pnl"] = df.groupby("_m").agg(**ag).reset_index().rename(columns={"_m":"month"}).to_dict(orient="records")

    if "product_name" in df.columns and "profit" in df.columns:
        pp = df.groupby("product_name").agg(revenue=("revenue","sum"),profit=("profit","sum")).reset_index()
        pp["margin_pct"] = (pp["profit"]/pp["revenue"]*100).round(1)
        result["profit_by_product"] = pp.sort_values("profit",ascending=False).to_dict(orient="records")

    if "region" in df.columns and "profit" in df.columns:
        rp = df.groupby("region").agg(revenue=("revenue","sum"),profit=("profit","sum")).reset_index()
        rp["margin_pct"] = (rp["profit"]/rp["revenue"]*100).round(1)
        result["profit_by_region"] = rp.to_dict(orient="records")

    return result


def run_whatif(price_change, cost_change, units_change):
    if db.df is None: return {"error": "No data"}
    df = db.df
    cr = float(df["revenue"].sum()) if "revenue" in df.columns else 0
    cc = float(df["cost"].sum()) if "cost" in df.columns else 0
    cp = float(df["profit"].sum()) if "profit" in df.columns else cr-cc
    cu = float(df["units_sold"].sum()) if "units_sold" in df.columns else 0
    pm,cm,um = 1+price_change/100, 1+cost_change/100, 1+units_change/100
    nr,nc2 = cr*pm*um, cc*cm*um
    np2 = nr-nc2
    pd2 = np2-cp
    pct = (pd2/cp*100) if cp else 0

    mc = []
    if "date" in df.columns and "revenue" in df.columns:
        df2 = df.copy()
        df2["_m"] = pd.to_datetime(df2["date"]).dt.strftime("%Y-%m")
        ag = {"actual_revenue":("revenue","sum")}
        if "cost" in df.columns: ag["actual_cost"]=("cost","sum")
        if "profit" in df.columns: ag["actual_profit"]=("profit","sum")
        m = df2.groupby("_m").agg(**ag).reset_index()
        for _,r in m.iterrows():
            ar=r.get("actual_revenue",0); ac2=r.get("actual_cost",0); ap=r.get("actual_profit",ar-ac2)
            mc.append({"month":r["_m"],"actual_revenue":round(ar),"projected_revenue":round(ar*pm*um),"actual_profit":round(ap),"projected_profit":round(ar*pm*um-ac2*cm*um)})

    ci = []
    if "product_category" in df.columns and "revenue" in df.columns:
        ag2 = {"revenue":("revenue","sum")}
        if "profit" in df.columns: ag2["profit"]=("profit","sum")
        if "cost" in df.columns: ag2["cost"]=("cost","sum")
        c = df.groupby("product_category").agg(**ag2).reset_index()
        for _,r in c.iterrows():
            p3 = r.get("profit", r["revenue"]-r.get("cost",0))
            np3 = r["revenue"]*pm*um - r.get("cost",0)*cm*um
            ci.append({"category":r["product_category"],"current_profit":round(p3),"projected_profit":round(np3),"change_pct":round((np3-p3)/p3*100,1) if p3 else 0})

    try:
        ai = llm.chat(WHATIF_PROMPT.format(current_revenue=cr,current_cost=cc,current_profit=cp,price_change=price_change,cost_change=cost_change,units_change=units_change,new_revenue=nr,new_cost=nc2,new_profit=np2,profit_diff=pd2,profit_pct_change=pct),"Analyze.",temp=0.3)
    except Exception:
        ai = f"Projected profit change: {format_val(pd2,'currency')} ({pct:+.1f}%)"

    return {"current":{"revenue":round(cr),"cost":round(cc),"profit":round(cp),"units":round(cu)},"projected":{"revenue":round(nr),"cost":round(nc2),"profit":round(np2)},"change":{"profit_diff":round(pd2),"profit_pct_change":round(pct,1)},"monthly_comparison":mc,"category_impact":ci,"ai_commentary":ai}


def detect_anomalies():
    if db.df is None: return {"anomalies":[],"count":0,"ai_analysis":[]}
    df = db.df.copy()
    found = []
    for col in df.select_dtypes(include=["number"]).columns:
        m,s = df[col].mean(), df[col].std()
        if s == 0: continue
        out = df[(df[col]>m+2*s)|(df[col]<m-2*s)]
        if 0 < len(out) < len(df)*0.1:
            for _,r in out.head(2).iterrows():
                ctx = ""
                if "product_name" in df.columns: ctx += f" for {r.get('product_name','')}"
                if "region" in df.columns: ctx += f" in {r.get('region','')}"
                found.append(f"{col} {'high' if r[col]>m else 'low'} ({r[col]:,.0f} vs avg {m:,.0f}){ctx}")

    if "date" in df.columns and "revenue" in df.columns:
        df["_m"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m")
        mo = df.groupby("_m")["revenue"].sum().reset_index()
        mo["pct"] = mo["revenue"].pct_change()*100
        for _,r in mo[mo["pct"]<-20].iterrows():
            found.append(f"Revenue dropped {r['pct']:.1f}% in {r['_m']}")

    if not found: return {"anomalies":[],"count":0,"ai_analysis":[]}

    try:
        sm = f"Rows:{len(df)}\n"+"\n".join(f"{c}:mean={df[c].mean():,.0f}" for c in df.select_dtypes(include=["number"]).columns[:4])
        ai = parse_json(llm.chat(ANOMALY_PROMPT.format(data_summary=sm,anomalies="\n".join(f"- {a}" for a in found[:8])),"Analyze.",temp=0.2))
    except Exception:
        ai = [{"metric":a[:30],"description":a,"severity":"medium","suggestion":"Investigate"} for a in found[:5]]

    return {"anomalies":found[:5],"count":len(found),"ai_analysis":ai[:5]}


def profile_data(df, filename):
    ci,missing = [],{}
    for col in df.columns:
        info = {"name":col,"dtype":str(df[col].dtype),"unique_count":int(df[col].nunique()),"sample_values":[str(v) for v in df[col].dropna().unique()[:5]],"null_count":int(df[col].isnull().sum())}
        if "date" in col.lower(): info["semantic_type"]="date"
        elif df[col].dtype in ["int64","float64"]: info["semantic_type"]="numeric"
        else: info["semantic_type"]="categorical"
        ci.append(info)
        if df[col].isnull().sum()>0: missing[col]=int(df[col].isnull().sum())
    t=df.shape[0]*df.shape[1]
    q=round((1-sum(missing.values())/t)*100,1) if t else 100.0
    try:
        ds=f"File:{filename},{len(df)} rows\nCols:"+",".join(f"{c['name']}({c['semantic_type']})" for c in ci)
        qs=parse_json(llm.chat(PROFILE_PROMPT.format(info=ds),"Questions."))[:3]
    except Exception:
        qs=["Show revenue by region","Monthly trends","Top products by profit"]
    return {"filename":filename,"rows":len(df),"columns":len(df.columns),"column_info":ci,"data_quality_score":q,"missing_values":missing,"suggested_questions":qs,"preview":df.head(5).to_dict(orient="records")}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FASTAPI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.load_default()
    yield

app = FastAPI(title="DASH.AI", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def root(): return {"message":"DASH.AI Running"}

@app.get("/api/health")
def health(): return {"status":"healthy","data_loaded":bool(db.schema_info),"table_name":db.table_name}

@app.post("/api/query")
def query(req: QueryRequest): return process_query(req.question, req.conversation_history or [])

@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"): raise HTTPException(400,"CSV only")
    c = await file.read()
    db.load_bytes(c, file.filename)
    return {"status":"success","message":f"Loaded {len(db.df)} rows","profile":profile_data(db.df,file.filename)}

@app.get("/api/profile")
def get_profile():
    if db.df is None: raise HTTPException(404,"No data")
    return profile_data(db.df,db.table_name+".csv")

@app.post("/api/deep-dive")
def deep_dive(): return generate_deep_dive()

@app.post("/api/what-if")
def what_if(req: WhatIfRequest): return run_whatif(req.price_change,req.cost_change,req.units_change)

@app.get("/api/anomalies")
def anomalies_route(): return detect_anomalies()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)