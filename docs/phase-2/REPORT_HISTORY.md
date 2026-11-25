# INSLIGHT — Report History & Storage Architecture
**Phase 2: Persistent Report Management**

---

## 1. Overview

The Report History module provides persistent audit tracking, secure file retrieval, and status management for all analytical reports synthesized by users.

---

## 2. Database Schema (`reports`)

Managed via SQLAlchemy 2.0 and Alembic migration `b4280f8d0630_phase2_reports_schedules_oauth`:

| Column | Type | Constraints | Purpose |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | Primary Key | UUID identifier |
| `user_id` | `VARCHAR(36)` | Foreign Key (`users.id` CASCADE), Index | Report owner |
| `dataset_id` | `VARCHAR(36)` | Foreign Key (`datasets.id` SET NULL), Nullable | Source dataset |
| `name` | `VARCHAR(255)` | Non-null | User-defined or default title |
| `report_format`| `VARCHAR(20)` | Non-null | Format: `pdf`, `excel`, `csv` |
| `file_path` | `VARCHAR(500)` | Non-null | Local physical disk path |
| `file_size` | `INTEGER` | Default 0 | File size in bytes |
| `parameters_json`| `TEXT` | Nullable | Serialized query & KPI parameters |
| `recipients` | `VARCHAR(500)` | Nullable | Comma-separated email addresses if sent |
| `email_subject`| `VARCHAR(255)` | Nullable | Subject line used in email |
| `status` | `VARCHAR(50)` | Default `'generated'` | Status: `generated`, `sent`, `failed` |
| `gmail_message_id`| `VARCHAR(100)`| Nullable | Google message ID if sent via Gmail |
| `created_at` | `DATETIME` | Non-null, default UTC now | Generation timestamp |

---

## 3. Storage Hierarchy

```text
backend/data/reports/
  ├── {user_a_uuid}/
  │     ├── {report_1_uuid}.pdf
  │     └── {report_2_uuid}.xlsx
  └── {user_b_uuid}/
        └── {report_3_uuid}.csv
```

---

## 4. Security & Access Control

1. **Authorization Enforcement:** Every report query (`get`, `download`, `delete`) filters on `Report.id == report_id AND Report.user_id == user.id`.
2. **Path Obfuscation:** The frontend never receives absolute server disk paths; it interacts solely with opaque report UUIDs (`/api/v1/reports/{report_id}/download`).
3. **Cascade Deletion:** Deleting a report record cleans up the physical file on disk to prevent storage leaks. Deleting a user account cascades and removes all associated report records and datasets.
