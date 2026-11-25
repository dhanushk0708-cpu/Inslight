# INSLIGHT — College Project Report & Viva Preparation Guide
## AI-Powered Business Intelligence Platform (BCA AI & ML Final-Year Project)

---

### 1. Project Abstract
**INSLIGHT** is a full-stack, multi-tenant AI Business Intelligence platform that enables business users and analysts to upload tabular CSV datasets, ask natural-language questions (via text or multilingual voice), perform automated Root Cause Analysis, generate machine-learning time-series forecasts, detect anomalies, build interactive dashboards, and export executive PDF, Excel, and PowerPoint (`.pptx`) reports. Unlike naive LLM chat wrappers, INSLIGHT grounds every statistic in deterministic DuckDB SQL and scikit-learn computations, enforces strict SQL AST security via SQLGlot, and isolates user data per tenant.

---

### 2. Problem Statement
Small and medium businesses generate operational CSV/tabular data but lack dedicated data engineering teams. Traditional BI tools require manual SQL/dashboard authoring, while generic AI chatbots hallucinate numbers, leak data across users, or execute unsafe SQL.

---

### 3. Objectives
1. Provide secure, multi-tenant authentication with Role-Based Access Control (`admin` and `analyst`).
2. Translate natural-language business questions into safe, AST-validated DuckDB SQL queries.
3. Combine deterministic analytics, ML forecasting, and anomaly detection inside a tool-based AI BI Agent.
4. Support multilingual voice input (English, Hindi, Kannada) and automated PDF/Excel/PowerPoint reporting.
5. Ensure production readiness with notifications, audit logging, rate limiting, health probes, Alembic migrations, and CI/CD.

---

### 4. Existing System vs. Proposed System
- **Existing System:** Manual spreadsheets, static BI dashboards, or ungrounded LLM wrappers prone to numeric hallucinations and SQL injection.
- **Proposed System (INSLIGHT):** Automated schema profiling + RAG schema grounding + 2-layer Business Context Guard + SQLGlot AST validation + isolated per-user DuckDB storage + scikit-learn ML forecasting/anomalies + automated PDF/Excel/PPTX reporting + RBAC & audit logging.

---

### 5. System Architecture & Technology Stack
- **Frontend:** Next.js 14 (App Router), React, TypeScript, custom dark-neon UI (`frontend/`).
- **Backend:** FastAPI, Python 3.11, Pydantic v2, Uvicorn.
- **Relational DB & Migrations:** SQLite (local demo) / PostgreSQL (production), SQLAlchemy 2.0, Alembic (`2604d90ecb63`).
- **Analytical Engine:** DuckDB (isolated `.duckdb` file per dataset), Pandas, NumPy.
- **AI & ML:** Groq API (`openai/gpt-oss-120b`), `scikit-learn` (Random Forest, Ridge Regression, Isolation Forest), SQLGlot (AST SQL validator).
- **Reporting & Visualization:** ReportLab (PDF), `openpyxl` (Excel), `python-pptx` (PowerPoint), Matplotlib.
- **Security:** `bcrypt` password hashing, PyJWT (`HS256`), `cryptography.fernet` OAuth token encryption, sliding-window rate limiter.
- **CI/CD:** GitHub Actions (`.github/workflows/ci.yml`).

---

### 6. Database Design
13 SQLAlchemy tables managed via Alembic:
`users` (with `role`), `datasets`, `chat_sessions`, `chat_messages`, `reports`, `scheduled_reports`, `oauth_credentials`, `alerts`, `alert_rules`, `saved_dashboards`, `dataset_relationships`, `notifications`, `audit_logs`, `presentations`.

---

### 7. Core AI, ML & Security Pipelines
- **RAG Implementation:** `RAGService` extracts exact column names, inferred semantic types (numeric, date, categorical, identifier), sample values, and summary statistics from the user's active dataset to ground LLM SQL prompts.
- **Business Context Guard:** Layer 1 deterministic regex allow/block list + Layer 2 LLM JSON intent classifier rejecting off-topic questions.
- **AI BI Agent Workflow:** Classifies intent across Strategic Performance & Opportunities/Risks, Root Cause Analysis, ML Forecasting, Anomaly Detection, Comparative Analytics, and SQL fallback (auto-upgrading unconfident SQL to Strategic Analysis).
- **SQL Security:** `SQLService.validate_sql` parses generated SQL with `sqlglot`, enforcing single-statement `SELECT`-only AST, blocking DDL/DML/file-read functions, and checking table/column allowlists.
- **Forecasting & Anomaly Detection:** Evaluates Moving Average, Holt's Linear Exponential Smoothing, Ridge Linear Regression, and Random Forest using backtest MAE/RMSE/MAPE and 95% confidence bounds; detects anomalies with Z-Score, IQR, and Isolation Forest.
- **Voice Assistant & Reporting:** Browser Web Speech API (`en-IN`, `hi-IN`, `kn-IN`) + `speechSynthesis`; ReportLab PDF, openpyxl Excel (formula-injection sanitized), `python-pptx` PowerPoint, Gmail OAuth2, and UTC background scheduler.

---

### 8. Testing, Deployment & Future Enhancements
- **Testing Strategy:** 55 automated `pytest` unit/integration/security tests, `npx tsc --noEmit`, `next build`, and Alembic migration verification.
- **Deployment Architecture:** Next.js frontend + FastAPI backend behind HTTPS reverse proxy + PostgreSQL + persistent volume for `.duckdb` and exported reports.
- **Future Enhancements:** Live PostgreSQL multi-tenant connection pooling, Redis-backed distributed rate limiting, custom per-user timezone cron expressions for scheduled reports, and interactive drill-down dashboard filters.
