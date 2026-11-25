# INSLIGHT BI Report Engine — Verification & Test Results

## 1. Test Suite Summary

The comprehensive automated test suite covers unit, integration, authentication, SQL security, dataset isolation, scheduler, and reporting engine components.

### Test Results
- **Test Framework:** `pytest 9.2.0` on Python 3.11.9 (Windows x64)
- **Total Tests Collected:** 33 items
- **Passed:** 33 (100%)
- **Failed:** 0
- **Duration:** 52.11s

```
tests/test_analytics.py::test_what_if_analysis PASSED                    [  3%]
tests/test_analytics.py::test_anomalies_detection PASSED                 [  6%]
tests/test_auth.py::test_user_registration_success PASSED                [  9%]
tests/test_auth.py::test_user_registration_duplicate_fails PASSED        [ 12%]
tests/test_auth.py::test_user_login_success PASSED                       [ 15%]
tests/test_auth.py::test_user_login_invalid_password_fails PASSED        [ 18%]
tests/test_auth.py::test_unauthenticated_access_to_all_protected_endpoints PASSED [ 21%]
tests/test_auth.py::test_invalid_jwt_token_rejected PASSED               [ 24%]
tests/test_auth.py::test_expired_jwt_token_rejected PASSED               [ 27%]
tests/test_business_guard.py::test_deterministic_business_questions_allowed PASSED [ 30%]
tests/test_business_guard.py::test_deterministic_unrelated_questions_rejected PASSED [ 33%]
tests/test_business_guard.py::test_guard_validation_rejects_unrelated PASSED [ 36%]
tests/test_business_guard.py::test_guard_validation_requires_dataset_when_none_loaded PASSED [ 39%]
tests/test_dataset_isolation.py::test_dataset_isolation_between_users PASSED [ 42%]
tests/test_gmail.py::test_gmail_authorization_url_generation PASSED      [ 45%]
tests/test_gmail.py::test_gmail_status_and_disconnect PASSED             [ 48%]
tests/test_gmail.py::test_gmail_oauth_callback_handling PASSED           [ 51%]
tests/test_gmail.py::test_gmail_email_send_mock PASSED                   [ 54%]
tests/test_reports.py::test_formula_injection_sanitization PASSED        [ 57%]
tests/test_reports.py::test_pdf_report_generation PASSED                 [ 60%]
tests/test_reports.py::test_excel_report_generation PASSED               [ 63%]
tests/test_reports.py::test_csv_report_generation PASSED                 [ 66%]
tests/test_reports.py::test_report_endpoints_and_isolation PASSED        [ 69%]
tests/test_reports.py::test_comprehensive_pdf_report_and_pagination PASSED [ 72%]
tests/test_reports.py::test_comprehensive_excel_multi_sheet_workbook PASSED [ 75%]
tests/test_scheduler.py::test_schedule_crud_and_isolation PASSED         [ 78%]
tests/test_scheduler.py::test_scheduler_due_execution PASSED             [ 81%]
tests/test_sql_security.py::test_sql_validator_allows_valid_select PASSED [ 84%]
tests/test_sql_security.py::test_sql_validator_rejects_drop_table PASSED [ 87%]
tests/test_sql_security.py::test_sql_validator_rejects_delete PASSED     [ 90%]
tests/test_sql_security.py::test_sql_validator_rejects_multiple_statements PASSED [ 93%]
tests/test_sql_security.py::test_sql_validator_rejects_dml_and_ddl PASSED [ 96%]
tests/test_sql_security.py::test_sql_validator_rejects_subquery_on_disallowed_tables PASSED [100%]
```

---

## 2. Generated Artifact Validation

### PDF Document Generation
- **Sample Dataset Tested:** `sample_sales.csv` (96 records)
- **Output File Size:** 369,917 bytes
- **Page Count:** Exactly 10 Pages (validated via `pypdf.PdfReader`)
- **Visuals Included:** 5 Matplotlib charts (Trend, Regional, SKU Rankings, Donut, Comparison)
- **Numbering:** Dynamic two-pass header/footer with `NumberedCanvas` ("Page X of 10").

### Excel Document Generation
- **Worksheets Verified:** 9 sheets (`Executive Summary`, `KPI Dashboard`, `Revenue Trends`, `Regional Performance`, `Product Performance`, `Category Breakdown`, `Anomaly Audit`, `Analyst Insights & Strategy`, `Source Data Partition`)
- **Output File Size:** 20,333 bytes
- **Formula Injection Security:** Passed (Cells starting with `=, +, -, @` sanitized with single quotes)

### Frontend Verification
- **Framework:** Next.js 14.0.4 App Router
- **Type Check:** `npx tsc --noEmit` passed with 0 errors.
- **Production Build:** `npm run build` compiled 6 static routes cleanly.

### Project Constraint Audit
- **`frontend-react/` Directory:** 100% untouched.
