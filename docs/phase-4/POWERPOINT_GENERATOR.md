# AI PowerPoint Presentation Generator

## Overview
Implemented in `backend/app/services/presentation_service.py`, `backend/app/api/v1/routes/presentations.py`, and `frontend/src/features/presentations/PresentationStudio.tsx`.

## Supported Presentation Types
- Executive Business Review
- Monthly Sales Report
- Revenue Performance
- Regional Performance
- Product Performance
- Business Opportunities and Risks
- Forecasting Report
- Custom Business Presentation

## Two-Step User Workflow
1. **Generate Editable Outline (`POST /api/v1/presentations/outline`):**
   - Validates prompt via `BusinessContextGuard`.
   - Executes `StrategicAnalysisService` and `ForecastingService` directly against the user's DuckDB dataset.
   - Returns an editable JSON outline (`slides: [{slide_number, title, layout, bullets, metric_highlight}]`).
2. **Preview, Edit & Build `.pptx` (`POST /api/v1/presentations/generate`):**
   - User edits slide titles, bullets, or removes slides in `PresentationStudio.tsx`.
   - Backend generates a 16:9 widescreen PowerPoint deck via `python-pptx` with dark-slate executive styling, KPI cards, and embedded `matplotlib` charts (`bar`, `pie`).
   - Saves `.pptx` to `REPORT_STORAGE_DIR`, persists `Presentation` record, logs `AuditService`, and triggers a `Notification`.
3. **Download & Manage (`GET /api/v1/presentations`, `GET /{id}/download`, `DELETE /{id}`):**
   - Enforces strict `user_id` ownership (`404` for cross-user access).
