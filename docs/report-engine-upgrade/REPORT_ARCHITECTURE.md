# INSLIGHT BI Report Engine — System Architecture

## 1. Architectural Overview

The INSLIGHT Business Intelligence Report Engine transforms raw columnar dataset records into executive-grade, C-suite presentation documents across PDF, Excel, and CSV formats.

Prior to this upgrade, reports were limited to 2-page tables lacking visual charts, executive commentary, financial ratios, or pagination accounting. The upgraded engine enforces a single source of truth analytics pipeline, computing all metrics once via DuckDB in `ReportAnalyticsService` before formatting for downstream targets.

```
                    ┌────────────────────────────┐
                    │   Client Request / Cron    │
                    │  (ReportModal / Scheduler) │
                    └─────────────┬──────────────┘
                                  │
                                  ▼
                    ┌────────────────────────────┐
                    │   ReportService Gateway    │
                    │ (backend/app/services/...) │
                    └─────────────┬──────────────┘
                                  │
                                  ▼
                    ┌────────────────────────────┐
                    │  ReportAnalyticsService    │
                    │  - Column Semantic Type    │
                    │  - DuckDB Metric Engine    │
                    │  - Financial Ratios (INR)  │
                    │  - Groq LLM Narrative     │
                    └─────────────┬──────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         ▼                        ▼                        ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ReportVisualizer  │    │PDFReportGenerator│    │ExcelReportGen.   │
│- Matplotlib Agg  │    │- ReportLab Engine│    │- OpenPyXL Engine │
│- INR Formatter   │───▶│- NumberedCanvas  │    │- 9 Sheet Workbk  │
│- In-Memory Bytes │    │- 10 Boardroom Pgs│    │- Formula Protect │
└──────────────────┘    └──────────────────┘    └──────────────────┘
```

---

## 2. Component Structure

| Component | Path | Responsibility |
|---|---|---|
| `ReportAnalyticsService` | `backend/app/services/report_analytics_service.py` | Single source of analytical truth. Connects to DuckDB, infers dimensions/measures, computes KPIs, MoM growth, group rankings, Z-score/IQR anomalies, data governance profile, and synthesizes grounded executive summary. |
| `ReportVisualizer` | `backend/app/services/report_visualizer.py` | Headless Matplotlib visualization engine (`Agg` backend). Generates 5 corporate-styled 300-DPI charts rendered directly to in-memory PNG byte streams. |
| `PDFReportGenerator` | `backend/app/services/pdf_generator.py` | ReportLab document builder utilizing two-pass `NumberedCanvas` ("Page X of Y"), boardroom corporate palette, 10 distinct sections, dynamic table wrapping, and embedded visual charts. |
| `ExcelReportGenerator` | `backend/app/services/excel_generator.py` | OpenPyXL workbook architect producing 9 themed worksheets with freeze panes, auto-fit column widths, currency formats (`₹ #,##0.00`), and formula injection sanitization. |
| `CSVReportGenerator` | `backend/app/services/csv_generator.py` | Lightweight RFC 4180 streaming table export for external data pipelines. |
| `ReportService` | `backend/app/services/report_service.py` | Orchestration layer integrating database repository, user isolated file storage, scheduled delivery, and optional custom SQL filter support. |

---

## 3. Storage and Multi-Tenant Isolation

Reports are isolated by user ID at both the database and file system levels:
- **File System:** `storage/reports/{user_id}/{report_uuid}.pdf`
- **Database:** `reports` table indexed by `user_id` foreign key.
- **Access Control:** All API endpoints (`/api/v1/reports/*`) authenticate callers via JWT and restrict querying and downloading to the report creator's `user_id`.
