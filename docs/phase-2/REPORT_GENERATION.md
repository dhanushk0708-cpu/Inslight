# INSLIGHT — Report Generation Architecture
**PDF, Excel, and CSV Document Synthesis**

---

## 1. Overview

The INSLIGHT Report Generation engine transforms live business intelligence analytics into downloadable and emailable business reports. All report metrics are derived from authenticated queries, DuckDB columnar aggregations, and actual dataset profiling.

---

## 2. Report Formats

### 2.1 PDF Business Report (`ReportLab`)
Implemented in `backend/app/services/pdf_generator.py`.
- **Layout & Structure:**
  1. **Header Block:** Document Title, Dataset Name, Generation Timestamp (UTC), Decorative Accent Line.
  2. **Executive Summary:** Clean AI narrative summarizing macro trends and performance drivers.
  3. **Key Performance Indicators:** 3-column structured grid of KPI cards (Metric Label, Formatted Value, Value Column).
  4. **Performance Breakdown Table:** Up to 7 columns of actual dataset records with alternating zebra row styling and dark header band.
  5. **Operational Outliers & Anomalies:** Red-accented risk table showing metric, timestamp, observed value, expected range, and severity.
  6. **Data Scope & Limitations:** Summary of evaluated rows, column count, and overall data quality score.
- **Two-Pass Dynamic Numbering:** Custom `NumberedCanvas` dynamically calculates total pages to print `"Page X of Y"` and confidentiality disclaimers in the footer.

### 2.2 Structured Excel Workbooks (`openpyxl`)
Implemented in `backend/app/services/excel_generator.py`.
- **Worksheets:**
  - `Overview`: Dataset metadata, record counts, health score, and executive summary.
  - `KPI Summary`: Metric name, value, aggregation type, and display format.
  - `Query Results`: Tabular data rows with styled headers, borders, and alternating row fills.
  - `Business Insights`: Key findings, recommended actions, and outlier alerts.
- **Formatting:** Automatic column width calculation based on maximum cell string length.

### 2.3 CSV Exports (`csv`)
Implemented in `backend/app/services/csv_generator.py`.
- Clean comma-separated format for ingestion into external spreadsheets, Python scripts, or data pipelines.

---

## 3. Critical Security: Formula Injection Prevention

### 3.1 The Vulnerability (CSV / Formula Injection)
When spreadsheet applications (Microsoft Excel, LibreOffice, Google Sheets) open CSV or XLSX files, text cells beginning with mathematical or command symbols can be executed as dynamic formulas:
- `=cmd|' /C calc'!A0`
- `+1+1`
- `-2+cmd`
- `@SUM(...)`

### 3.2 Remediation Implementation
The helper `sanitize_formula_injection(val)` inspects all string values written to Excel cells or CSV rows:
```python
def sanitize_formula_injection(val: Any) -> Any:
    if isinstance(val, str) and len(val) > 0:
        if val[0] in ("=", "+", "-", "@", "\t", "\r"):
            return "'" + val
    return val
```
Prefixing with a single quote (`'`) forces spreadsheet applications to treat the cell contents purely as verbatim text strings, completely neutralizing formula execution.

---

## 4. Multi-Tenant Storage & Isolation

- Generated reports are written to disk under user-isolated subdirectories:
  `data/reports/{user_id}/{report_id}.{pdf|xlsx|csv}`
- Each report record in the database is bound to `user_id`.
- The download endpoint (`GET /api/v1/reports/{report_id}/download`) validates `Report.user_id == user.id`. Cross-user attempts return `404 Not Found`.
