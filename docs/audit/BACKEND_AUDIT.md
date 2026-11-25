# INSLIGHT — Technical Audit: FastAPI Backend
**Document ID:** `AUDIT-DOC-03`
**Target:** `backend/` (`main.py`, `requirements.txt`, `data/`)
**Date of Audit:** November 2026
**Auditor:** Backend Architect & Senior Python Engineer

---

## 1. Existing Implementation Overview

The backend is implemented as a single Python file, `backend/main.py` (1,342 lines, 51.7 KB), supported by `requirements.txt` and a seed CSV dataset at `backend/data/sample_sales.csv`.

```
backend/
├── .env
├── main.py                    # 1,342-line monolithic file
├── requirements.txt
├── runtime.txt
└── data/
    └── sample_sales.csv
```

### Core Components Identified in `main.py`:
1. **Pydantic Schemas (lines 27–36):**
   - `QueryRequest`: Defines `question: str` and `conversation_history: Optional[List[Dict[str, str]]] = []`.
   - `WhatIfRequest`: Defines `price_change: float = 0.0`, `discount_change: float = 0.0`, `units_change: float = 0.0`.
2. **Safe CSV Reader (`read_csv_safe`, lines 42–69):**
   - Cycles through encodings (`utf-8`, `utf-8-sig`, `cp1252`, `latin-1`, `iso-8859-1`, `ascii`) to read uploaded CSV files into Pandas.
3. **Database Manager (`DatabaseManager`, lines 75–344):**
   - Encapsulates an in-memory SQLite connection (`sqlite3.connect(":memory:", check_same_thread=False)`).
   - Manages data ingestion, column normalization, date parsing, numeric coercion, calculated column derivations (`total_revenue`, `discount_amount`, `discount_pct`), index creation, alias building, and SQL execution.
4. **LLM Connector (`LLM`, lines 350–383):**
   - Implements raw HTTP POST calls via `requests` to Groq (`https://api.groq.com/openai/v1/chat/completions`) using model `llama-3.3-70b-versatile`.
5. **Prompt Templates (lines 390–486):**
   - Hardcoded prompt strings: `SQL_PROMPT`, `SQL_FIX_PROMPT`, `CHART_PROMPT`, `STORY_PROMPT`, `SUGGEST_PROMPT`, `PROFILE_PROMPT`, `DEEP_DIVE_PROMPT`, `WHATIF_PROMPT`, `ANOMALY_PROMPT`.
6. **Execution & Analytics Pipelines (lines 492–1250):**
   - Helpers: `parse_json`, `clean_sql`, `format_val`, `error_response`.
   - `build_fallback_query`: 150 lines of keyword-matching fallback SQL heuristics.
   - `smart_execute`: SQL execution with retry loop and dangerous keyword checks.
   - `process_query`: 5-step conversational query pipeline.
   - `generate_deep_dive`: Multi-aggregation deep dive pipeline.
   - `run_whatif`: Formulaic scenario modeling with LLM commentary.
   - `detect_anomalies`: Z-score statistical anomaly detection.
   - `profile_data`: Dataset profiling, quality score calculation, and sample generation.
7. **FastAPI Application & Endpoints (lines 1256–1338):**
   - App initialization, CORS middleware, lifespan startup handler, and 8 API routes.

---

## 2. Backend Code Quality & Architectural Flaws

### 2.1 Global Mutable Singletons & Concurrency Hazards
- At line 343: `db = DatabaseManager()` is instantiated as a module-level global variable.
- At line 383: `llm = LLM()` is instantiated as a module-level global variable.
- **Race Conditions:**
  - The in-memory SQLite connection is created with `check_same_thread=False`.
  - In Python's standard `sqlite3` module, sharing a single connection across multiple OS threads (which FastAPI utilizes via `anyio.to_thread.run_sync` for synchronous `def` endpoints) leads to thread safety violations, cursor interleaving, and `sqlite3.ProgrammingError: Recursive use of cursors not allowed`.
  - When two requests are executed simultaneously, cursor operations collide, yielding corrupted results or internal server crashes.

### 2.2 Blocking Operations inside Async Endpoints
- The endpoint `/api/upload` is declared as:
  ```python
  @app.post("/api/upload")
  async def upload(file: UploadFile = File(...)):
      content = await file.read()
      db.load_bytes(content, file.filename)
  ```
- `db.load_bytes()` executes synchronous, CPU-bound Pandas transformations, encoding detection loops, and SQLite schema writes directly within the asyncio event loop thread.
- **Impact:** During large CSV uploads (up to 100MB), the entire FastAPI event loop is blocked. All concurrent requests to `/api/health`, `/api/query`, or other routes freeze until the upload finishes processing.

### 2.3 Synchronous Blocking Network I/O in LLM Calls
- `LLM.chat()` uses the blocking `requests` library:
  ```python
  r = requests.post(self.url, headers=..., json=..., timeout=30)
  ```
- Because `process_query` makes up to 4 sequential LLM calls, a single query blocks an ASGI worker thread for 2–10 seconds.
- Under modest concurrency (5–10 simultaneous users), the thread pool becomes exhausted, leading to request queuing and HTTP 504 timeouts.

### 2.4 Lack of Layered Abstraction
- Database access, AI orchestration, data cleaning, business logic, and HTTP presentation are inextricably coupled inside single functions.
- For example, `process_query()` directly manipulates SQLite connections, invokes HTTP requests to Groq, constructs Pandas DataFrames, calculates mathematical aggregates, and formats HTTP presentation JSON.
- Testing any individual component in isolation without spinning up SQLite and Groq is currently impossible.

### 2.5 Inadequate Validation & Error Masking
- The SQL fallback mechanism (`build_fallback_query`) silently intercepts failed LLM queries or invalid schemas and executes a generic keyword-guessed query.
- The user is not informed that their specific question failed to be interpreted by the AI; instead, they receive data from an arbitrary fallback query (e.g., top categories by total revenue).
- This introduces severe silent data inaccuracies in decision-making.

---

## 3. Function-by-Function Target Relocation Mapping

To refactor `backend/main.py` into a production-grade, maintainable architecture, every existing function and class must be relocated as follows:

| Existing Symbol / Function | Lines in `main.py` | Target Modular Module | Responsibility |
|---|---|---|---|
| `QueryRequest`, `WhatIfRequest` | 27–36 | `app/schemas/analytics.py` | Pydantic DTO request models with field validation |
| `read_csv_safe` | 42–69 | `app/utils/csv_reader.py` | Resilient encoding detection and file reading |
| `DatabaseManager` | 75–344 | `app/repositories/dataset_repository.py` & `app/core/database.py` | Dataset persistence, schema management, and connection pool |
| `LLM` class | 350–383 | `app/services/ai_service.py` | Asynchronous LLM client (using official Groq / httpx client) |
| Prompt strings (`SQL_PROMPT`, etc.) | 390–486 | `app/services/prompts/` | Versioned prompt templates and Jinja2 formats |
| `parse_json` | 492–500 | `app/utils/helpers.py` | Robust markdown/JSON block extraction |
| `clean_sql` | 502–509 | `app/utils/sql_cleaner.py` | SQL markdown stripping and AST normalization |
| `format_val` | 512–530 | `app/utils/formatters.py` | Metric formatting (currency, percent, numbers) |
| `error_response` | 532–545 | `app/schemas/responses.py` | Standardized API error payload builder |
| `build_fallback_query` | 547–706 | `app/services/sql_fallback_service.py` | Rule-based SQL query builder |
| `smart_execute` | 712–768 | `app/services/sql_service.py` | Query validation, execution, and self-healing retries |
| `process_query` | 774–987 | `app/services/query_orchestrator.py` | Multi-step query, chart, and story pipeline |
| `generate_deep_dive` | 993–1052 | `app/analytics/deep_dive.py` | Deep dive metric aggregation and LLM analysis |
| `run_whatif` | 1058–1124 | `app/analytics/what_if.py` | Mathematical scenario simulation and forecasting |
| `detect_anomalies` | 1130–1191 | `app/analytics/anomaly_detection.py` | Statistical outlier calculations and insight generation |
| `profile_data` | 1197–1250 | `app/services/dataset_service.py` | Schema inspection, null analysis, quality scoring |
| FastAPI app, CORS, routes | 1256–1338 | `app/main.py` & `app/api/v1/routes/*.py` | Routing, middleware, dependency injection |

---

## 4. Recommended Modular FastAPI Architecture

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application factory, middleware, router mounts
│   │
│   ├── core/                       # Core infrastructure configuration
│   │   ├── __init__.py
│   │   ├── config.py               # Pydantic BaseSettings for environment variables
│   │   ├── database.py             # Database engine, session maker, connection lifecycle
│   │   ├── security.py             # Auth dependencies, JWT validation, API key guards
│   │   └── logging.py              # Structured JSON logging configuration
│   │
│   ├── api/                        # HTTP API presentation layer
│   │   ├── __init__.py
│   │   ├── deps.py                 # Dependency injection (DB session, current user, AI client)
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py           # Master v1 API router
│   │       └── routes/
│   │           ├── health.py       # Health check and engine status
│   │           ├── datasets.py     # File upload, profiling, dataset listing
│   │           ├── query.py        # Natural language query pipeline
│   │           ├── deep_dive.py    # Deep dive business analysis
│   │           ├── what_if.py      # Scenario modeling
│   │           └── anomalies.py    # Anomaly detection endpoints
│   │
│   ├── schemas/                    # Pydantic validation schemas (DTOs)
│   │   ├── __init__.py
│   │   ├── common.py               # Standard response wrappers, pagination, errors
│   │   ├── dataset.py              # Upload responses, profile schemas
│   │   ├── query.py                # Query requests, KPI card, chart configurations
│   │   └── analytics.py            # What-if, deep-dive, anomaly schemas
│   │
│   ├── services/                   # Business logic and external orchestrations
│   │   ├── __init__.py
│   │   ├── ai_service.py           # Asynchronous LLM interactions (Groq client)
│   │   ├── query_orchestrator.py   # Multi-step query coordination
│   │   ├── sql_service.py          # SQLGlot AST parsing, validation, safe execution
│   │   ├── dataset_service.py      # Dataframe transformations and profiling
│   │   └── prompts/                # Dedicated prompt management
│   │       ├── __init__.py
│   │       ├── sql_prompts.py
│   │       ├── chart_prompts.py
│   │       └── insight_prompts.py
│   │
│   ├── analytics/                  # Specialized analytical computation engines
│   │   ├── __init__.py
│   │   ├── anomaly_detection.py    # Z-score and trend outlier detection
│   │   ├── scenario_simulator.py   # What-if sensitivity modeling
│   │   └── root_cause.py           # Driver and risk ranking
│   │
│   ├── repositories/               # Data access layer
│   │   ├── __init__.py
│   │   ├── base.py                 # Generic repository pattern
│   │   └── dataset_repository.py   # Dataset metadata and tabular query execution
│   │
│   └── utils/                      # Helper utilities
│       ├── __init__.py
│       ├── csv_reader.py           # Safe CSV reader with encoding heuristics
│       ├── formatters.py           # Currency and number formatting
│       └── helpers.py              # JSON parsing and string utilities
│
├── tests/                          # Automated test suite
│   ├── conftest.py
│   ├── unit/
│   └── integration/
│
├── requirements.txt
└── runtime.txt
```
