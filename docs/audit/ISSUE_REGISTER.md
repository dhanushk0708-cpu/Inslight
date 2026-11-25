# INSLIGHT — Comprehensive Issue Register
**Document ID:** `AUDIT-DOC-08`
**Date of Audit:** November 2026
**Auditor:** Senior Software Architect & Engineering Review Board

---

## Issue Classification Legend
- **CRITICAL:** Security vulnerability, multi-tenant data leakage, major data corruption, or application-breaking flaw.
- **HIGH:** Major architectural, reliability, performance, or functionality failure.
- **MEDIUM:** Maintainability, code organization, usability, or minor performance degradation.
- **LOW:** Code cleanliness, style inconsistency, or minor cosmetic improvement.

---

## Master Issue Table

| ID | Category | Problem | File/Location | Severity | Impact | Recommended Solution |
|---|---|---|---|---|---|---|
| **SEC-01** | Data Isolation | Global in-memory SQLite singleton shares data across all users; uploads overwrite active database | `backend/main.py:75-80, 103-112, 343` | **CRITICAL** | Severe data leakage; User B views User A's data; concurrent uploads destroy user state | Implement user/tenant authentication; isolate datasets via tenant-scoped DuckDB/Parquet or PostgreSQL schemas |
| **SEC-02** | Authentication | Complete absence of authentication, authorization, or role-based access control | `backend/main.py:1256-1338` | **CRITICAL** | All API endpoints and analytical datasets are publicly accessible without verification | Implement JWT bearer token authentication, user entity models, and FastAPI dependency guards |
| **SEC-03** | Security | Naive blacklist SQL validation and unparameterized string formatting in DDL and queries | `backend/main.py:221-226, 313-316, 719-722` | **HIGH** | SQL injection via crafted CSV headers or malicious filenames; blacklist bypass | Parse generated SQL using SQLGlot AST; enforce read-only `SELECT` queries; sanitize identifiers |
| **SEC-04** | Security | Insecure CORS configuration (`allow_origins=["*"]` with `allow_credentials=True`) | `backend/main.py:1263-1269` | **HIGH** | Rejection by modern browsers or exposure to cross-origin credentialed attacks | Replace wildcard origin with explicit origin whitelist configured via environment variables |
| **SEC-05** | Security | Unbounded CSV upload memory buffering and file extension-only validation | `backend/main.py:1294-1300` | **HIGH** | Out-of-memory DoS on large/concurrent uploads; potential upload of non-CSV files | Stream file chunks to temporary disk storage; enforce strict MIME type and magic byte verification |
| **SEC-06** | Security | Total lack of API rate limiting on expensive LLM-backed routes | `backend/main.py:1288-1291` | **HIGH** | Financial DoS, quota exhaustion, and denial of service via rapid API spam | Introduce Redis-backed or in-process token-bucket rate limiting (e.g., `slowapi`) |
| **ARCH-01** | Architecture | Monolithic backend: 1,342 lines in a single file combining routes, DB, AI, and business logic | `backend/main.py:1-1342` | **HIGH** | Extreme technical debt; tightly coupled components; impossible to test in isolation | Restructure into modular FastAPI layered architecture (`app/core`, `app/api`, `app/services`, `app/repositories`) |
| **ARCH-02** | Architecture | Monolithic frontend: 1,082 lines in a single `page.tsx` file with inline styles | `frontend/src/app/page.tsx:1-1082` | **HIGH** | Maintainability nightmare; massive bundle; high re-rendering overhead | Decompose into modular feature components (`features/chat`, `features/analytics`, `features/what-if`) |
| **PERF-01** | Performance | Synchronous, CPU-bound Pandas processing executed directly inside async FastAPI route | `backend/main.py:1294-1309` | **HIGH** | Freezes asyncio event loop for all concurrent users during CSV upload and parsing | Execute CPU-heavy parsing in thread pool (`asyncio.to_thread`) or background task worker (Celery/ARQ) |
| **PERF-02** | Performance | Sequential execution of 4 separate LLM inference calls inside `/api/query` | `backend/main.py:788-878` | **HIGH** | 2.5s–6.0s query latency; terrible user experience | Run independent chart, narrative, and suggestion LLM tasks in parallel via `asyncio.gather()` |
| **PERF-03** | Performance | Root component state in Next.js triggers full page & SVG re-render on every keystroke | `frontend/src/app/page.tsx:656-673` | **HIGH** | Severe UI input lag; unnecessary SVG coordinate and DOM recalculations | Move chat input and slider states into local component scopes; memoize charts with `React.memo` |
| **CONC-01** | Concurrency | SQLite `:memory:` connection shared across worker threads without synchronization locks | `backend/main.py:77, 343` | **HIGH** | `sqlite3.ProgrammingError: Recursive use of cursors` or memory corruption under concurrency | Use connection pooling and per-request/per-session isolated database handles |
| **DATA-01** | Data Persistence | Ephemeral in-memory database provides zero data durability; all data lost on restart | `backend/main.py:77-80` | **HIGH** | Complete loss of user uploads upon server reboot or worker recycling | Store uploaded datasets as persistent Parquet files; store metadata in persistent PostgreSQL |
| **AI-01** | AI / RAG | Missing AI Business Context Guard; out-of-scope questions waste tokens or generate broken SQL | `backend/main.py:774-802` | **HIGH** | Inaccurate answers; hallucinations; unnecessary Groq API cost on non-data questions | Implement an Intent Classifier / Business Context Guard to reject or route out-of-scope queries |
| **AI-02** | AI / Reliability | Silent SQL fallback query mask: failed AI queries silently return unrelated generic data | `backend/main.py:716-744, 808-816` | **HIGH** | Misleading business metrics; executive decisions based on unrelated fallback data | Explicitly notify user of SQL generation failure; propose suggested query formulations |
| **AI-03** | AI / Architecture | Groq SDK installed in virtualenv but bypassed in code via synchronous `requests.post` | `backend/main.py:11, 350-381` | **MEDIUM** | Missing async HTTP/2 connection pooling, streaming, and automatic exponential backoff | Migrate to official `AsyncGroq` client library with connection pooling and async streaming |
| **FE-01** | Frontend | Runtime CSS injection via `injectStyles()` creates FOUC and bypasses Next.js CSS pipeline | `frontend/src/app/page.tsx:9-525` | **MEDIUM** | Layout shifts; bypassed CSS optimization; unmaintainable 500-line CSS string in JS | Migrate inline CSS to standard Tailwind utility classes and modular CSS stylesheets |
| **FE-02** | Frontend | Installed dependencies (`recharts`, `lucide-react`, `react-dropzone`) completely unused | `frontend/package.json:8`, `page.tsx` | **MEDIUM** | Bloated `node_modules` (>10MB); custom hand-rolled SVGs lack responsiveness and accessibility | Replace handcrafted SVG charts with Recharts components; replace emojis with Lucide icons |
| **FE-03** | Frontend / Type | Loose TypeScript compiler configuration (`strict: false`); untyped component props | `frontend/tsconfig.json:10`, `page.tsx` | **MEDIUM** | Runtime `undefined` errors; unvalidated API contract mismatches | Enable `strict: true` in `tsconfig.json`; define TypeScript interfaces for all DTOs and props |
| **FE-04** | Feature Discrepancy| Voice query capability claimed in README is completely missing from Next.js frontend | `README.md:42-45`, `frontend/src/app/page.tsx` | **MEDIUM** | Feature absence; broken documentation promise | Implement Web Speech API / Whisper STT voice recording interface in Phase 2 roadmap |
| **TEST-01** | Testing & QA | Total absence of automated test suites (unit, integration, API, or frontend tests) | Project-wide | **HIGH** | High risk of regression during refactoring; no verification of analytical correctness | Establish `pytest` test suite for backend services and `vitest` / React Testing Library for frontend |
| **OPS-01** | DevOps | Missing Docker containerization, CI/CD pipeline, and structured JSON logging | Project-wide | **MEDIUM** | Inconsistent environment setups; manual deployment risks; unmonitored production errors | Create multi-stage `Dockerfile`, GitHub Actions CI pipeline, and structured Python logging |
