# INSLIGHT — Phase 2 Implementation Summary
**Voice Assistant & Reporting Automation**
**Final-Year BCA AI & ML Project**

---

## 1. Executive Summary

Phase 2 builds directly upon the secure layered foundation established in Phase 1, introducing voice accessibility, automated document reporting (PDF, Excel, CSV), Google Gmail OAuth 2.0 integration, persistent report history, and automated weekly/monthly report scheduling.

All implementations strictly adhere to college project guidelines: avoiding unnecessary infrastructure complexity (no Redis, Celery, or microservices) while maintaining enterprise-grade security (Fernet token encryption, CSRF protection, spreadsheet formula injection sanitization, and strict multi-tenant isolation).

---

## 2. Key Features Implemented

### 2.1 Multilingual Voice Assistant & AI Voice Response
- **Speech Recognition (Web Speech API):** Seamless voice input integrated directly beside the chat input. Supports English (`en-IN`), Hindi (`hi-IN`), and Kannada (`kn-IN`).
- **Human-in-the-Loop Transcript Review:** Converts speech to text and populates the editable input box. Never executes automatically without explicit user confirmation.
- **Privacy Guarantees:** Zero audio recording on the backend; all speech recognition executes client-side via native browser APIs.
- **AI Voice Narration (Speech Synthesis API):** Optional text-to-speech engine that reads executive business summaries. Strips raw code and SQL queries; includes manual Play/Stop controls.

### 2.2 Professional Report Generation (PDF, Excel, CSV)
- **High-Fidelity PDF Reports (`ReportLab`):** Automated business reports featuring Cover/Header blocks, Executive Summaries, Key Performance Indicator grids, data breakdown tables, outlier/anomaly logs, data quality health scores, and dynamic two-pass page numbering ("Page X of Y").
- **Multi-Tab Excel Workbooks (`openpyxl`):** Structured workbooks across `Overview`, `KPI Summary`, `Query Results`, and `Business Insights` tabs with professional typography and formatting.
- **Spreadsheet Formula Injection Sanitization:** Critical security defense neutralizing cells starting with `=`, `+`, `-`, `@`, `\t`, or `\r` by prefixing with a single quote (`'`).
- **CSV Export:** Fast, lightweight raw data export with formula injection sanitization.

### 2.3 Gmail OAuth 2.0 Integration & Email Composer
- **Secure OAuth 2.0 Authorization Code Flow:** Leverages existing credentials in `backend/google-oauth-credentials.json` requesting minimum required scope (`https://www.googleapis.com/auth/gmail.send`).
- **CSRF State Token:** Uses signed, expiring JWT state tokens to prevent cross-site request forgery during OAuth redirects.
- **Fernet Token Encryption at Rest:** Encrypts Google access tokens and refresh tokens in the database using 256-bit AES encryption.
- **Email Composer:** Interactive UI modal with multi-recipient inputs, CC support, editable subject/body, attachment size validation (<25MB limit), and an explicit "Review & Confirm Delivery" step before dispatching via the Gmail API.

### 2.4 Persistent Report History & Ownership Isolation
- **Database Schema:** New `reports` table tracking report ID, format, file path, size, generation timestamp, email delivery status, and Gmail message ID.
- **Multi-Tenant Physical Storage:** Files are stored in per-user isolated subdirectories (`data/reports/{user_id}/{report_id}.{ext}`). Cross-user download or deletion attempts return `404 Not Found`.

### 2.5 Automated Report Scheduling
- **Lightweight In-Process Scheduler:** Standard library async scheduler loop integrated into the FastAPI lifespan. Checks every 60 seconds for due jobs.
- **Configurable Frequencies:** Supports `weekly` (+7 days) and `monthly` (+30 days) automated reporting.
- **Duplicate Prevention & History:** Records `last_run_at`, computes `next_run_at`, and captures execution logs (`success` / `failed`).

---

## 3. Architecture & File Structure

```text
backend/
  app/
    api/v1/routes/
      reports.py                # Report generation, history, download, email & scheduling routes
      gmail.py                  # Google OAuth authorize, callback, status, disconnect routes
    models/
      report.py                 # Report & ScheduledReport SQLAlchemy models
      oauth.py                  # OAuthCredential SQLAlchemy model
    repositories/
      report_repository.py      # Database operations for reports and schedules
      oauth_repository.py       # Encrypted token storage & retrieval
    services/
      pdf_generator.py          # ReportLab PDF styling & layout engine
      excel_generator.py        # openpyxl workbook generator with formula injection protection
      csv_generator.py          # Sanitized CSV generator
      report_service.py         # Unified report generation orchestrator
      gmail_service.py          # Google OAuth & Gmail API v1 sender
      scheduler.py              # In-process background cron loop
    core/
      security.py               # Added Fernet symmetric encryption helpers

frontend/
  src/
    features/
      voice/
        VoiceInput.tsx          # Web Speech API input with language selector & privacy tooltip
        VoiceControls.tsx       # Speech Synthesis toggle and audio controls
      reports/
        ReportModal.tsx         # Report generation dialog (PDF/Excel/CSV)
        EmailComposerModal.tsx  # Gmail composer with preview and confirmation
        ReportsView.tsx         # Report history table & schedule manager
      chat/
        ChatInput.tsx           # Updated to embed VoiceInput
    app/
      page.tsx                  # Added Reports tab and Query Export action
    types/
      index.ts                  # Added ReportItem, ScheduledReportItem, GmailStatus types
```

---

## 4. Verification & Readiness

- **Backend Pytest Suite:** **31 / 31 passed (100% pass rate)** in 13.24 seconds.
- **Frontend TypeScript & Build:** Next.js production build compiled cleanly across all 6 static routes with 0 errors.
- **Untouched Components:** `frontend-react/` remains completely untouched.
