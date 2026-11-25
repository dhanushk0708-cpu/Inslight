# Known Issues, Limitations & Defect Log

**Audit Date:** 2026-11-25

---

## 1. Defect Fixed During This Audit

1. **Scheduler Email Failure Status Overwrite (`backend/app/services/scheduler.py`)**
   - **Issue:** In `SchedulerService.execute_due_schedules()`, if `GmailService.send_report_email()` raised an exception, `schedule.last_status` was set to `"Generated, mail failed: ..."` inside the `except` block, but the very next line unconditionally overwrote `schedule.last_status = "success"`.
   - **Fix:** Moved `schedule.last_status = "success"` into the `try` block (and the `else` branch when no recipients are configured) so email delivery failures are accurately preserved in `last_status`.

---

## 2. Known Limitations & Non-Critical Findings

1. **Gmail Live OAuth & Delivery Not Executed (`CONFIGURATION REQUIRED`)**
   - Automated tests mock `httpx.AsyncClient` for Google token exchange and `gmail.send`. Real OAuth consent and live Gmail API email delivery require an interactive browser login with Google Cloud test-user whitelisting.
2. **Scheduled Report Timezone Handling (`PARTIAL`)**
   - Schedules currently compute `next_run_at` in UTC using fixed `timedelta(days=7)` or `timedelta(days=30)` increments from creation/execution time. User-selectable timezones and specific wall-clock cron times are not implemented.
3. **Alembic Version Stamp on SQLite (`inslight.db`)**
   - `init_db()` creates all tables via `Base.metadata.create_all()` on startup. As a result, `alembic current` reports empty on `inslight.db` even though the schema matches `c7391abf0831 (head)`.
4. **Browser Subagent Connectivity in Audit Environment**
   - Live automated Chrome DevTools clicks could not run during this audit because Chrome remote debugging (`DevToolsActivePort`) was not active on the host.
5. **Development Fallback Secrets in `config.py`**
   - `SECRET_KEY` and `ENCRYPTION_KEY` fall back to static development strings if omitted from `.env`. Production deployments must set unique secrets in `.env`.
6. **Legacy `test_reports.py` / `httpx` Deprecation Warnings**
   - Pytest emits 33 `DeprecationWarning` messages for `httpx.AsyncClient(app=...)` shortcut usage in test fixtures; zero functional impact.
