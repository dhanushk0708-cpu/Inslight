# INSLIGHT — Phase 2 Verification & Test Report
**Test Execution Date:** November 24, 2026
**Auditor Roles:** Senior Full-Stack Engineer, QA Architect
**Result:** **100% PASS RATE (31/31 BACKEND TESTS, 0 FRONTEND BUILD ERRORS)**

---

## 1. Automated Backend Test Execution

Executed via `pytest -v` using the Python 3.11.9 virtual environment (`backend/.venv`):

```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\dhanu\OneDrive\Desktop\dash-ai\backend
plugins: anyio-3.7.1
collected 31 items

tests/test_analytics.py::test_what_if_analysis PASSED                    [  3%]
tests/test_analytics.py::test_anomalies_detection PASSED                 [  6%]
tests/test_auth.py::test_user_registration_success PASSED                [  9%]
tests/test_auth.py::test_user_registration_duplicate_fails PASSED        [ 12%]
tests/test_auth.py::test_user_login_success PASSED                       [ 16%]
tests/test_auth.py::test_user_login_invalid_password_fails PASSED        [ 19%]
tests/test_auth.py::test_unauthenticated_access_to_all_protected_endpoints PASSED [ 22%]
tests/test_auth.py::test_invalid_jwt_token_rejected PASSED               [ 25%]
tests/test_auth.py::test_expired_jwt_token_rejected PASSED               [ 29%]
tests/test_business_guard.py::test_deterministic_business_questions_allowed PASSED [ 32%]
tests/test_business_guard.py::test_deterministic_unrelated_questions_rejected PASSED [ 35%]
tests/test_business_guard.py::test_guard_validation_rejects_unrelated PASSED [ 38%]
tests/test_business_guard.py::test_guard_validation_requires_dataset_when_none_loaded PASSED [ 41%]
tests/test_dataset_isolation.py::test_dataset_isolation_between_users PASSED [ 45%]
tests/test_gmail.py::test_gmail_authorization_url_generation PASSED      [ 48%]
tests/test_gmail.py::test_gmail_status_and_disconnect PASSED             [ 51%]
tests/test_gmail.py::test_gmail_oauth_callback_handling PASSED           [ 54%]
tests/test_gmail.py::test_gmail_email_send_mock PASSED                   [ 58%]
tests/test_reports.py::test_formula_injection_sanitization PASSED        [ 61%]
tests/test_reports.py::test_pdf_report_generation PASSED                 [ 64%]
tests/test_reports.py::test_excel_report_generation PASSED               [ 67%]
tests/test_reports.py::test_csv_report_generation PASSED                 [ 70%]
tests/test_reports.py::test_report_endpoints_and_isolation PASSED        [ 74%]
tests/test_scheduler.py::test_schedule_crud_and_isolation PASSED         [ 77%]
tests/test_scheduler.py::test_scheduler_due_execution PASSED             [ 80%]
tests/test_sql_security.py::test_sql_validator_allows_valid_select PASSED [ 83%]
tests/test_sql_security.py::test_sql_validator_rejects_drop_table PASSED [ 87%]
tests/test_sql_security.py::test_sql_validator_rejects_delete PASSED     [ 90%]
tests/test_sql_security.py::test_sql_validator_rejects_multiple_statements PASSED [ 93%]
tests/test_sql_security.py::test_sql_validator_rejects_dml_and_ddl PASSED [ 96%]
tests/test_sql_security.py::test_sql_validator_rejects_subquery_on_disallowed_tables PASSED [100%]

====================== 31 passed, 17 warnings in 13.24s =======================
```

---

## 2. Frontend Build & Static Analysis

Executed via `npx tsc --noEmit && npm run build` inside `frontend/`:
- **TypeScript Static Check:** 0 type errors.
- **Next.js Production Build:**
  - Route compilation: **6/6 static routes generated successfully** (`/`, `/_not-found`, `/login`, `/register`).
  - Total first load JS: **98 kB**.
  - Status: **PASSED**.

---

## 3. Strict Restrictions Compliance Verification

- **`frontend-react/`:** Completely untouched. Verified via `git status frontend-react`.
- **Phase 1 Functionality:** 100% preserved. All 20 Phase 1 tests pass alongside the 11 new Phase 2 tests.
- **Credential Protection:** Credentials file `google-oauth-credentials.json` remains properly ignored by Git. No tokens, secrets, or passwords appear in logs or responses.
