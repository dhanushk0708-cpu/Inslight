# INSLIGHT — Phase 1 Final Independent Verification Report
**Date:** November 24, 2026
**Auditor Roles:** Senior QA Engineer, Application Security Engineer, Full-Stack Architect
**Project:** INSLIGHT — AI-Powered Business Intelligence Platform (Final-Year BCA AI & ML Project)
**Status:** **PHASE 1 VERIFIED & APPROVED FOR PHASE 2**

---

## Executive Summary

An exhaustive, independent verification and defect remediation of the **Phase 1: Secure Foundation, Architecture Restructuring & AI Intelligence** implementation was conducted. The audit tested the live codebase, executed automated security and regression test suites, confirmed data isolation boundaries, and performed static analysis and production compilation.

All confirmed defects—specifically an authentication bypass risk via `get_optional_current_user`, silent dataset fallback on cross-user queries, and chat session hijacking vulnerability—have been remediated and rigorously verified. The backend test suite achieves **100% pass rate (20/20 tests)**, and the Next.js frontend compiles cleanly across all routes with zero errors.

---

## 1. Compliance with Strict Restrictions

| Restriction | Audit Finding | Compliance Status |
| :--- | :--- | :---: |
| **`frontend-react/` Untouched** | Verified via Git status. No source files modified, renamed, moved, or deleted. | **COMPLIANT** |
| **Preserve Existing Functionality** | All original features (KPI cards, charts, deep-dive, what-if, anomalies, CSV upload) preserved and operational. | **COMPLIANT** |
| **No Phase 2 Features Introduced** | Voice assistant, automated PDF/Excel reports, and Gmail integrations were not introduced. | **COMPLIANT** |
| **No Destructive Database Ops** | Safe migrations and table definitions retained; no data corruption. | **COMPLIANT** |
| **No Mock Data Replacement** | Real DuckDB engine, real SQLGlot AST validation, real AI service prompts retained. | **COMPLIANT** |

---

## 2. Authentication & Security Audit

### 2.1 Endpoint Authentication Verification
Every backend route was audited to ensure proper dependency injection and token requirement:

| Endpoint | Method | Previous Dependency | Remediated Dependency | Unauthenticated Result |
| :--- | :---: | :--- | :--- | :---: |
| `/api/v1/auth/register` | `POST` | Public | Public | `201 Created` |
| `/api/v1/auth/login` | `POST` | Public | Public | `200 OK` / `401 Unauthorized` |
| `/api/v1/health` | `GET` | `get_optional_current_user` | **Public (Zero Metadata Leak)** | `200 OK` (System Health Only) |
| `/api/v1/datasets/upload`| `POST` | `get_optional_current_user` | `Depends(get_current_user)` | `401 Unauthorized` |
| `/api/v1/datasets` | `GET` | `Depends(get_current_user)` | `Depends(get_current_user)` | `401 Unauthorized` |
| `/api/v1/datasets/active`| `GET` | `get_optional_current_user` | `Depends(get_current_user)` | `401 Unauthorized` |
| `/api/v1/datasets/{id}` | `DELETE`| `Depends(get_current_user)` | `Depends(get_current_user)` | `401 Unauthorized` |
| `/api/v1/query` | `POST` | `get_optional_current_user` | `Depends(get_current_user)` | `401 Unauthorized` |
| `/api/v1/profile` | `GET` | `get_optional_current_user` | `Depends(get_current_user)` | `401 Unauthorized` |
| `/api/v1/deep-dive` | `POST` | `get_optional_current_user` | `Depends(get_current_user)` | `401 Unauthorized` |
| `/api/v1/what-if` | `POST` | `get_optional_current_user` | `Depends(get_current_user)` | `401 Unauthorized` |
| `/api/v1/anomalies` | `GET` | `get_optional_current_user` | `Depends(get_current_user)` | `401 Unauthorized` |

### 2.2 Investigation of `get_optional_current_user` and `demo@inslight.ai`
* **Vulnerability Identified:** The initial implementation of `get_optional_current_user` in `backend/app/api/deps.py` automatically registered and returned a fallback user (`demo@inslight.ai`) whenever an unauthenticated request arrived. Consequently, an attacker or concurrent guest users could query, upload, and inspect the shared demo user's analytical data without any credentials.
* **Remediation Implemented:**
  1. `get_optional_current_user` was refactored to return `Optional[User]` (`None` if no valid token is provided), terminating the automatic fallback to `demo@inslight.ai`.
  2. All functional data and analytical routes were transitioned to `Depends(get_current_user)`, enforcing mandatory JWT authentication.
  3. `/api/v1/health` was stripped of user dataset resolution to ensure zero metadata leakage to unauthenticated probes.
  4. The frontend dashboard retrieves `/api/v1/health` for general backend status and queries `/api/v1/datasets/active` using the authenticated user's Bearer token.

### 2.3 JWT & Credential Security
* **Password Hashing:** Verified with `passlib[bcrypt]` using salt rounds. Plaintext passwords never enter the database.
* **Duplicate Registrations:** Rejected with `HTTP 400 Bad Request` (`Email already exists`).
* **Invalid Tokens:** Rejected with `HTTP 401 Unauthorized` (`Invalid or expired authentication token.`).
* **Expired Tokens:** Tested with tokens set to `exp = now - 10s`; rejected with `HTTP 401 Unauthorized`.
* **Identity Source:** Authenticated identity is resolved directly from the verified JWT `sub` claim matched against active database records.

---

## 3. Dataset & Cross-User Isolation Audit

### 3.1 Two-User Cross-Tenant Isolation Test
A dedicated multi-tenant integration test was executed (`tests/test_dataset_isolation.py`):
1. **User A (`user_a@domain.com`)** registered and uploaded `dataset_a.csv` (sales revenue).
2. **User B (`user_b@domain.com`)** registered and uploaded `dataset_b.csv` (customer spend).
3. **Dataset Listing:** `GET /api/v1/datasets` for User A returned strictly Dataset A (count = 1). `GET /api/v1/datasets` for User B returned strictly Dataset B (count = 1).
4. **Unauthorized Deletion:** User B attempted `DELETE /api/v1/datasets/{dataset_a_id}`. The request was rejected with `404 Not Found`, and User A's dataset remained completely intact.
5. **Unauthorized What-If Simulation:** User B attempted `POST /api/v1/what-if` supplying User A's `dataset_id`. The request was rejected with `404 Not Found` (`Dataset not found or access denied.`).
6. **Unauthorized Natural-Language Query:** User B attempted `POST /api/v1/query` specifying User A's `dataset_id`. The request was blocked, returning an explicit error (`Dataset '{dataset_a_id}' not found or access denied.`).
7. **Session Hijacking Prevention:** In `QueryService.process_user_query`, chat history persistence verifies `ChatRepository.get_session(db, session_id=session_id, user_id=user.id)`. Attempting to inject messages into another user's session is detected and blocked.
8. **Physical File Isolation:** DuckDB databases are stored in distinct per-user paths (`data/datasets/{user_id}/{dataset_id}.duckdb`). Verified that `path_a` and `path_b` point to completely isolated user subdirectories.

---

## 4. Database Architecture & Verification

### 4.1 ORM Models and Migration Verification
The schema is managed through SQLAlchemy 2.0 and Alembic:
* **Models:**
  - `User`: `id` (UUID), `name`, `email` (unique index), `hashed_password`, `is_active`, `created_at`, `updated_at`.
  - `Dataset`: `id` (UUID), `user_id` (FK to `users.id` ON DELETE CASCADE), `original_filename`, `table_name`, `storage_path`, `row_count`, `column_count`, `schema_metadata`, `created_at`.
  - `ChatSession`: `id` (UUID), `user_id` (FK to `users.id`), `dataset_id` (FK to `datasets.id`), `title`, `created_at`.
  - `ChatMessage`: `id` (UUID), `session_id` (FK to `chat_sessions.id`), `role`, `content`, `metadata_json`, `created_at`.
* **Alembic Migration:** Verified migration script `alembic/versions/2925db913e27_initial_schema_users_datasets_.py` with complete `upgrade()` and `downgrade()` routines.

### 4.2 SQLite vs. PostgreSQL Clarification
* **Automated Test Suite Environment:** The automated Pytest suite uses an in-memory SQLite engine with `StaticPool` (`sqlite:///:memory:`). This provides deterministic test isolation, zero environmental flakiness, and fast execution (< 7 seconds) without external daemon dependencies.
* **Production / Persistent Environment:** The application configuration (`app.core.config.settings`) supports both PostgreSQL via `DATABASE_URL` (e.g. `postgresql+psycopg2://user:password@localhost:5432/inslight_db`) and local persistent SQLite (`sqlite:///./data/inslight.db`).
* **Audit Statement:** The test suite verifies the SQLAlchemy 2.0 ORM query syntax, foreign key cascades, and UUID relationships using SQLite. The PostgreSQL dialect configurations and Alembic revision scripts are structured and ready for production deployment.

---

## 5. SQL Security & Execution Safety

SQL security was audited across the LLM generation phase, AST validation phase, and DuckDB analytical execution phase:

### 5.1 SQLGlot AST Validation Tests
All dangerous patterns were verified against `SQLService.validate_sql()`:

| Attack / Pattern Tested | Input Sample | Validation Result | AST Enforcement Mechanism |
| :--- | :--- | :---: | :--- |
| **DROP TABLE** | `DROP TABLE sales_data` | **BLOCKED** | Non-Select statement rejected |
| **DELETE** | `DELETE FROM sales_data WHERE 1=1` | **BLOCKED** | Non-Select statement rejected |
| **UPDATE** | `UPDATE sales_data SET revenue = 0` | **BLOCKED** | Non-Select statement rejected |
| **INSERT** | `INSERT INTO sales_data VALUES (1, 2)` | **BLOCKED** | Non-Select statement rejected |
| **CREATE TABLE** | `CREATE TABLE evil (id INT)` | **BLOCKED** | Non-Select statement rejected |
| **PRAGMA / ATTACH** | `ATTACH DATABASE 'evil.db' AS evil` | **BLOCKED** | Non-Select statement rejected |
| **Multi-Statement Stacking** | `SELECT * FROM sales; DROP TABLE sales;` | **BLOCKED** | Expression list length > 1 rejected |
| **Disallowed Table Access** | `SELECT * FROM users` | **BLOCKED** | Table name != dataset `table_name` |
| **Disallowed Subquery Table** | `SELECT * FROM (SELECT * FROM users)` | **BLOCKED** | Recursive AST traversal identifies unauthorized table |
| **Missing LIMIT** | `SELECT region, revenue FROM sales_data` | **SAFE** | Automatically injects `LIMIT 100` |

### 5.2 DuckDB Execution Path
* Queries only execute on a localized, read-only file connection (`duckdb.connect(storage_path, read_only=True)`).
* The analytical execution path never touches the metadata database (PostgreSQL/SQLite), preventing SQL injection from reaching user accounts or authentication credentials.

---

## 6. Business Context Guard Verification

The 5-layer Business Context Guard (`backend/app/services/business_guard.py`) was verified to confirm that non-business questions are rejected before SQL generation:

### 6.1 Query Filtering Results
* **Legitimate Business Questions (ACCEPTED):**
  - *"What is my total revenue?"* -> ALLOWED (Deterministic keyword match: revenue)
  - *"Show sales trends over time"* -> ALLOWED (Deterministic keyword match: sales, trends)
  - *"Which product category generated the highest profit?"* -> ALLOWED (Deterministic keyword match: category, profit)
  - *"What is the average order discount percentage?"* -> ALLOWED (Deterministic keyword match: discount)
  - *"Compare revenue between regions"* -> ALLOWED (Deterministic keyword match: revenue, compare)
* **Irrelevant / Inappropriate Questions (REJECTED):**
  - *"Who is the Prime Minister of India?"* -> REJECTED (Domain rejection message returned)
  - *"Tell me a funny joke"* -> REJECTED (Domain rejection message returned)
  - *"Write a Python program to sort an array"* -> REJECTED (Domain rejection message returned)
  - *"What is 1 + 1?"* -> REJECTED (Domain rejection message returned)
  - *"Write a poem about dogs"* -> REJECTED (Domain rejection message returned)
* **Execution Safety Proof:**
  When a question is rejected by the guard, `QueryService.process_user_query` immediately returns `error_response(rejection)` at Layer 2. Neither LLM SQL generation nor DuckDB execution is invoked.

---

## 7. RAG (Retrieval-Augmented Generation) Assessment

### 7.1 Implemented Capabilities (Schema-Aware RAG)
The Phase 1 RAG implementation is a **Deterministic Dataset-Aware Schema RAG Engine** located in `backend/app/services/rag_service.py`:
* **Schema Extraction:** Automatically inspects column names, semantic types (`numeric`, `date`, `categorical`, `identifier`), null frequencies, and sample distributions.
* **Prompt Construction:** Injects the formatted table schema and sanitized column list into the SQL generation template.
* **Context Isolation:** Limits context strictly to the authenticated user's active dataset.
* **Token Optimization:** Uses concise schema summaries instead of full data dumps to prevent LLM context window overflow.

### 7.2 Clear Distinction: Tabular Schema RAG vs. Vector Embeddings
* **Clarification:** Vector search and semantic embeddings (e.g. ChromaDB / FAISS / pgvector) are **not** implemented in Phase 1.
* **Technical Justification:** For structured tabular analytics, vector embeddings introduce hallucination and non-deterministic schema references. Tabular BI requires exact column names and SQL type definitions. Phase 1 correctly prioritizes deterministic AST schema grounding.

---

## 8. Frontend Quality & Architecture Verification

### 8.1 Structure and Components
The frontend (`frontend/src/`) is cleanly organized into modern App Router standards:
* **Routes:**
  - `src/app/page.tsx` — Protected Dashboard with KPI grids, ChartRenderer, and Chat interface.
  - `src/app/login/page.tsx` — Enterprise login page with JWT token storage.
  - `src/app/register/page.tsx` — User registration page with client-side validation.
* **Modular Components & Features:**
  - `components/charts/ChartRenderer.tsx` — Dynamic Recharts wrapper (Bar, Line, Area, Pie).
  - `components/common/DataTable.tsx` — Paginated data preview table.
  - `features/analytics/KPIGrid.tsx` — Summary KPI metric cards.
  - `features/what-if/WhatIfPanel.tsx` — Interactive scenario slider simulator.
  - `features/anomalies/AnomaliesPanel.tsx` — Outlier alerts and anomaly view.
  - `features/dataset/DatasetProfileView.tsx` — Comprehensive dataset quality and distribution dashboard.
* **State & Services:**
  - `services/api-client.ts` — Centralized fetch client injecting `Authorization: Bearer <token>` and handling 401 token invalidation.
  - `services/auth-service.ts` — Authentication lifecycle manager with localStorage persistence.

### 8.2 Production Build Verification
The Next.js production build was executed and verified:
* **Command:** `npx tsc --noEmit && npm run build`
* **Output:**
  - TypeScript validation: **0 errors**
  - Route compilation: **6/6 static routes compiled successfully** (`/`, `/_not-found`, `/login`, `/register`)
  - Shared JS bundle size: **81.9 kB**
  - Build status: **SUCCESS**

---

## 9. Issues Identified and Remediated

| ID | Issue Description | Severity | Remediation Applied | Status |
| :--- | :--- | :---: | :--- | :---: |
| **SEC-01** | `get_optional_current_user` silently mapped unauthenticated callers to `demo@inslight.ai`, permitting unauthorized dataset access. | **HIGH** | Refactored `deps.py` to return `None`; converted all core routes (`/query`, `/datasets/upload`, `/profile`, `/deep-dive`, `/what-if`, `/anomalies`) to `Depends(get_current_user)`. | **RESOLVED** |
| **SEC-02** | `/api/v1/health` leaked the active dataset row count and column schema to unauthenticated callers. | **MEDIUM** | Stripped dataset resolution from `/health`; converted `/health` to a public operational probe (`status: healthy`). | **RESOLVED** |
| **SEC-03** | `QueryService` and `/what-if` fell back to user's latest dataset when given another user's `dataset_id`, masking unauthorized cross-tenant requests. | **MEDIUM** | Updated `QueryService` and `what_if.py` to immediately return `404 Not Found` / `access denied` when a specified `dataset_id` does not belong to the user. | **RESOLVED** |
| **SEC-04** | `ChatRepository.add_message` did not verify `session.user_id == user.id`, leaving room for cross-user message injection. | **MEDIUM** | Added session ownership check in `QueryService` before persisting messages. | **RESOLVED** |
| **TST-01** | Analytics tests in `test_analytics.py` lacked authentication headers and failed following the security hardening. | **LOW** | Updated tests to register an analyst user and supply Bearer tokens in test requests. | **RESOLVED** |
| **TST-02** | `test_dataset_isolation.py` attempted to access nonexistent static method `DatasetService.get_duckdb_path`. | **LOW** | Added `DatasetService.get_duckdb_path(cls, user_id, dataset_id)` helper and verified directory isolation. | **RESOLVED** |

---

## 10. Automated Test Results Summary

```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\dhanu\OneDrive\Desktop\dash-ai\backend
plugins: anyio-3.7.1
collected 20 items

tests/test_analytics.py::test_what_if_analysis PASSED                    [  5%]
tests/test_analytics.py::test_anomalies_detection PASSED                 [ 10%]
tests/test_auth.py::test_user_registration_success PASSED                [ 15%]
tests/test_auth.py::test_user_registration_duplicate_fails PASSED        [ 20%]
tests/test_auth.py::test_user_login_success PASSED                       [ 25%]
tests/test_auth.py::test_user_login_invalid_password_fails PASSED        [ 30%]
tests/test_auth.py::test_unauthenticated_access_to_all_protected_endpoints PASSED [ 35%]
tests/test_auth.py::test_invalid_jwt_token_rejected PASSED               [ 40%]
tests/test_auth.py::test_expired_jwt_token_rejected PASSED               [ 45%]
tests/test_business_guard.py::test_deterministic_business_questions_allowed PASSED [ 50%]
tests/test_business_guard.py::test_deterministic_unrelated_questions_rejected PASSED [ 55%]
tests/test_business_guard.py::test_guard_validation_rejects_unrelated PASSED [ 60%]
tests/test_business_guard.py::test_guard_validation_requires_dataset_when_none_loaded PASSED [ 65%]
tests/test_dataset_isolation.py::test_dataset_isolation_between_users PASSED [ 70%]
tests/test_sql_security.py::test_sql_validator_allows_valid_select PASSED [ 75%]
tests/test_sql_security.py::test_sql_validator_rejects_drop_table PASSED [ 80%]
tests/test_sql_security.py::test_sql_validator_rejects_delete PASSED     [ 85%]
tests/test_sql_security.py::test_sql_validator_rejects_multiple_statements PASSED [ 90%]
tests/test_sql_security.py::test_sql_validator_rejects_dml_and_ddl PASSED [ 95%]
tests/test_sql_security.py::test_sql_validator_rejects_subquery_on_disallowed_tables PASSED [100%]

======================= 20 passed in 6.16s =======================
```

---

## 11. Final Assessment & Recommendation

The Phase 1 architecture of **INSLIGHT** has been thoroughly tested, remediated, and verified.
* **Backend:** Secure, layered, modular monolith with strict JWT authentication, SQLGlot AST validation, 5-layer Business Context Guard, and per-user DuckDB data isolation.
* **Frontend:** Refactored Next.js 14 App Router application with modular component architecture, auth flow, and 100% build pass rate.
* **Integrity:** `frontend-react/` remains completely untouched. No Phase 2 features were prematurely implemented.

**Recommendation:**
The project is **technically sound, fully verified, and ready to advance to Phase 2**.
