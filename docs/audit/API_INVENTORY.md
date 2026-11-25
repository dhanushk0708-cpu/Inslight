# INSLIGHT — Complete API Inventory
**Document ID:** `AUDIT-DOC-06`
**Target:** FastAPI REST Endpoints in `backend/main.py`
**Date of Audit:** November 2026
**Auditor:** Backend Architect & Application Security Auditor

---

## 1. API Inventory Summary Table

| HTTP Method | Route Path | Function Name | Request Format | Response Format | Auth | DB Access | AI Calls | Risk / Issues |
|---|---|---|---|---|---|---|---|---|
| `GET` | `/` | `root` | None | JSON | None | None | None | Low |
| `GET` | `/api/health` | `health` | None | JSON | None | Reads schema | None | Low: Exposes table/col structure |
| `POST` | `/api/query` | `query` | JSON (`QueryRequest`) | JSON | None | Executes SQL | 4x LLM (Groq) | High: Latency, no rate limit, SQL injection |
| `POST` | `/api/upload` | `upload` | `multipart/form-data` | JSON | None | Replaces DB | 1x LLM (Groq) | Critical: Overwrites global data, memory DoS |
| `GET` | `/api/profile` | `get_profile` | None | JSON | None | Reads DataFrame | 1x LLM (Groq) | Medium: Shared dataset profile |
| `POST` | `/api/deep-dive` | `deep_dive` | None | JSON | None | Reads DataFrame | 1x LLM (Groq) | Medium: Synchronous compute |
| `POST` | `/api/what-if` | `what_if` | JSON (`WhatIfRequest`) | JSON | None | Reads DataFrame | 1x LLM (Groq) | Medium: Hardcoded business logic |
| `GET` | `/api/anomalies` | `anomalies_route`| None | JSON | None | Reads DataFrame | 1x LLM (Groq) | Medium: Unbounded Z-score scan |

---

## 2. Detailed Endpoint Specifications

### 2.1 `GET /`
- **Location:** `backend/main.py` lines 1272–1274
- **Purpose:** Simple service ping / root banner.
- **Request:** Empty.
- **Response:**
  ```json
  {"message": "DASH.AI Running", "version": "2.1"}
  ```
- **Authentication:** None.

---

### 2.2 `GET /api/health`
- **Location:** `backend/main.py` lines 1277–1285
- **Purpose:** Health check reporting whether data is loaded, current table name, row count, and column list.
- **Request:** Empty.
- **Response:**
  ```json
  {
    "status": "healthy",
    "data_loaded": true,
    "table_name": "sales_data",
    "row_count": 97,
    "columns": ["date", "region", "product_category", "product_name", "units_sold", "unit_price", "revenue", "cost", "profit", "salesperson"]
  }
  ```
- **Concerns:** Unauthenticated inspection of table names and column headers.

---

### 2.3 `POST /api/query`
- **Location:** `backend/main.py` lines 1288–1290 (handled by `process_query` lines 774–987)
- **Purpose:** Core conversational analytics pipeline: translates natural language into SQL, executes it, designs dashboard charts, writes executive narrative, and suggests follow-ups.
- **Request Schema (`QueryRequest`):**
  ```json
  {
    "question": "Show revenue by region",
    "conversation_history": [
      {"role": "user", "content": "previous question"}
    ]
  }
  ```
- **Response Schema:**
  ```json
  {
    "kpi_cards": [{"label": "Total Revenue", "value": "$1.2M", "trend": null, "trend_direction": "neutral"}],
    "main_chart": {"type": "bar", "title": "Revenue by Region", "x_axis": "region", "y_axis": "total_revenue", "series": null, "data": [...], "highlight": null},
    "secondary_chart": null,
    "narrative": "East region led revenue at $450K...",
    "suggested_followups": ["Top products in East", "Monthly revenue trend"],
    "sql_query": "SELECT region, SUM(revenue) AS total_revenue FROM sales_data GROUP BY region ORDER BY total_revenue DESC",
    "error": null,
    "available_columns": [...],
    "data_quality": null
  }
  ```
- **Security & Stability Concerns:**
  - Up to 4 sequential synchronous Groq API calls.
  - Zero rate-limiting: vulnerability to API quota exhaustion and financial denial-of-service.
  - Unsanitized dynamic SQL execution (`self.conn.execute(sql)`).
  - Silent fallback to keyword-guessed query when LLM fails.

---

### 2.4 `POST /api/upload`
- **Location:** `backend/main.py` lines 1293–1314
- **Purpose:** Uploads a CSV dataset, replaces active in-memory SQLite table, and profiles dataset statistics.
- **Request Format:** `multipart/form-data`, field: `file` (binary CSV).
- **Response Schema:**
  ```json
  {
    "status": "success",
    "message": "Loaded 97 rows with 10 columns",
    "profile": {
      "filename": "sample_sales.csv",
      "rows": 97,
      "columns": 10,
      "column_info": [...],
      "data_quality_score": 100.0,
      "missing_values": {},
      "suggested_questions": ["Show revenue by category", "Monthly trend"],
      "preview": [...]
    }
  }
  ```
- **Security & Stability Concerns:**
  - **CRITICAL:** Replaces the global in-memory database table, destroying other users' active data.
  - File size limit (100MB) is read entirely into memory via `await file.read()`, exposing the server to memory exhaustion DoS.
  - Extension check (`.endswith(".csv")`) does not inspect MIME type or magic bytes.
  - CPU-heavy Pandas parsing executes directly on the asyncio event loop thread.

---

### 2.5 `GET /api/profile`
- **Location:** `backend/main.py` lines 1317–1321
- **Purpose:** Fetches schema profile and CXO business questions for currently loaded dataset.
- **Request:** Empty.
- **Response Schema:** Same as `profile` sub-object in `/api/upload`.
- **Concerns:** Returns whatever dataset was last loaded by any user.

---

### 2.6 `POST /api/deep-dive`
- **Location:** `backend/main.py` lines 1324–1326 (handled by `generate_deep_dive` lines 993–1052)
- **Purpose:** Aggregates metrics by category, payment method, and product; sends summary to LLM for driver and risk analysis; computes monthly trend.
- **Request:** Empty body.
- **Response Schema:**
  ```json
  {
    "top_revenue_drivers": [{"name": "Electronics", "revenue": 540000, "trend": "up"}],
    "risk_areas": [{"name": "Clothing", "issue": "High return rate", "impact_amount": 25000, "severity": "high"}],
    "root_cause_analysis": "Executive overview of drivers...",
    "recommendations": [{"action": "Expand Electronics", "expected_impact": "+15% revenue", "priority": "high"}],
    "monthly_trend": [{"month": "2024-01", "total_revenue": 120000}],
    "revenue_by_category": [{"product_category": "Electronics", "total_revenue": 540000}]
  }
  ```
- **Concerns:** Synchronous pandas grouping; hardcoded column heuristics (`rev_col`, `cat_col`, `prod_col`).

---

### 2.7 `POST /api/what-if`
- **Location:** `backend/main.py` lines 1329–1331 (handled by `run_whatif` lines 1058–1124)
- **Purpose:** Simulates revenue impact of price, discount, and unit changes.
- **Request Schema (`WhatIfRequest`):**
  ```json
  {
    "price_change": 10.0,
    "discount_change": -5.0,
    "units_change": 15.0
  }
  ```
- **Response Schema:**
  ```json
  {
    "current": {"revenue": 1000000, "units": 5000},
    "projected": {"revenue": 1250000},
    "change": {"revenue_diff": 250000, "revenue_pct_change": 25.0},
    "monthly_comparison": [...],
    "category_impact": [...],
    "ai_commentary": "Analysis text..."
  }
  ```
- **Concerns:** Linear elasticity assumption (`discount_impact = current_revenue * (discount_change / 100) * 0.5`) is hardcoded and may not match domain business reality.

---

### 2.8 `GET /api/anomalies`
- **Location:** `backend/main.py` lines 1334–1336 (handled by `detect_anomalies` lines 1130–1191)
- **Purpose:** Identifies statistical outliers (> 2 standard deviations) across numerical features and month-over-month drops (< -15%).
- **Request:** Empty.
- **Response Schema:**
  ```json
  {
    "anomalies": ["revenue unusually high: 96,000 vs avg 32,000 (Electronics)"],
    "count": 1,
    "ai_analysis": [
      {
        "metric": "revenue",
        "description": "High spike in Electronics",
        "severity": "medium",
        "suggestion": "Verify order authenticity"
      }
    ]
  }
  ```
- **Concerns:** Hardcoded 2-sigma threshold; ignores data skew and multi-modal distributions.

---

## 3. Backward Compatibility Preservation Strategy

During the modular refactoring to `app/api/v1/routes/`:
1. All 8 route paths (`/api/health`, `/api/query`, `/api/upload`, `/api/profile`, `/api/deep-dive`, `/api/what-if`, `/api/anomalies`) must remain accessible at their exact URL paths.
2. In the Next.js frontend, `fetch(`${API}/api/query`)` will continue functioning without breaking changes.
3. Once authenticated sessions and dataset IDs are introduced in Phase 1, optional query parameters or headers (e.g., `X-Dataset-ID` or `Bearer <token>`) will be supported with graceful fallbacks.
