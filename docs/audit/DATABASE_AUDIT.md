# INSLIGHT — Technical Audit: Database & Data Isolation
**Document ID:** `AUDIT-DOC-04`
**Date of Audit:** November 2026
**Auditor:** Senior Database Engineer & Application Security Auditor

---

## 1. Database Implementation Overview

The current database architecture in Inslight relies on Python's built-in `sqlite3` library configured to operate as an ephemeral in-memory database:

```python
# backend/main.py (lines 75-80)
class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.table_name = "sales_data"
        self.schema_info = ""
        self.df: Optional[pd.DataFrame] = None
        self.column_aliases: Dict[str, str] = {}
        self.actual_columns: List[str] = []
```

### Ingestion & Table Creation Workflow:
1. When the server launches, `lifespan` invokes `db.load_default()`, attempting to load `backend/data/sample_sales.csv`.
2. When a user uploads a new dataset via POST `/api/upload`, the backend executes `db.load_bytes()`:
   ```python
   self.df.to_sql(self.table_name, self.conn, if_exists="replace", index=False)
   ```
3. SQLite indexes are dynamically generated on pre-defined column candidates (`order_date`, `region`, `product_category`, etc.).
4. PRAGMA queries inspect column types and sample values to construct the text schema passed to the LLM prompt.

---

## 2. Critical Findings: Multi-Tenancy & Data Leakage

### 2.1 CRITICAL VULNERABILITY: Total Absence of User Data Isolation
- **Mechanism:** The backend maintains a single global singleton instance `db = DatabaseManager()` in memory.
- **Scenario:**
  1. *User A* uploads a confidential corporate sales dataset (`q3_confidential_payroll.csv`).
  2. The table `q3_confidential_payroll` replaces the active in-memory table.
  3. *User B* opens Inslight from another browser session and queries: *"Show total revenue and salaries"*.
  4. *User B* receives complete access to *User A*'s dataset.
  5. Furthermore, if *User B* uploads `retail_orders.csv`, *User A*'s active session immediately has its data overwritten.
- **Severity:** **CRITICAL**. This represents a severe flaw in tenant isolation and data confidentiality.

### 2.2 Ephemeral Lifecycle & Zero Data Persistence
- Because the database is initialized with `:memory:`, all ingested datasets, computed indexes, and user states exist solely in RAM.
- Any server restart, deployment cycle, or worker recycling event permanently destroys all user-uploaded datasets.
- There is no backup, replication, snapshotting, or write-ahead logging (WAL) mechanism.

### 2.3 Concurrency & Connection Contention
- SQLite in-memory connections with `check_same_thread=False` are not thread-safe for concurrent read/write operations without explicit synchronization locks.
- If an upload occurs while another client runs a query, SQLite locks or raises `sqlite3.OperationalError: database table is locked` or corrupts memory state.
- Connection pooling is absent.

---

## 3. Dynamic Indexing & Schema Sanitization

In `DatabaseManager._create_indexes` (lines 212–246), indexes are created using unparameterized f-strings:
```python
self.conn.execute(
    f"CREATE INDEX IF NOT EXISTS idx_{col} ON {self.table_name}([{col}])"
)
```
- If a CSV column header or filename contains malicious characters (e.g., `col]) --`), this string interpolation enables SQL injection directly during index creation.
- Table names derived from filenames:
  ```python
  self.table_name = filename.replace(".csv", "").replace(" ", "_").replace("-", "_").lower()
  ```
  Special characters like quotes, semicolons, or SQLite keywords are not stripped, introducing table name injection vulnerabilities.

---

## 4. Target Production Database Architecture

To transition Inslight into an enterprise-ready analytical application, a hybrid relational and analytical storage model is recommended:

```
                  ┌───────────────────────────────────────────────┐
                  │                 FastAPI App                   │
                  └───────┬───────────────────────────────┬───────┘
                          │                               │
             [Metadata & Authentication]         [Analytical Datasets]
                          │                               │
                          ▼                               ▼
                 ┌──────────────────┐            ┌──────────────────┐
                 │    PostgreSQL    │            │     DuckDB /     │
                 │   (SQLAlchemy)   │            │  Parquet Storage │
                 └──────────────────┘            └──────────────────┘
                 • Users & Auth                  • High-speed columnar
                 • Organizations / Tenants         SQL execution
                 • Dataset metadata & schema     • Per-tenant / session
                 • Chat & query history            isolated files
                 • Audit & access logs           • Vector / embeddings
```

### Architectural Decisions:
1. **Metadata Tier (PostgreSQL + SQLAlchemy + Alembic):**
   - Stores user accounts, tenant boundaries, dataset metadata, query histories, KPI snapshots, and permission policies.
   - Provides ACID compliance, relational foreign keys, row-level security (RLS), and database migrations via Alembic.
2. **Analytical Data Tier (DuckDB / Columnar Parquet):**
   - Instead of SQLite (which is row-oriented and slow on large aggregations), analytical queries should execute against DuckDB or Parquet files.
   - DuckDB provides 10x–100x faster aggregations (`SUM`, `AVG`, `GROUP BY`) on tabular data than SQLite.
   - **Isolation Strategy:** Each dataset is stored as an isolated Parquet file keyed by `tenant_id/dataset_id.parquet`. A query executes against an ephemeral DuckDB session scoped strictly to the authenticated user's dataset path.
