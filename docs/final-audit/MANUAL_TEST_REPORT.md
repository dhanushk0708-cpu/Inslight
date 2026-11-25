# Manual & Live Integration Test Report

**Audit Date:** 2026-11-25

---

## 1. Live Server & API Integration Verification (`http://127.0.0.1:8000`)

Both the backend (`:8000`) and frontend (`:3000`) were verified running. Live HTTP requests using `httpx` were executed end-to-end against `http://127.0.0.1:8000/api/v1` with two freshly registered users (`User 1` and `User 2`):

| Workflow Tested Live | HTTP Status | Observed Result |
|---|---|---|
| Frontend Root (`http://127.0.0.1:3000/`) | `200 OK` | Served HTML (`9,705` bytes) |
| Health Check (`GET /health`) | `200 OK` | `{"status": "healthy", "version": "1.0.0"}` |
| User Registration (`POST /auth/register`) | `201 Created` | Registered User 1 & User 2 with JWT tokens |
| CSV Upload (`POST /datasets/upload` — `sample_sales.csv`) | `200 OK` | Parsed `96` rows |
| Active Dataset Sync (`GET /datasets/active`) | `200 OK` | Returned `row_count: 96`, `rows: 96` |
| PDF & Excel Report Generation (`POST /reports/generate`) | `200 OK` | Both PDF and Excel generated |
| PDF Download & Isolation (`GET /reports/{id}/download`) | `200 OK` / `404` | User 1 downloaded `369,876` bytes; User 2 blocked with `404` |
| Schedule Create, Toggle & Isolation (`POST/PUT/GET /reports/schedules`) | `200 OK` / `404` | Created weekly schedule, toggled `is_active: false`, User 2 blocked with `404` |
| BI Agent Broad Question (`POST /agent/query`) | `200 OK` | `strategic_analysis` returned 3 opportunities (with hypothesis/calc labels) & 3 risks |
| Root Cause Analysis (`POST /analytics/rca`) | `200 OK` | `status: success` |
| Forecasting (`POST /analytics/forecast`) | `200 OK` | `status: success`, `method: random_forest` |
| Advanced Anomalies (`POST /analytics/advanced-anomalies`) | `200 OK` | `status: success` |
| Alerts Scan & Feed (`POST /alerts/scan`, `GET /alerts`) | `200 OK` | Evaluated active rules cleanly |
| Data Quality & Preview (`POST /quality`, `GET /quality/preview`) | `200 OK` | `overall_score: 100`, preview returned `200 OK` |
| Comparative Analytics (`POST /analytics/compare`) | `200 OK` | `status: success` |
| AI Dashboard Studio (`generate`, `save`, `duplicate`, `get` U2) | `200 OK` / `404` | Generated, persisted, duplicated; User 2 blocked with `404` |
| Multi-Dataset (`candidates`, `validate`, `preview`) | `200 OK` | `cardinality: many_to_one`, `risk_level: LOW`, `0` nulls, DuckDB join returned records |

---

## 2. Live Browser Verification Status

- **Attempted:** Invoked the Chrome DevTools browser subagent against `http://localhost:3000`.
- **Outcome:** **NOT TESTED** in this audit pass because Chrome remote debugging (`DevToolsActivePort` at `C:\Users\dhanu\AppData\Local\Google\Chrome\User Data\DevToolsActivePort`) was not running/enabled on the host machine.
- **Note:** Prior interactive browser testing was performed by the user (who verified the dashboard, KPI cards, opportunities, risks, charts, and dataset synchronization, and reported the Markdown formatting issue fixed in `MarkdownRenderer.tsx`).
