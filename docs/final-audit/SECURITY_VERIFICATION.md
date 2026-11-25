# Security & Authorization Verification Report

**Audit Date:** 2026-11-25

---

## 1. Route Authorization Audit

All routes registered on `app.main.app` were programmatically inspected for authentication dependencies (`get_current_user`).

- **Protected Application Routes (52 routes):** Every data, analytics, agent, alert, dashboard, relationship, report, schedule, and profile endpoint enforces `Depends(get_current_user)` (HTTP `401`/`403` when unauthenticated).
- **Public Endpoints (4 routes):**
  1. `POST /api/v1/auth/login`
  2. `POST /api/v1/auth/register`
  3. `GET /api/v1/health` — Returns static operational status only (`status`, `version`, `service`); zero tenant/dataset metadata leaked.
  4. `GET /api/v1/integrations/gmail/callback` — Protected by signed JWT `state` CSRF token (`decode_access_token(state)` with 15-minute expiry).

---

## 2. Security Controls Verification

| Control | Implementation | Verification | Status |
|---|---|---|---|
| **Password Security** | `bcrypt.gensalt()` + `bcrypt.hashpw()` (`core/security.py`) | `test_auth.py` | **PASS** |
| **JWT Validation** | PyJWT HS256 with `exp`, `sub`, `iat`; rejects invalid/expired tokens | `test_invalid_jwt_token_rejected`, `test_expired_jwt_token_rejected` | **PASS** |
| **Duplicate Registration Guard** | Email uniqueness check on `/auth/register` | `test_user_registration_duplicate_fails` | **PASS** |
| **Dataset Isolation** | `DatasetRepository` filters by `user_id`; isolated DuckDB file per dataset under `data/datasets/{user_id}/` | `test_dataset_isolation_between_users` + Live API | **PASS** |
| **Report & Schedule Ownership** | `ReportRepository` scopes all queries/downloads/deletes by `user_id` | `test_reports.py` + Live API (`404` cross-user) | **PASS** |
| **Dashboard Ownership** | `SavedDashboard` queries scoped by `user_id` | Live API (`404` cross-user) | **PASS** |
| **SQL AST Validation** | `SQLService.validate_sql` via SQLGlot: `SELECT`-only, single statement, table/column allowlist, blocks DDL/DML/subqueries on disallowed tables | `test_sql_security.py` (6 tests) | **PASS** |
| **Business Context Guard** | 2-layer deterministic regex + LLM classifier rejecting non-business queries | `test_business_guard.py` (4 tests) | **PASS** |
| **Excel Formula Injection Guard** | Sanitizes leading `=`, `+`, `-`, `@` in exported cells | `test_formula_injection_sanitization` | **PASS** |
| **Gmail Token Encryption at Rest** | Fernet symmetric encryption (`encrypt_secret` / `decrypt_secret`) | Code inspection (`core/security.py`, `gmail_service.py`) | **PASS** |
| **Secret Exposure** | `google-oauth-credentials.json` is gitignored; `SECRET_KEY` and `ENCRYPTION_KEY` have dev defaults in `config.py` | Code inspection (`config.py`) | **PARTIAL** |

> **Security Advisory for Production Deployment:** `backend/app/core/config.py` provides hardcoded fallback defaults for `SECRET_KEY` and `ENCRYPTION_KEY` for local college demonstration convenience. Before any production deployment, strong environment-specific secrets must be injected via `.env` / secret manager.
