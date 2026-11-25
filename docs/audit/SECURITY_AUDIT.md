# INSLIGHT — Application Security Audit
**Document ID:** `AUDIT-DOC-07`
**Date of Audit:** November 2026
**Auditor:** Application Security Auditor & Senior Software Architect

---

## 1. Security Evaluation Summary

A static application security testing (SAST) review of the Inslight codebase was conducted across frontend and backend implementations. The overall security posture of the current application is **CRITICAL / HIGH-RISK**.

The system was developed as a rapid hackathon proof-of-concept without enterprise security controls, multi-tenant isolation, authentication boundaries, or robust defense-in-depth sanitization.

| Security Domain | Status | Risk Level | Primary Vulnerability |
|---|---|---|---|
| **Authentication & Authorization** | Absent | **CRITICAL** | All endpoints are open; no user identity or tenant context |
| **Data Isolation & Multi-Tenancy** | Absent | **CRITICAL** | Global in-memory SQLite database shared across all users |
| **SQL Execution & Injection** | Insecure | **HIGH** | Incomplete blacklist filter; string formatting in schema & DDL |
| **Cross-Origin Resource Sharing (CORS)**| Misconfigured | **HIGH** | Wildcard `*` origin coupled with `allow_credentials=True` |
| **File Upload Handling** | Vulnerable | **HIGH** | In-memory 100MB buffer reading; extension-only verification |
| **Rate Limiting & DoS Protection** | Absent | **HIGH** | Unbounded external LLM inference requests |
| **Secret & Key Management** | Exposed on disk | **MEDIUM** | Plaintext API keys in `.env`; no secrets manager integration |
| **Information Disclosure** | Vulnerable | **MEDIUM** | Raw internal stack trace and exception leakage in responses |

---

## 2. In-Depth Vulnerability Analysis

### 2.1 Multi-Tenant Data Leakage & Session Hijacking
- **File & Location:** `backend/main.py` lines 75–80, 343, 103–112
- **Evidence:**
  ```python
  class DatabaseManager:
      def __init__(self):
          self.conn = sqlite3.connect(":memory:", check_same_thread=False)
          self.table_name = "sales_data"
  ...
  db = DatabaseManager()
  ```
- **Finding:** A single `DatabaseManager` instance is created at module import and shared across every incoming HTTP request.
- **Impact:** Any user uploading a dataset immediately replaces the database for all active users worldwide. Confidential datasets are leaked across user sessions without restriction.
- **Classification:** **CONFIRMED VULNERABILITY (CRITICAL)**.

---

### 2.2 Unsafe Dynamic SQL & Injection Risks
- **File & Location:** `backend/main.py` lines 221–226, 313–316, 719–722
- **Evidence:**
  ```python
  # (1) Naive blacklist validation
  for danger in ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]:
      if danger in upper:
          return None, None, sql, f"Blocked: {danger}"

  # (2) Unparameterized DDL execution
  self.conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{col} ON {self.table_name}([{col}])")

  # (3) Unparameterized query execution
  cursor = self.conn.execute(sql)
  ```
- **Finding:**
  1. The blacklist check only inspects 6 keywords. Advanced SQLite attacks using `ATTACH DATABASE`, `PRAGMA writable_schema`, `SELECT load_extension()`, subqueries, or hex-encoded comments can bypass this check.
  2. Index creation string-interpolates `col` and `table_name`. A maliciously crafted CSV header or uploaded filename (e.g., `data]; DROP TABLE sales_data; --.csv`) will execute arbitrary SQL.
  3. The LLM-generated SQL query is executed directly via `cursor = self.conn.execute(sql)` without AST validation.
- **Impact:** Potential remote code execution (via SQLite extension loading if enabled), database corruption, or arbitrary data tampering.
- **Classification:** **CONFIRMED VULNERABILITY (HIGH)**.

---

### 2.3 Permissive CORS Misconfiguration
- **File & Location:** `backend/main.py` lines 1263–1269
- **Evidence:**
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```
- **Finding:** The configuration sets `allow_origins=["*"]` while simultaneously declaring `allow_credentials=True`.
- **Impact:** Under modern browser standards, combining wildcard origins with credential sharing is rejected or exposes cross-origin requests to credentialed session hijacking. Any third-party website can forge cross-origin requests to Inslight.
- **Classification:** **CONFIRMED VULNERABILITY (HIGH)**.

---

### 2.4 File Upload Denial-of-Service & Validation Flaws
- **File & Location:** `backend/main.py` lines 1294–1300
- **Evidence:**
  ```python
  @app.post("/api/upload")
  async def upload(file: UploadFile = File(...)):
      if not file.filename.lower().endswith(".csv"):
          raise HTTPException(400, "Only CSV files supported")
      content = await file.read()
      if len(content) > 100 * 1024 * 1024:
          raise HTTPException(400, "File too large (max 100MB)")
  ```
- **Finding:**
  1. `await file.read()` reads up to 100MB into system RAM per request. Multiple concurrent uploads can trigger an out-of-memory (OOM) crash of the server process.
  2. The validation solely relies on `filename.lower().endswith(".csv")`. File MIME type (`file.content_type`) and binary magic byte checks are omitted.
- **Classification:** **CONFIRMED VULNERABILITY (HIGH)**.

---

### 2.5 Total Absence of Rate Limiting
- **File & Location:** `backend/main.py` lines 1288–1291 (`/api/query`)
- **Finding:** There is no rate-limiting middleware (e.g., `slowapi`, Redis token bucket).
- **Impact:** An attacker or runaway client loop can dispatch thousands of requests to `/api/query`. Each request fires up to 4 sequential LLM calls to Groq Cloud, rapidly exhausting monthly API quotas, incurring billing charges, and denying service to legitimate users.
- **Classification:** **CONFIRMED VULNERABILITY (HIGH)**.

---

### 2.6 Sensitive Information & Stack Trace Leakage
- **File & Location:** `backend/main.py` lines 1304–1308, lines 985–987
- **Evidence:**
  ```python
  except Exception as e:
      raise HTTPException(400, f"Failed to parse CSV: {str(e)[:200]}")
  ...
  except Exception as e:
      return error_response(f"Error: {str(e)}", ...)
  ```
- **Finding:** Internal exception details, file paths, and database error messages are reflected directly in the HTTP JSON response.
- **Impact:** Assists attackers in mapping internal dependencies, directory structures, and database engine quirks.
- **Classification:** **CONFIRMED VULNERABILITY (MEDIUM)**.

---

## 3. Recommended Remediation Blueprint

1. **Phase 1 Mandatory Authentication:** Introduce JWT Bearer token authentication and tenant identification headers on every API route.
2. **Per-Tenant Isolated Data Engine:** Replace the global in-memory SQLite singleton with isolated, per-tenant columnar datasets (DuckDB or partitioned PostgreSQL).
3. **AST SQL Parser (SQLGlot):** Enforce strict AST validation. Allow only `exp.Select` statements. Disallow DDL, DML, `PRAGMA`, and file system functions.
4. **CORS Hardening:** Restrict `allow_origins` to explicitly defined environment configurations (e.g., `http://localhost:3000` in dev, production domain in prod). Disallow wildcards with credentials.
5. **Streaming Chunk-Based File Ingestion:** Stream uploaded CSVs directly to disk or object storage in chunks; validate MIME types and parse with bounded memory buffers.
6. **Rate Limiting:** Implement token-bucket rate limiting (e.g., 20 requests/minute/user for LLM query routes).
