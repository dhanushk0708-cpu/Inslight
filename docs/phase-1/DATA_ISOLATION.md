# INSLIGHT — Phase 1: Multi-Tenant Dataset Isolation
**Document ID:** `PHASE1-ISOLATION-01`
**Security Classification:** Critical Data Protection Architecture

---

## 1. Problem Statement: Prototype Vulnerability

In the hackathon prototype:
- All queries and uploads operated against a single global variable `db = DatabaseManager()`.
- An in-memory SQLite table named `sales_data` was shared globally across all threads and connections.
- When *User A* uploaded a dataset, it immediately overwrote the table for *User B*.
- Any user could inspect, query, or destroy any other user's data.

---

## 2. The Inslight Isolation Architecture

Phase 1 introduces **Defense-in-Depth Multi-Tenant Isolation**:

```
[Request with JWT]
       │
       ▼
1. Authentication Layer (api/deps.py)
   Extracts authenticated user_id from verified JWT
       │
       ▼
2. Authorization & Repository Layer (repositories/dataset_repository.py)
   Queries dataset strictly filtered by:
   WHERE datasets.id = :dataset_id AND datasets.user_id = :authenticated_user_id
       │
       ▼
3. File-System Storage Isolation (services/dataset_service.py)
   Dataset stored at:
   data/datasets/{user_id}/{dataset_id}.duckdb
       │
       ▼
4. Analytical Execution Isolation (services/sql_service.py)
   Connects strictly to that user's DuckDB file in read-only mode
```

---

## 3. Strict Ownership Enforcement Rules

1. **Upload Ownership:**
   - When a user uploads a CSV, a new UUID is generated for the dataset.
   - The dataset record is inserted into PostgreSQL with `user_id = user.id`.
   - The physical data is written to `data/datasets/{user_id}/{dataset_id}.duckdb`.
2. **Query Resolution:**
   - When executing `/api/v1/query`, the backend looks up datasets owned by `user.id`.
   - If a specific `dataset_id` is passed, the repository verifies `dataset.user_id == user.id`. If mismatched, HTTP 404/403 is returned.
3. **Deletion Protection:**
   - A user cannot delete a dataset unless `dataset.user_id == user.id`.
4. **Chat History Isolation:**
   - `chat_sessions` are strictly filtered by `user_id`. Users cannot view or append messages to another user's session.

---

## 4. Verification & Automated Test Evidence

Automated tests in `tests/test_dataset_isolation.py` prove complete tenant isolation:
- *Test Scenario:* User A registers and uploads `dataset_a.csv`. User B registers and uploads `dataset_b.csv`.
- *Verification 1:* User A querying `/api/v1/datasets` only receives `dataset_a.csv`.
- *Verification 2:* User B querying `/api/v1/datasets` only receives `dataset_b.csv`.
- *Verification 3:* User B attempting `DELETE /api/v1/datasets/{dataset_a_id}` receives HTTP 404/403, and User A's dataset remains intact.
