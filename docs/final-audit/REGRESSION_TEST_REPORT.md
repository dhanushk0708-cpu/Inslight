# Regression & Technical Verification Report

**Audit Date:** 2026-11-25

---

## 1. Automated Backend Test Suite (`pytest`)

Executed against the complete `backend/tests/` directory **after** the final code edit (`scheduler.py` failure-status fix):

- **Command:** `backend/.venv/Scripts/python.exe -m pytest backend/tests -v --tb=short`
- **Total Collected:** 49 tests
- **Passed:** 49 (100%)
- **Failed:** 0
- **Skipped:** 0

### Suite Breakdown
- `test_analytics.py`: 2 passed
- `test_auth.py`: 7 passed
- `test_business_guard.py`: 4 passed
- `test_dataset_isolation.py`: 1 passed
- `test_gmail.py`: 4 passed (uses mocked Google OAuth/Gmail API responses)
- `test_phase3_analytics.py`: 5 passed
- `test_phase3_bi_agent.py`: 8 passed
- `test_phase3_dashboards_alerts_relationships.py`: 3 passed
- `test_reports.py`: 7 passed
- `test_scheduler.py`: 2 passed
- `test_sql_security.py`: 6 passed

---

## 2. Frontend TypeScript & Production Build Verification

- **TypeScript Check:** `cd frontend && npx tsc --noEmit` — **0 errors** (Exit code 0)
- **Next.js Production Build:** `cd frontend && npm run build` — **Compiled successfully**, **6/6 static pages generated** (`/`, `/_not-found`, `/login`, `/register`).

---

## 3. Database Migration Verification (`alembic`)

- **Alembic Head:** `c7391abf0831 (head)` (`phase3_alerts_dashboards_relationships`)
- **Alembic Current on `inslight.db`:** Empty (untracked).
- **Finding:** Local SQLite database `backend/data/inslight.db` initializes tables automatically via SQLAlchemy `Base.metadata.create_all()` inside `init_db()` on FastAPI startup rather than running `alembic upgrade head`. All Phase 1–3 tables exist and operate properly, but `alembic_version` is not stamped in `inslight.db`.

---

## 4. Boundary Verification (`frontend-react/`)

- `git status --porcelain frontend-react/` returned only `?? frontend-react/.env.example`.
- Zero source files inside `frontend-react/` were modified.
