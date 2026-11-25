# INSLIGHT — Four-Phase Implementation Roadmap
**Document ID:** `AUDIT-DOC-10`
**Date of Audit:** November 2026
**Auditor:** Senior Software Architect & Engineering Review Board

---

## Roadmap Overview

To transform Inslight from an early-stage hackathon prototype into a resilient, production-grade AI Business Intelligence platform, engineering efforts are structured across four disciplined development phases.

```
┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: Secure Foundation, Modularization & AI Intelligence (Core)    │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: Voice Assistant & Automated Reporting Automation               │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: Advanced Business Intelligence & Root Cause Engine             │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 4: Enterprise Hardening, CI/CD, Observability & Deployment        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Secure Foundation, Modularization & AI Intelligence

### 1.1 Objectives & Deliverables
- Establish strong authentication, authorization, and tenant dataset isolation.
- Refactor monolithic `backend/main.py` into a modular, production-grade FastAPI architecture.
- Refactor monolithic `frontend/src/app/page.tsx` into modular feature components and eliminate runtime CSS injection.
- Replace volatile in-memory SQLite with PostgreSQL (metadata) and DuckDB (columnar analytical execution).
- Introduce **AI Business Context Guard**, AST SQL validation via `sqlglot`, and conversational chat history.

### 1.2 Detailed Task Breakdown
1. **Security & Data Isolation:**
   - Implement JWT Bearer token authentication with password hashing (`argon2` or `bcrypt`).
   - Create PostgreSQL schemas for `User`, `Tenant`, `Dataset`, and `ChatHistory`.
   - Implement dataset storage isolation: assign each dataset a UUID and store as isolated Parquet files.
2. **Backend Modularization:**
   - Break `main.py` into `app/core/`, `app/api/v1/routes/`, `app/services/`, `app/schemas/`, and `app/repositories/`.
   - Wrap Groq interactions in `AsyncGroq` client with parallelized `asyncio.gather()` execution.
   - Enforce SQLGlot AST validation on all generated SQL queries, blocking non-`SELECT` statements.
3. **AI Business Context Guard:**
   - Introduce pre-execution intent classification: reject out-of-scope or non-analytical queries before firing SQL generation.
   - Implement hallucination prevention: map prompt schema exclusively from verified dataset metadata.
4. **Frontend Modularization:**
   - Split `page.tsx` into feature folders (`features/chat`, `features/analytics`, `features/what-if`).
   - Eliminate `injectStyles()`; migrate all styling to Tailwind CSS classes.
   - Replace hand-rolled SVGs with Recharts; replace emojis with Lucide React icons.
   - Localize chat input and slider state to prevent full-page re-renders.

### 1.3 Reusable Assets from Existing Codebase
- Safe CSV reader encoding detection logic (`read_csv_safe`).
- Column normalization and derived column heuristics (`total_revenue`, `discount_pct`).
- Proven Groq prompts (`SQL_PROMPT`, `CHART_PROMPT`, `STORY_PROMPT`), wrapped into Jinja2 templates.
- Metric formatting utilities (`format_val`).

### 1.4 Risks & Mitigation
- *Risk:* Latency during large CSV uploads.
- *Mitigation:* Offload CSV parsing to thread pool (`asyncio.to_thread`) with chunked streaming.

### 1.5 Phase 1 Acceptance Criteria
- [ ] No global database singletons remain.
- [ ] User A cannot access or overwrite User B's dataset.
- [ ] Backend is fully modularized with zero circular imports.
- [ ] Next.js frontend has `strict: true` type checking and zero runtime CSS injection.
- [ ] Every generated SQL query passes SQLGlot AST validation before execution.
- [ ] Automated unit test suite reaches minimum 80% coverage on core services.

---

## Phase 2: Voice Assistant & Automated Reporting Automation

### 2.1 Objectives & Deliverables
- Implement browser-based voice input and speech-to-text (STT) assistant.
- Implement multilingual voice recognition and audio feedback.
- Build PDF and Excel analytical export engines.
- Integrate automated email distribution (Gmail API / SMTP) with report history.

### 2.2 Detailed Task Breakdown
1. **Voice Assistant Integration:**
   - Integrate Web Speech API in Next.js frontend with fallback to backend Whisper / Groq Whisper API for high-fidelity multilingual audio transcription.
   - Provide visual voice waveform indicator and microphone permission management.
2. **Automated Export Engines:**
   - Build high-resolution PDF report generator using `WeasyPrint` or `Puppeteer`, capturing KPI cards, charts, and executive insights.
   - Build Excel report generator using `OpenPyXL` / `xlsxwriter` with styled multi-tab workbooks (Raw Data, Summary, Pivot).
3. **Distribution & Delivery Automation:**
   - Implement asynchronous email delivery via background workers.
   - Require explicit user confirmation modal before sending external emails.
   - Store historical generated reports with secure download tokens in PostgreSQL.

### 2.3 Reusable Assets from Existing Codebase
- Query result schemas and chart configurations from Phase 1.
- Analytical aggregation logic from `generate_deep_dive` and `run_whatif`.

### 2.4 Risks & Mitigation
- *Risk:* Heavy PDF generation causing HTTP request timeouts.
- *Mitigation:* Asynchronous job queue (Redis + ARQ/Celery) returning job ID with status polling/WebSocket updates.

### 2.5 Phase 2 Acceptance Criteria
- [ ] Voice queries are accurately transcribed and routed through the query pipeline.
- [ ] Users can download pixel-perfect PDF and multi-tab Excel reports.
- [ ] Email reports require explicit user approval and execute asynchronously.

---

## Phase 3: Advanced AI Business Intelligence

### 3.1 Objectives & Deliverables
- Deploy Autonomous AI Business Intelligence Agent.
- Implement Root Cause Analysis (RCA) engine with variance decomposition.
- Introduce time-series predictive forecasting models.
- Build interactive custom Dashboard Builder with drag-and-drop widgets.
- Multi-dataset relationship detection and cross-dataset joins.

### 3.2 Detailed Task Breakdown
1. **AI BI Agent:**
   - Multi-step reasoning agent that formulates iterative hypotheses, executes multiple analytical sub-queries, and synthesizes strategic takeaways.
2. **Root Cause Analysis (RCA) Engine:**
   - Algorithmic contribution analysis: decomposes revenue/profit changes across dimensions (region, category, salesperson) using Waterfall calculations.
3. **Predictive Analytics & Forecasting:**
   - Time-series forecasting (Prophet or ARIMA/Exponential Smoothing) projecting future revenue, demand, and margin trends with confidence intervals.
4. **Data Quality & Hygiene Assistant:**
   - Advanced profiling detecting missing values, duplicate entries, data drift, and schema discrepancies with automated remediation suggestions.
5. **Dynamic Dashboard Builder:**
   - Allow users to pin charts, customize layouts, and save personalized executive dashboards.

### 3.3 Phase 3 Acceptance Criteria
- [ ] AI Agent generates multi-turn investigative hypotheses and verifies them against data.
- [ ] Root cause decomposition explains 100% of metric variance mathematically.
- [ ] Forecasting models render confidence bounds on time-series charts.

---

## Phase 4: Production, Enterprise & Deployment

### 4.1 Objectives & Deliverables
- Enterprise security hardening, audit logging, and compliance readiness.
- PowerPoint (PPTX) presentation generator for executive decks.
- Automated CI/CD pipelines, containerization, and deployment orchestration.
- Comprehensive observability, distributed tracing, and automated backup strategies.

### 4.2 Detailed Task Breakdown
1. **Enterprise Hardening & Auditing:**
   - Implement immutable audit logs capturing every user query, export, and dataset access.
   - Enforce fine-grained Role-Based Access Control (RBAC: Admin, Analyst, Viewer).
2. **Executive PowerPoint Generation:**
   - Build PPTX export service using `python-pptx`, generating branded slide decks containing executive summaries, KPI tables, and rendered charts.
3. **Observability & Monitoring:**
   - Integrate structured JSON logging with correlation IDs.
   - Prometheus metrics for query latency, LLM token consumption, and error rates; Grafana dashboards.
   - Sentry integration for real-time exception tracking.
4. **DevOps & Production Deployment:**
   - Multi-stage Docker containerization for Next.js frontend and FastAPI backend.
   - GitHub Actions CI/CD pipeline running linting, type checks, unit tests, and security scans.
   - Automated database backups and recovery drills.

### 4.3 Phase 4 Acceptance Criteria
- [ ] Enterprise audit logs satisfy security compliance criteria.
- [ ] Full CI/CD pipeline builds and passes tests on every pull request.
- [ ] Zero critical vulnerabilities detected in automated container vulnerability scans.
