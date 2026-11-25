# INSLIGHT — Target Architecture Specification
**Document ID:** `AUDIT-DOC-09`
**Date of Audit:** November 2026
**Auditor:** Senior Software Architect & Backend Architect

---

## 1. Architectural Philosophy: The Well-Structured Modular Monolith

Inslight does not require complex distributed microservices, Kubernetes orchestrators, or heavy multi-agent frameworks (such as LangGraph or AutoGen) at its current stage of evolution. Introducing distributed microservices prematurely would create unnecessary operational complexity, distributed transaction overhead, network latency, and deployment friction.

Instead, the target architecture for Inslight is a **high-performance, well-structured Modular Monolith**:
- A single unified backend application with strict internal layer boundaries and dependency injection.
- A decoupled, componentized Next.js 14 frontend utilizing clean API client contracts.
- An analytical engine designed for high-concurrency tabular processing and tenant isolation.

---

## 2. Target Technology Stack Evaluation

Every technology in the target architecture must justify its presence by solving an explicit technical deficiency in the existing codebase:

### 2.1 Backend Framework: FastAPI (Retained & Modularized)
1. **Why required:** High-performance asynchronous Python web framework with native Pydantic data validation and OpenAPI generation.
2. **Problem it solves:** Retaining FastAPI leverages existing team Python expertise while allowing the refactoring of `backend/main.py` into clean APIRouters.
3. **When required:** Immediate (Phase 1).
4. **Can existing be retained:** Yes, retained and restructured into layered modules.

---

### 2.2 Relational Database: PostgreSQL + SQLAlchemy 2.0 + Alembic (New)
1. **Why required:** Production-grade relational database for user accounts, tenant permissions, dataset metadata, chat histories, and audit logs.
2. **Problem it solves:** Solves **SEC-01** (multi-tenant data leakage) and **DATA-01** (ephemeral in-memory data loss). Provides durable ACID transactions and row-level security.
3. **When required:** Immediate (Phase 1).
4. **Can existing be retained:** No. In-memory SQLite (`:memory:`) cannot support multi-user isolation or persistent data.

---

### 2.3 Analytical Engine: DuckDB / Parquet (New)
1. **Why required:** Columnar analytical database engine capable of querying Parquet files directly in milliseconds with zero network overhead.
2. **Problem it solves:** Replaces slow row-oriented SQLite queries and Pandas table locking. DuckDB provides vectorized aggregation (`SUM`, `AVG`, `GROUP BY`) on millions of rows while allowing per-tenant/per-dataset file isolation.
3. **When required:** Immediate (Phase 1).
4. **Can existing be retained:** No. Pandas `to_sql` into SQLite memory does not scale and lacks concurrency safety.

---

### 2.4 SQL Parsing & Validation: SQLGlot (New)
1. **Why required:** Industrial-strength SQL parser, transpiler, and Abstract Syntax Tree (AST) validator.
2. **Problem it solves:** Solves **SEC-03** (SQL injection and bypassable keyword blacklist). Inspects the AST of LLM-generated SQL, confirms statements are strictly `SELECT`, validates column existence against metadata, and blocks destructive DDL/DML.
3. **When required:** Immediate (Phase 1).
4. **Can existing be retained:** No. The current blacklist filter (`if "DROP" in upper`) is trivial to bypass.

---

### 2.5 Cache & Message Broker: Redis (Phase 1 / Phase 2)
1. **Why required:** In-memory key-value store for session caching, query result caching, API rate limiting, and async task queuing.
2. **Problem it solves:** Solves **SEC-06** (rate limiting) and prevents repetitive LLM calls for identical analytical queries.
3. **When required:** Phased. In-memory rate limiting in Phase 1; Redis broker in Phase 2 for async report generation.
4. **Can existing be retained:** Currently absent.

---

### 2.6 Background Task Worker: Celery or ARQ (Phase 2)
1. **Why required:** Offloads long-running tasks (heavy CSV parsing, PDF report generation, multilingual speech synthesis, email delivery) from HTTP request handlers.
2. **Problem it solves:** Solves **PERF-01** (event-loop blocking on uploads) and enables scheduled email reports without HTTP timeout risks.
3. **When required:** Phase 2 (Voice & Reports). In Phase 1, FastAPI's `BackgroundTasks` or `asyncio.to_thread` suffices for dataset ingestion.
4. **Can existing be retained:** Currently absent.

---

### 2.7 Frontend Framework: Next.js 14 App Router + Tailwind + Recharts (Retained & Refactored)
1. **Why required:** Modern React 18 framework with App Router, SSR/SSG capabilities, and fast UI hydration.
2. **Problem it solves:** Solves **ARCH-02** (1,082-line `page.tsx`), **FE-01** (runtime CSS injection), and **PERF-03** (keystroke re-rendering lag).
3. **When required:** Immediate (Phase 1).
4. **Can existing be retained:** Yes, the framework is retained, but the monolithic `page.tsx` is completely refactored into modular components.

---

## 3. High-Level Target System Architecture

```
                    ┌───────────────────────────────────────────────┐
                    │               Client Browser                  │
                    │        (Next.js 14 Modular App Router)        │
                    └───────────────────────┬───────────────────────┘
                                            │ HTTPS / WSS
                                            ▼
                    ┌───────────────────────────────────────────────┐
                    │               API Gateway / NGINX             │
                    │             (SSL, Rate Limit, CORS)           │
                    └───────────────────────┬───────────────────────┘
                                            │
                                            ▼
                    ┌───────────────────────────────────────────────┐
                    │             FastAPI Modular Monolith          │
                    │                                               │
                    │  ┌─────────────────┐   ┌───────────────────┐  │
                    │  │ Auth & Security │   │ Business Guard    │  │
                    │  │ (JWT / RBAC)    │   │ (Query Classifier)│  │
                    │  └────────┬────────┘   └─────────┬─────────┘  │
                    │           │                      │            │
                    │  ┌────────▼────────┐   ┌─────────▼─────────┐  │
                    │  │ SQLGlot Parser  │   │ AI Orchestrator   │  │
                    │  │ (AST Validator) │   │ (AsyncGroq / LLM) │  │
                    │  └────────┬────────┘   └─────────┬─────────┘  │
                    └───────────┼──────────────────────┼────────────┘
                                │                      │
                ┌───────────────┴────────┐             │
                ▼                        ▼             ▼
       ┌─────────────────┐      ┌─────────────────┐   ┌───────────────┐
       │   PostgreSQL    │      │ DuckDB Engine   │   │   External    │
       │  (Users, Auth,  │      │ (Per-Tenant     │   │   Groq API    │
       │   Chat, Meta)   │      │  Parquet Data)  │   │ (Llama-3.3-70B│
       └─────────────────┘      └─────────────────┘   └───────────────┘
                ▲
                │
       ┌────────┴────────┐
       │  Redis Cache &  │
       │   Task Broker   │
       └─────────────────┘
```

---

## 4. Proposed Modular Backend Folder Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                     # App factory, middleware, lifespan, router includes
│   │
│   ├── core/                       # Core system infrastructure
│   │   ├── __init__.py
│   │   ├── config.py               # Pydantic Settings (ENV variables, secrets)
│   │   ├── database.py             # PostgreSQL SQLAlchemy async engine & sessionmaker
│   │   ├── security.py             # JWT issuance, hashing, security dependencies
│   │   └── logging.py              # Structured JSON logging setup
│   │
│   ├── api/                        # HTTP presentation layer
│   │   ├── __init__.py
│   │   ├── deps.py                 # Dependency injection (DB session, current user)
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py           # Master v1 router aggregating route modules
│   │       └── routes/
│   │           ├── auth.py         # Login, register, token refresh
│   │           ├── health.py       # Liveness and readiness probes
│   │           ├── datasets.py     # Upload, list, delete, profile datasets
│   │           ├── query.py        # Natural language query execution
│   │           ├── deep_dive.py    # Deep dive analytical endpoints
│   │           ├── what_if.py      # Scenario modeling endpoints
│   │           └── anomalies.py    # Statistical outlier endpoints
│   │
│   ├── models/                     # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py                 # User and organization models
│   │   ├── dataset.py              # Dataset metadata and schema definitions
│   │   ├── chat_history.py         # Conversational threads and messages
│   │   └── audit_log.py            # User action auditing
│   │
│   ├── schemas/                    # Pydantic DTO models
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── dataset.py
│   │   ├── query.py
│   │   └── analytics.py
│   │
│   ├── services/                   # Business logic and AI orchestration
│   │   ├── __init__.py
│   │   ├── ai_service.py           # AsyncGroq API client wrapper
│   │   ├── business_guard.py       # Business Context Guard & query intent classification
│   │   ├── sql_service.py          # SQL generation and SQLGlot AST validation
│   │   ├── dataset_service.py      # Ingestion, profiling, Parquet transformation
│   │   └── prompts/                # Dedicated prompt templates
│   │       ├── __init__.py
│   │       ├── sql_templates.py
│   │       ├── chart_templates.py
│   │       └── narrative_templates.py
│   │
│   ├── analytics/                  # Algorithmic calculation engines
│   │   ├── __init__.py
│   │   ├── anomaly_detector.py     # Multi-variate outlier detection
│   │   ├── scenario_engine.py      # What-if elasticity and impact modeling
│   │   └── root_cause_engine.py    # Contribution and variance analysis
│   │
│   ├── repositories/               # Data access layer
│   │   ├── __init__.py
│   │   ├── base.py                 # Generic CRUD repository
│   │   ├── user_repository.py      # User persistence
│   │   └── dataset_repository.py   # DuckDB analytical query execution
│   │
│   └── utils/                      # Common utilities
│       ├── __init__.py
│       ├── csv_reader.py           # Multi-encoding CSV streaming reader
│       └── formatters.py           # Metric formatting utilities
│
├── alembic/                        # Database migration scripts
│   ├── env.py
│   └── versions/
│
├── tests/                          # Automated tests
│   ├── conftest.py
│   ├── unit/
│   └── integration/
│
├── Dockerfile
├── requirements.txt
└── runtime.txt
```
