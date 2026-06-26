"""
DASH.AI Backend - AI BI Co-Pilot
Fixed: CSV encoding detection for non-UTF-8 files (Excel exports, etc.)
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
    discount_change: float = 0.0
    units_change: float = 0.0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SAFE CSV READER — handles encoding issues
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def read_csv_safe(source, is_bytes=False) -> pd.DataFrame:
    """
    Try multiple encodings to read CSV.
    Handles Excel exports (cp1252), Latin-1, UTF-8-BOM, etc.
    """
    encodings = ["utf-8", "utf-8-sig", "cp1252", "latin-1", "iso-8859-1", "ascii"]

    for enc in encodings:
        try:
            if is_bytes:
                df = pd.read_csv(io.BytesIO(source), encoding=enc)
            else:
                df = pd.read_csv(source, encoding=enc)
            print(f"[CSV] Successfully read with encoding: {enc}")
            return df
        except UnicodeDecodeError:
            continue
        except Exception as e:
            # Non-encoding error — re-raise
            raise e

    # Last resort: read with errors='replace' (replaces bad chars with ?)
    print("[CSV] All encodings failed — using latin-1 with error replacement")
    if is_bytes:
        return pd.read_csv(io.BytesIO(source), encoding="latin-1", on_bad_lines="skip")
    else:
        return pd.read_csv(source, encoding="latin-1", on_bad_lines="skip")


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
        self.actual_columns: List[str] = []

    def load_default(self):
        paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sample_sales.csv"),
            os.path.join(os.getcwd(), "data", "sample_sales.csv"),
            "data/sample_sales.csv",
            "backend/data/sample_sales.csv",
        ]
        for p in paths:
            if os.path.exists(p):
                print(f"[OK] Default CSV: {p}")
                self.load_csv(p)
                return
        print("[WARN] No default CSV found — waiting for upload")

    def load_csv(self, filepath: str, table_name: str = "sales_data"):
        self.table_name = table_name
        self.df = read_csv_safe(filepath, is_bytes=False)
        self._process()

    def load_bytes(self, file_bytes: bytes, filename: str):
        self.table_name = (
            filename.replace(".csv", "")
            .replace(" ", "_")
            .replace("-", "_")
            .lower()
        )
        self.df = read_csv_safe(file_bytes, is_bytes=True)
        self._process()

    def _process(self):
        # ── Normalize column names ──
        self.df.columns = [
            c.strip()
            .lower()
            .replace(" ", "_")
            .replace(".", "_")
            .replace("(", "")
            .replace(")", "")
            .replace("/", "_")
            .replace("-", "_")
            .replace("__", "_")
            .strip("_")
            for c in self.df.columns
        ]

        # Remove fully empty columns
        self.df = self.df.dropna(axis=1, how="all")

        # Remove duplicate columns
        self.df = self.df.loc[:, ~self.df.columns.duplicated()]

        self.actual_columns = list(self.df.columns)
        print(f"[COLUMNS] {self.actual_columns}")

        # ── Parse date columns ──
        for col in self.df.columns:
            if any(kw in col.lower() for kw in ["date", "datetime", "timestamp"]):
                try:
                    self.df[col] = pd.to_datetime(
                        self.df[col], dayfirst=False, infer_datetime_format=True
                    ).dt.strftime("%Y-%m-%d")
                    print(f"[DATE] Parsed '{col}' as date")
                except Exception:
                    pass

        # ── Force numeric on likely numeric columns ──
        numeric_hints = [
            "price", "cost", "revenue", "amount", "total", "quantity",
            "units", "sold", "profit", "discount", "rating", "review",
            "count", "score", "margin", "tax", "fee", "salary", "income",
            "sl_no", "id_num",
        ]
        for col in self.df.columns:
            if any(hint in col.lower() for hint in numeric_hints):
                if self.df[col].dtype == "object":
                    # Try to clean and convert
                    try:
                        cleaned = (
                            self.df[col]
                            .astype(str)
                            .str.replace(",", "", regex=False)
                            .str.replace("$", "", regex=False)
                            .str.replace("₹", "", regex=False)
                            .str.replace("€", "", regex=False)
                            .str.replace("£", "", regex=False)
                            .str.strip()
                        )
                        self.df[col] = pd.to_numeric(cleaned, errors="coerce")
                        print(f"[NUMERIC] Converted '{col}' to numeric")
                    except Exception:
                        pass

        # ── Derive missing columns ──
        if "total_revenue" not in self.df.columns:
            if "price" in self.df.columns and "quantity_sold" in self.df.columns:
                self.df["total_revenue"] = self.df["price"] * self.df["quantity_sold"]
                print("[DERIVED] total_revenue = price × quantity_sold")
            elif "price" in self.df.columns and "quantity" in self.df.columns:
                self.df["total_revenue"] = self.df["price"] * self.df["quantity"]
                print("[DERIVED] total_revenue = price × quantity")

        if "discount_amount" not in self.df.columns:
            if "price" in self.df.columns and "discounted_price" in self.df.columns:
                self.df["discount_amount"] = self.df["price"] - self.df["discounted_price"]
                print("[DERIVED] discount_amount = price − discounted_price")
            elif "price" in self.df.columns and "discount_price" in self.df.columns:
                self.df["discount_amount"] = self.df["price"] - self.df["discount_price"]
                print("[DERIVED] discount_amount = price − discount_price")

        if "discount_pct" not in self.df.columns:
            if "price" in self.df.columns and "discount_amount" in self.df.columns:
                self.df["discount_pct"] = (
                    self.df["discount_amount"] / self.df["price"] * 100
                ).round(1)
                print("[DERIVED] discount_pct computed")

        self.actual_columns = list(self.df.columns)

        # ── Write to SQLite ──
        self.df.to_sql(self.table_name, self.conn, if_exists="replace", index=False)

        # ── Create indexes ──
        self._create_indexes()

        self.schema_info = self._schema()
        self._build_aliases()
        print(f"[OK] {len(self.df)} rows → '{self.table_name}' | {len(self.actual_columns)} cols")

    def _create_indexes(self):
        idx_candidates = [
            "order_date", "date", "product_category", "product_id",
            "customer", "payment_method", "rating", "region",
            "category", "product_name", "salesperson",
        ]
        created = 0
        for col in idx_candidates:
            if col in self.actual_columns:
                try:
                    self.conn.execute(
                        f"CREATE INDEX IF NOT EXISTS idx_{col} ON {self.table_name}([{col}])"
                    )
                    created += 1
                except Exception:
                    pass

        # Composite indexes for common GROUP BY pairs
        date_col = next((c for c in self.actual_columns if "date" in c.lower()), None)
        cat_col = next(
            (c for c in self.actual_columns if c in ["product_category", "category"]),
            None,
        )
        if date_col and cat_col:
            try:
                self.conn.execute(
                    f"CREATE INDEX IF NOT EXISTS idx_cat_date "
                    f"ON {self.table_name}([{cat_col}], [{date_col}])"
                )
                created += 1
            except Exception:
                pass

        print(f"[OK] {created} indexes created")

    def _build_aliases(self):
        if self.df is None:
            return
        self.column_aliases = {}
        actual = set(self.actual_columns)

        alias_map = {
            "revenue": ["total_revenue", "amount", "sales_amount"],
            "sales": ["total_revenue", "revenue", "amount"],
            "amount": ["total_revenue", "revenue"],
            "income": ["total_revenue", "revenue"],
            "cost": ["discounted_price", "discount_price", "price"],
            "unit_price": ["price"],
            "selling_price": ["discounted_price", "discount_price"],
            "quantity": ["quantity_sold", "qty", "units"],
            "units": ["quantity_sold", "quantity", "units_sold"],
            "qty": ["quantity_sold", "quantity"],
            "product": ["product_category", "product_id", "product_name"],
            "product_name": ["product_id"],
            "category": ["product_category"],
            "item": ["product_id", "product_name"],
            "buyer": ["customer"],
            "client": ["customer"],
            "name": ["customer", "product_name"],
            "date": ["order_date"],
            "payment": ["payment_method"],
            "score": ["rating"],
            "stars": ["rating"],
            "reviews": ["review_count"],
            "discount": ["discount_price", "discounted_price", "discount_pct"],
            "offer": ["discount_price", "discounted_price"],
            "region": ["product_category"],
            "profit": ["total_revenue"],
        }

        for keyword, candidates in alias_map.items():
            if keyword not in actual:
                for c in candidates:
                    if c in actual:
                        self.column_aliases[keyword] = c
                        break

        for c in actual:
            self.column_aliases[c] = c

    def _schema(self) -> str:
        cursor = self.conn.execute(f"PRAGMA table_info({self.table_name})")
        cols = cursor.fetchall()
        lines = [
            f"Table: {self.table_name}",
            f"Row count: {len(self.df)}",
            f"ALL AVAILABLE COLUMNS (use ONLY these exact names):",
        ]
        for col in cols:
            col_name = col[1]
            col_type = col[2]
            try:
                samples = self.conn.execute(
                    f"SELECT DISTINCT [{col_name}] FROM {self.table_name} LIMIT 6"
                ).fetchall()
                s = ", ".join(str(r[0]) for r in samples)
            except Exception:
                s = "N/A"
            lines.append(f"  - {col_name} ({col_type}) → examples: {s}")
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
                clean_col = col
                func_match = re.match(
                    r"(SUM|AVG|COUNT|MAX|MIN|ROUND)\((\w+)\)", col, re.IGNORECASE
                )
                if func_match:
                    func_name = func_match.group(1).lower()
                    col_name = func_match.group(2)
                    if func_name == "sum":
                        clean_col = f"total_{col_name}"
                    elif func_name == "avg":
                        clean_col = f"avg_{col_name}"
                    elif func_name == "count":
                        clean_col = f"count_{col_name}"
                    else:
                        clean_col = f"{func_name}_{col_name}"
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
            print("[OK] Groq API key loaded")

    def chat(self, system: str, user: str, temp: float = 0.1) -> str:
        if not self.api_key:
            raise Exception("GROQ_API_KEY not set")
        r = requests.post(
            self.url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": temp,
                "max_tokens": 4096,
            },
            timeout=30,
        )
        if r.status_code != 200:
            raise Exception(f"Groq error {r.status_code}: {r.text[:300]}")
        return r.json()["choices"][0]["message"]["content"].strip()


llm = LLM()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PROMPTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SQL_PROMPT = """You are a SQLite SQL generator for a sales/e-commerce dataset.

DATABASE SCHEMA:
{schema}

TABLE: {table}
EXACT COLUMNS: {columns}

CRITICAL RULES:
1. ONLY use columns from EXACT COLUMNS above — nothing else.
2. ALWAYS alias aggregations: SUM(x) AS total_x, AVG(x) AS avg_x, COUNT(*) AS order_count
3. For monthly data: strftime('%Y-%m', order_date) AS month
4. For yearly data: strftime('%Y', order_date) AS year
5. ALWAYS include ORDER BY.
6. LIMIT 50 for grouped queries.
7. Return ONLY raw SQL — no markdown, no backticks, no explanation.
8. If a requested column doesn't exist, use the closest match from EXACT COLUMNS.

USER QUESTION: {question}
CONTEXT: {history}"""

SQL_FIX_PROMPT = """Fix this SQLite query. Error: {error}

TABLE: {table}
AVAILABLE COLUMNS (use ONLY these): {columns}

FAILED SQL: {failed_sql}

Return ONLY the corrected SQL, nothing else."""

CHART_PROMPT = """Design a dashboard for this data. Return ONLY valid JSON:
{{
  "main_chart": {{
    "type": "bar"|"line"|"pie"|"area",
    "title": "title",
    "x_axis": "EXACT column from DATA COLUMNS",
    "y_axis": "EXACT column from DATA COLUMNS"
  }},
  "secondary_chart": {{
    "type": "pie"|"bar",
    "title": "title",
    "x_axis": "EXACT column",
    "y_axis": "EXACT column"
  }} or null,
  "kpi_cards": [
    {{"label": "Label", "value_column": "EXACT column", "aggregation": "sum"|"avg"|"max"|"count", "format": "currency"|"number"|"percent"}}
  ]
}}

Use "line" for time-series. "bar" for comparisons. "pie" for shares.

DATA COLUMNS: {columns}
SAMPLE: {sample}
ROWS: {rows}
QUESTION: {question}

Return ONLY JSON."""

STORY_PROMPT = """Write 2-3 sentence executive insight. Use numbers ($X.XM, XX%).
Never say "the data shows". Max 3 sentences. End with actionable insight.

DATA: {data_summary}
QUESTION: {question}

Return ONLY text."""

SUGGEST_PROMPT = """Suggest 3 follow-up questions about this dataset as JSON array.
Schema: {schema}
Previous question: {question}
Return ONLY: ["q1", "q2", "q3"]"""

PROFILE_PROMPT = """Generate 3 CXO business questions for this dataset as JSON array.
DATASET: {info}
Return ONLY: ["q1", "q2", "q3"]"""

DEEP_DIVE_PROMPT = """Analyze this data deeply. Return JSON:
{{
  "top_revenue_drivers": [{{"name": "x", "revenue": 123, "trend": "up"}}],
  "risk_areas": [{{"name": "x", "issue": "desc", "impact_amount": 123, "severity": "high"}}],
  "root_cause_analysis": "2-3 sentences with numbers",
  "recommendations": [{{"action": "do this", "expected_impact": "$X increase", "priority": "high"}}]
}}
DATA: {data_summary}
Return ONLY JSON."""

WHATIF_PROMPT = """Analyze scenario in 2-3 sentences:
Current Revenue: ${current_revenue:,.0f}, Units: {current_units:,.0f}
Changes: Price {price_change:+.1f}%, Discount {discount_change:+.1f}%, Units {units_change:+.1f}%
Projected Revenue: ${new_revenue:,.0f} (change: {revenue_pct_change:+.1f}%)
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
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        text = m.group(1)
    m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if m:
        text = m.group(1)
    return json.loads(text)


def clean_sql(text: str) -> str:
    text = re.sub(r"```(?:sql)?\s*", "", text)
    text = re.sub(r"```", "", text)
    text = text.strip().rstrip(";").strip()
    m = re.search(r"(SELECT\s)", text, re.IGNORECASE)
    if m:
        text = text[m.start():]
    return text


def format_val(val: float, fmt: str = "number") -> str:
    if fmt == "currency":
        if abs(val) >= 1e9:
            return f"${val / 1e9:,.2f}B"
        if abs(val) >= 1e6:
            return f"${val / 1e6:,.1f}M"
        if abs(val) >= 1e3:
            return f"${val / 1e3:,.1f}K"
        return f"${val:,.0f}"
    if fmt == "percent":
        return f"{val:.1f}%"
    if abs(val) >= 1e9:
        return f"{val / 1e9:,.2f}B"
    if abs(val) >= 1e6:
        return f"{val / 1e6:,.1f}M"
    if abs(val) >= 1e3:
        return f"{val / 1e3:,.1f}K"
    return f"{val:,.0f}"


def error_response(msg, suggestion=None, columns=None):
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


def build_fallback_query(question: str) -> str:
    """Build keyword-based fallback SQL when LLM fails"""
    q = question.lower()
    t = db.table_name
    cols = db.actual_columns

    # Find the best revenue/amount column
    rev_col = next(
        (c for c in ["total_revenue", "revenue", "amount", "sales"] if c in cols),
        None,
    )
    qty_col = next(
        (c for c in ["quantity_sold", "quantity", "units_sold", "units", "qty"] if c in cols),
        None,
    )
    date_col = next(
        (c for c in ["order_date", "date", "datetime", "order_datetime"] if c in cols),
        None,
    )
    cat_col = next(
        (c for c in ["product_category", "category", "product_type"] if c in cols),
        None,
    )
    prod_col = next(
        (c for c in ["product_id", "product_name", "product", "item"] if c in cols),
        None,
    )
    cust_col = next(
        (c for c in ["customer", "customer_name", "buyer", "client"] if c in cols),
        None,
    )
    pay_col = next(
        (c for c in ["payment_method", "payment_type", "payment"] if c in cols),
        None,
    )
    rating_col = next(
        (c for c in ["rating", "score", "stars"] if c in cols),
        None,
    )

    # Build SELECT parts
    def agg_parts():
        parts = []
        if rev_col:
            parts.append(f"SUM([{rev_col}]) AS total_revenue")
        if qty_col:
            parts.append(f"SUM([{qty_col}]) AS total_units")
        parts.append("COUNT(*) AS order_count")
        if rating_col:
            parts.append(f"ROUND(AVG([{rating_col}]), 2) AS avg_rating")
        return ", ".join(parts) if parts else "COUNT(*) AS row_count"

    # Monthly / time trends
    if date_col and any(w in q for w in ["monthly", "month", "trend", "over time", "time series"]):
        return (
            f"SELECT strftime('%Y-%m', [{date_col}]) AS month, {agg_parts()} "
            f"FROM {t} GROUP BY month ORDER BY month"
        )

    if date_col and any(w in q for w in ["yearly", "year", "annual", "this year"]):
        return (
            f"SELECT strftime('%Y', [{date_col}]) AS year, {agg_parts()} "
            f"FROM {t} GROUP BY year ORDER BY year"
        )

    if date_col and any(w in q for w in ["daily", "day", "per day"]):
        return (
            f"SELECT [{date_col}], {agg_parts()} "
            f"FROM {t} GROUP BY [{date_col}] ORDER BY [{date_col}] LIMIT 50"
        )

    # Category
    if cat_col and any(w in q for w in ["category", "categories", "by category", "product type"]):
        return (
            f"SELECT [{cat_col}], {agg_parts()} "
            f"FROM {t} GROUP BY [{cat_col}] ORDER BY total_revenue DESC"
        )

    # Product
    if prod_col and any(w in q for w in ["product", "top product", "best product", "by product", "best selling"]):
        extra = f", [{cat_col}]" if cat_col else ""
        group_extra = f", [{cat_col}]" if cat_col else ""
        return (
            f"SELECT [{prod_col}]{extra}, {agg_parts()} "
            f"FROM {t} GROUP BY [{prod_col}]{group_extra} "
            f"ORDER BY total_revenue DESC LIMIT 15"
        )

    # Payment
    if pay_col and any(w in q for w in ["payment", "payment method", "pay", "how pay"]):
        return (
            f"SELECT [{pay_col}], {agg_parts()} "
            f"FROM {t} GROUP BY [{pay_col}] ORDER BY total_revenue DESC"
        )

    # Customer
    if cust_col and any(w in q for w in ["customer", "buyer", "top customer", "client"]):
        return (
            f"SELECT [{cust_col}], {agg_parts()} "
            f"FROM {t} GROUP BY [{cust_col}] ORDER BY total_revenue DESC LIMIT 20"
        )

    # Rating
    if rating_col and any(w in q for w in ["rating", "rated", "review", "star", "best rated"]):
        group_col = prod_col or cat_col or cust_col
        if group_col:
            order = "ASC" if any(w in q for w in ["worst", "low", "poor"]) else "DESC"
            return (
                f"SELECT [{group_col}], ROUND(AVG([{rating_col}]), 2) AS avg_rating, "
                f"{agg_parts()} "
                f"FROM {t} GROUP BY [{group_col}] HAVING COUNT(*) >= 3 "
                f"ORDER BY avg_rating {order} LIMIT 15"
            )

    # Discount
    if any(w in q for w in ["discount", "offer", "deal"]):
        disc_parts = []
        if "price" in cols:
            disc_parts.append("ROUND(AVG([price]), 2) AS avg_price")
        if "discounted_price" in cols:
            disc_parts.append("ROUND(AVG([discounted_price]), 2) AS avg_disc_price")
        elif "discount_price" in cols:
            disc_parts.append("ROUND(AVG([discount_price]), 2) AS avg_disc_price")
        disc_parts.append(agg_parts())
        group = cat_col or prod_col
        if group:
            return (
                f"SELECT [{group}], {', '.join(disc_parts)} "
                f"FROM {t} GROUP BY [{group}] ORDER BY total_revenue DESC"
            )

    # Revenue / sales / total / summary
    if any(w in q for w in ["total", "sales", "revenue", "overall", "summary", "overview", "dashboard"]):
        group = cat_col or pay_col or prod_col
        if group:
            return (
                f"SELECT [{group}], {agg_parts()} "
                f"FROM {t} GROUP BY [{group}] ORDER BY total_revenue DESC"
            )

    # Compare
    if any(w in q for w in ["compare", "versus", "vs"]):
        if cat_col and pay_col:
            return (
                f"SELECT [{cat_col}], [{pay_col}], {agg_parts()} "
                f"FROM {t} GROUP BY [{cat_col}], [{pay_col}] "
                f"ORDER BY total_revenue DESC LIMIT 30"
            )

    # Default: use first categorical column
    group = cat_col or pay_col or prod_col or cust_col
    if group:
        return (
            f"SELECT [{group}], {agg_parts()} "
            f"FROM {t} GROUP BY [{group}] ORDER BY total_revenue DESC LIMIT 20"
        )

    # Absolute fallback
    return f"SELECT * FROM {t} LIMIT 20"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SMART SQL EXECUTOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def smart_execute(sql: str, question: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            upper = sql.upper().strip()
            if not upper.startswith("SELECT"):
                sql = build_fallback_query(question)

            for danger in ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]:
                if danger in upper:
                    return None, None, sql, f"Blocked: {danger}"

            results, columns = db.execute(sql)

            if results and len(results) > 0:
                df_check = pd.DataFrame(results)
                num_cols = df_check.select_dtypes(include=["number"]).columns
                has_valid = any(
                    df_check[nc].notna().any() and df_check[nc].sum() != 0
                    for nc in num_cols
                )
                if has_valid:
                    return results, columns, sql, None
                if attempt < max_retries - 1:
                    sql = build_fallback_query(question)
                    continue
                return results, columns, sql, None

            if attempt < max_retries - 1:
                fallback = build_fallback_query(question)
                if fallback != sql:
                    sql = fallback
                    continue
            return [], columns or [], sql, None

        except Exception as e:
            err = str(e)
            print(f"[SQL Attempt {attempt + 1}/{max_retries}] {err}")
            if attempt < max_retries - 1:
                if attempt == 0:
                    sql = build_fallback_query(question)
                    continue
                try:
                    fix_raw = llm.chat(
                        SQL_FIX_PROMPT.format(
                            error=err,
                            table=db.table_name,
                            columns=json.dumps(db.actual_columns),
                            failed_sql=sql,
                        ),
                        "Fix SQL",
                    )
                    sql = clean_sql(fix_raw)
                except Exception:
                    sql = build_fallback_query(question)

    return None, None, sql, "Query failed after retries"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN QUERY PIPELINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def process_query(question: str, history: list = None) -> dict:
    if not db.schema_info or db.df is None:
        return error_response("No data loaded. Upload a CSV first.")

    history = history or []
    hist_str = (
        "\n".join(f"{m.get('role', 'user')}: {m.get('content', '')}" for m in history[-6:])
        or "None"
    )
    cols_list = db.actual_columns

    try:
        # Step 1: Generate SQL
        try:
            sql_raw = llm.chat(
                SQL_PROMPT.format(
                    schema=db.schema_info,
                    table=db.table_name,
                    columns=json.dumps(cols_list),
                    question=question,
                    history=hist_str,
                ),
                question,
            )
            sql = clean_sql(sql_raw)
        except Exception:
            sql = build_fallback_query(question)

        print(f"[SQL] {sql}")

        # Step 2: Execute
        results, columns, final_sql, exec_error = smart_execute(sql, question)

        if exec_error or not results:
            fallback = build_fallback_query(question)
            if fallback:
                try:
                    results, columns = db.execute(fallback)
                    final_sql = fallback
                except Exception:
                    pass
            if not results:
                return error_response(
                    "No data found. Try a different question.",
                    f"Columns: {', '.join(cols_list)}",
                    columns=cols_list,
                )

        # Step 3: Chart config
        try:
            chart_raw = llm.chat(
                CHART_PROMPT.format(
                    columns=json.dumps(columns),
                    sample=json.dumps(results[:3], default=str),
                    rows=len(results),
                    question=question,
                ),
                "Design dashboard.",
            )
            dash_cfg = parse_json(chart_raw)
        except Exception:
            x_col = columns[0]
            y_col = None
            for c in columns[1:]:
                try:
                    if results[0].get(c) is not None and isinstance(results[0][c], (int, float)):
                        y_col = c
                        break
                except Exception:
                    pass
            if not y_col:
                y_col = columns[-1] if len(columns) > 1 else columns[0]
            chart_type = "line" if any(w in x_col.lower() for w in ["month", "year", "date"]) else "bar"
            dash_cfg = {
                "main_chart": {"type": chart_type, "title": question, "x_axis": x_col, "y_axis": y_col},
                "secondary_chart": None,
                "kpi_cards": [],
            }

        # Step 4: Narrative
        df = pd.DataFrame(results)
        summary = f"Question: {question}\nRows: {len(results)}, Columns: {columns}\n"
        for col in df.select_dtypes(include=["number"]).columns[:5]:
            if df[col].notna().any():
                summary += f"  {col}: total={df[col].sum():,.0f}, avg={df[col].mean():,.0f}\n"
        summary += f"Sample: {json.dumps(results[:2], default=str)}"

        try:
            narrative = llm.chat(
                STORY_PROMPT.format(data_summary=summary, question=question),
                "Insight.",
                temp=0.3,
            )
        except Exception:
            narrative = f"Query returned {len(results)} records."

        # Step 5: Follow-ups
        try:
            sug = llm.chat(
                SUGGEST_PROMPT.format(question=question, schema=db.schema_info),
                "Suggest.",
                temp=0.5,
            )
            followups = parse_json(sug)[:3]
        except Exception:
            followups = [
                "Show monthly revenue trends",
                "Top products by revenue",
                "Compare by payment method",
            ]

        # KPIs
        kpi_cards = []
        for kpi in dash_cfg.get("kpi_cards", []):
            try:
                col = kpi.get("value_column", "")
                if col in df.columns and df[col].notna().any():
                    agg_map = {
                        "sum": df[col].sum(), "avg": df[col].mean(),
                        "max": df[col].max(), "count": df[col].count(),
                    }
                    val = agg_map.get(kpi.get("aggregation", "sum"), df[col].sum())
                    if pd.notna(val) and val != 0:
                        kpi_cards.append({
                            "label": kpi.get("label", col.replace("_", " ").title()),
                            "value": format_val(float(val), kpi.get("format", "number")),
                            "trend": None,
                            "trend_direction": "neutral",
                        })
            except Exception:
                continue

        if not kpi_cards:
            for col in df.select_dtypes(include=["number"]).columns[:4]:
                val = df[col].sum()
                if pd.notna(val) and val != 0:
                    is_money = any(k in col.lower() for k in ["revenue", "price", "cost", "amount", "total", "profit"])
                    is_rating = "rating" in col.lower()
                    if is_rating:
                        kpi_cards.append({
                            "label": "Avg " + col.replace("_", " ").title(),
                            "value": f"{float(df[col].mean()):.2f}",
                            "trend": None, "trend_direction": "neutral",
                        })
                    else:
                        kpi_cards.append({
                            "label": col.replace("_", " ").title(),
                            "value": format_val(float(val), "currency" if is_money else "number"),
                            "trend": None, "trend_direction": "neutral",
                        })

        # Validate axes
        mc = dash_cfg.get("main_chart", {})
        x_ax = mc.get("x_axis", columns[0])
        y_ax = mc.get("y_axis", columns[-1] if len(columns) > 1 else columns[0])
        if x_ax not in columns:
            x_ax = columns[0]
        if y_ax not in columns:
            for c in columns:
                if c != x_ax and results and isinstance(results[0].get(c), (int, float)):
                    y_ax = c
                    break
            else:
                y_ax = columns[-1] if len(columns) > 1 else columns[0]

        chart_type = mc.get("type", "bar")
        if any(w in x_ax.lower() for w in ["month", "year", "date", "week"]):
            chart_type = "line"

        main_chart = {
            "type": chart_type,
            "title": mc.get("title", question),
            "x_axis": x_ax, "y_axis": y_ax,
            "series": mc.get("series"),
            "data": results,
            "highlight": mc.get("highlight"),
        }

        secondary_chart = None
        sc = dash_cfg.get("secondary_chart")
        if sc:
            sx = sc.get("x_axis", columns[0])
            sy = sc.get("y_axis", y_ax)
            if sx not in columns:
                sx = columns[0]
            if sy not in columns:
                sy = y_ax
            secondary_chart = {
                "type": sc.get("type", "pie"),
                "title": sc.get("title", "Breakdown"),
                "x_axis": sx, "y_axis": sy,
                "data": results,
            }

        dq = None
        missing = {c: int(df[c].isnull().sum()) for c in df.columns if df[c].isnull().sum() > 0}
        if missing:
            dq = {"missing_in_query": missing, "total_rows": len(results)}

        return {
            "kpi_cards": kpi_cards,
            "main_chart": main_chart,
            "secondary_chart": secondary_chart,
            "narrative": narrative,
            "suggested_followups": followups,
            "sql_query": final_sql,
            "error": None,
            "available_columns": cols_list,
            "data_quality": dq,
        }

    except Exception as e:
        return error_response(f"Error: {str(e)}", "Try: 'Show revenue by category'", columns=cols_list)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DEEP DIVE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_deep_dive() -> dict:
    if db.df is None:
        return {"error": "No data loaded"}
    df = db.df.copy()
    cols = db.actual_columns
    parts = []

    # Find columns dynamically
    rev_col = next((c for c in ["total_revenue", "revenue", "amount"] if c in cols), None)
    cat_col = next((c for c in ["product_category", "category"] if c in cols), None)
    prod_col = next((c for c in ["product_id", "product_name"] if c in cols), None)
    date_col = next((c for c in ["order_date", "date"] if c in cols), None)
    pay_col = next((c for c in ["payment_method", "payment"] if c in cols), None)
    rating_col = next((c for c in ["rating", "score"] if c in cols), None)
    qty_col = next((c for c in ["quantity_sold", "quantity"] if c in cols), None)

    if cat_col and rev_col:
        agg = {rev_col: (rev_col, "sum")}
        if qty_col:
            agg[qty_col] = (qty_col, "sum")
        if rating_col:
            agg[f"avg_{rating_col}"] = (rating_col, "mean")
        grp = df.groupby(cat_col).agg(**agg).reset_index()
        parts.append(f"By {cat_col}:\n{grp.to_string()}")

    if pay_col and rev_col:
        grp = df.groupby(pay_col).agg(
            revenue=(rev_col, "sum"), count=(rev_col, "count")
        ).reset_index()
        parts.append(f"\nBy {pay_col}:\n{grp.to_string()}")

    if prod_col and rev_col:
        grp = df.groupby(prod_col).agg(revenue=(rev_col, "sum")).reset_index()
        grp = grp.sort_values("revenue", ascending=False).head(15)
        parts.append(f"\nTop {prod_col}:\n{grp.to_string()}")

    try:
        result = parse_json(
            llm.chat(DEEP_DIVE_PROMPT.format(data_summary="\n".join(parts)), "Analyze.", temp=0.2)
        )
    except Exception as e:
        result = {
            "root_cause_analysis": f"Analysis of {len(df)} records complete.",
            "recommendations": [],
            "top_revenue_drivers": [],
            "risk_areas": [],
        }

    if date_col and rev_col:
        df["_m"] = pd.to_datetime(df[date_col]).dt.strftime("%Y-%m")
        monthly = df.groupby("_m").agg(total_revenue=(rev_col, "sum")).reset_index().rename(columns={"_m": "month"})
        result["monthly_trend"] = monthly.to_dict(orient="records")

    if cat_col and rev_col:
        cat_rev = df.groupby(cat_col).agg(total_revenue=(rev_col, "sum")).reset_index()
        cat_rev = cat_rev.sort_values("total_revenue", ascending=False)
        result["revenue_by_category"] = cat_rev.rename(columns={cat_col: "product_category"}).to_dict(orient="records")

    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WHAT-IF
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_whatif(price_change: float, discount_change: float, units_change: float):
    if db.df is None:
        return {"error": "No data loaded"}
    df = db.df
    cols = db.actual_columns

    rev_col = next((c for c in ["total_revenue", "revenue", "amount"] if c in cols), None)
    qty_col = next((c for c in ["quantity_sold", "quantity"] if c in cols), None)
    date_col = next((c for c in ["order_date", "date"] if c in cols), None)
    cat_col = next((c for c in ["product_category", "category"] if c in cols), None)

    current_revenue = float(df[rev_col].sum()) if rev_col else 0
    current_units = float(df[qty_col].sum()) if qty_col else 0

    pm, um = 1 + price_change / 100, 1 + units_change / 100
    new_revenue = current_revenue * pm * um
    discount_impact = current_revenue * (discount_change / 100) * 0.5
    new_revenue -= discount_impact
    revenue_diff = new_revenue - current_revenue
    pct = (revenue_diff / current_revenue * 100) if current_revenue else 0

    monthly = []
    if date_col and rev_col:
        df2 = df.copy()
        df2["_m"] = pd.to_datetime(df2[date_col]).dt.strftime("%Y-%m")
        mg = df2.groupby("_m").agg(actual_revenue=(rev_col, "sum")).reset_index()
        for _, r in mg.iterrows():
            ar = r["actual_revenue"]
            pr = ar * pm * um - ar * (discount_change / 100) * 0.5
            monthly.append({"month": r["_m"], "actual_revenue": round(ar), "projected_revenue": round(pr)})

    cat_impact = []
    if cat_col and rev_col:
        cg = df.groupby(cat_col).agg(revenue=(rev_col, "sum")).reset_index()
        for _, r in cg.iterrows():
            cr = r["revenue"]
            pr = cr * pm * um - cr * (discount_change / 100) * 0.5
            cat_impact.append({
                "category": r[cat_col],
                "current_revenue": round(cr),
                "projected_revenue": round(pr),
                "change_pct": round((pr - cr) / cr * 100, 1) if cr else 0,
            })

    try:
        ai_text = llm.chat(
            WHATIF_PROMPT.format(
                current_revenue=current_revenue, current_units=current_units,
                price_change=price_change, discount_change=discount_change,
                units_change=units_change, new_revenue=new_revenue,
                revenue_pct_change=pct,
            ),
            "Analyze.",
            temp=0.3,
        )
    except Exception:
        ai_text = f"Projected revenue change: {format_val(revenue_diff, 'currency')} ({pct:+.1f}%)"

    return {
        "current": {"revenue": round(current_revenue), "units": round(current_units)},
        "projected": {"revenue": round(new_revenue)},
        "change": {"revenue_diff": round(revenue_diff), "revenue_pct_change": round(pct, 1)},
        "monthly_comparison": monthly,
        "category_impact": cat_impact,
        "ai_commentary": ai_text,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ANOMALY DETECTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def detect_anomalies():
    if db.df is None:
        return {"anomalies": [], "count": 0, "ai_analysis": []}
    df = db.df.copy()
    found = []

    for col in df.select_dtypes(include=["number"]).columns:
        if "sl" in col.lower() and "no" in col.lower():
            continue
        series = df[col].dropna()
        if len(series) < 10:
            continue
        mean, std = series.mean(), series.std()
        if std == 0:
            continue
        outliers = df[(df[col] > mean + 2 * std) | (df[col] < mean - 2 * std)]
        if 0 < len(outliers) < len(df) * 0.05:
            for _, r in outliers.head(3).iterrows():
                direction = "unusually high" if r[col] > mean else "unusually low"
                ctx = ""
                for ctx_col in ["product_category", "category", "product_id", "customer", "region"]:
                    if ctx_col in df.columns:
                        ctx += f" ({r.get(ctx_col, '')})"
                        break
                found.append(f"{col} {direction}: {r[col]:,.0f} vs avg {mean:,.0f}{ctx}")

    date_col = next((c for c in ["order_date", "date"] if c in df.columns), None)
    rev_col = next((c for c in ["total_revenue", "revenue"] if c in df.columns), None)
    if date_col and rev_col:
        df["_m"] = pd.to_datetime(df[date_col]).dt.strftime("%Y-%m")
        mo = df.groupby("_m")[rev_col].sum().reset_index()
        mo["pct"] = mo[rev_col].pct_change() * 100
        for _, r in mo[mo["pct"] < -15].iterrows():
            found.append(f"Revenue dropped {r['pct']:.1f}% in {r['_m']}")

    if not found:
        return {"anomalies": [], "count": 0, "ai_analysis": []}

    try:
        sm = f"Rows:{len(df)}\n" + "\n".join(
            f"{c}: mean={df[c].mean():,.0f}, std={df[c].std():,.0f}"
            for c in df.select_dtypes(include=["number"]).columns[:5]
            if not ("sl" in c.lower() and "no" in c.lower())
        )
        ai = parse_json(
            llm.chat(
                ANOMALY_PROMPT.format(
                    data_summary=sm,
                    anomalies="\n".join(f"- {a}" for a in found[:8]),
                ),
                "Analyze.",
                temp=0.2,
            )
        )
    except Exception:
        ai = [
            {"metric": a[:40], "description": a, "severity": "medium", "suggestion": "Investigate"}
            for a in found[:5]
        ]

    return {"anomalies": found[:8], "count": len(found), "ai_analysis": ai[:5]}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATA PROFILER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def profile_data(df: pd.DataFrame, filename: str):
    column_info = []
    missing = {}
    for col in df.columns:
        info = {
            "name": col,
            "dtype": str(df[col].dtype),
            "unique_count": int(df[col].nunique()),
            "sample_values": [str(v) for v in df[col].dropna().unique()[:5]],
            "null_count": int(df[col].isnull().sum()),
        }
        if "date" in col.lower():
            info["semantic_type"] = "date"
        elif "id" in col.lower() and "sl" not in col.lower():
            info["semantic_type"] = "identifier"
        elif df[col].dtype in ["int64", "float64"]:
            info["semantic_type"] = "numeric"
            info["stats"] = {
                "mean": round(float(df[col].mean()), 2),
                "min": round(float(df[col].min()), 2),
                "max": round(float(df[col].max()), 2),
            }
        else:
            info["semantic_type"] = "categorical"
        column_info.append(info)
        if df[col].isnull().sum() > 0:
            missing[col] = int(df[col].isnull().sum())

    total = df.shape[0] * df.shape[1]
    quality = round((1 - sum(missing.values()) / total) * 100, 1) if total else 100.0

    try:
        ds = f"File:{filename}, {len(df)} rows, Cols:" + ",".join(
            f"{c['name']}({c['semantic_type']})" for c in column_info
        )
        questions = parse_json(llm.chat(PROFILE_PROMPT.format(info=ds), "Questions."))[:3]
    except Exception:
        questions = [
            "Show total revenue by category",
            "What is the monthly trend?",
            "Top products by revenue",
        ]

    return {
        "filename": filename,
        "rows": len(df),
        "columns": len(df.columns),
        "column_info": column_info,
        "data_quality_score": quality,
        "missing_values": missing,
        "suggested_questions": questions,
        "preview": json.loads(df.head(5).to_json(orient="records", default_handler=str)),
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FASTAPI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.load_default()
    yield


app = FastAPI(title="DASH.AI", version="2.1", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "DASH.AI Running", "version": "2.1"}


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "data_loaded": bool(db.schema_info),
        "table_name": db.table_name,
        "row_count": len(db.df) if db.df is not None else 0,
        "columns": db.actual_columns,
    }


@app.post("/api/query")
def query(req: QueryRequest):
    return process_query(req.question, req.conversation_history or [])


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Only CSV files supported")
    content = await file.read()
    if len(content) > 100 * 1024 * 1024:
        raise HTTPException(400, "File too large (max 100MB)")

    try:
        db.load_bytes(content, file.filename)
    except Exception as e:
        raise HTTPException(
            400,
            f"Failed to parse CSV: {str(e)[:200]}. "
            f"Try saving as UTF-8 CSV from Excel.",
        )

    return {
        "status": "success",
        "message": f"Loaded {len(db.df)} rows with {len(db.actual_columns)} columns",
        "profile": profile_data(db.df, file.filename),
    }


@app.get("/api/profile")
def get_profile():
    if db.df is None:
        raise HTTPException(404, "No data loaded")
    return profile_data(db.df, db.table_name + ".csv")


@app.post("/api/deep-dive")
def deep_dive():
    return generate_deep_dive()


@app.post("/api/what-if")
def what_if(req: WhatIfRequest):
    return run_whatif(req.price_change, req.discount_change, req.units_change)


@app.get("/api/anomalies")
def anomalies_route():
    return detect_anomalies()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)