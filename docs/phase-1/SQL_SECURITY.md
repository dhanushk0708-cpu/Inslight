# INSLIGHT — Phase 1: SQL Generation & AST Security
**Document ID:** `PHASE1-SQL-01`
**Target:** `backend/app/services/sql_service.py`
**Security Engine:** SQLGlot AST Parser & Transpiler

---

## 1. Problem Statement: Prototype Vulnerability

The prototype relied on a naive keyword blacklist:
```python
for danger in ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]:
    if danger in upper: return None, ...
```
This check was easily bypassed via:
- Comments (e.g. `/* DROP */`)
- Lowercase/mixed case tricks
- SQLite PRAGMAs (`PRAGMA writable_schema`)
- Direct table injection via unparameterized strings (`CREATE INDEX ... ON {table}([col])`)

---

## 2. SQLGlot Abstract Syntax Tree (AST) Validation

Inslight Phase 1 replaces string matching with **AST (Abstract Syntax Tree) Parsing**:

```python
import sqlglot
from sqlglot import exp

statements = sqlglot.parse(sql)
if len(statements) != 1:
    return False, "Multiple SQL statements are not permitted."

parsed = statements[0]
if not isinstance(parsed, exp.Select):
    return False, "Only SELECT queries are permitted."

disallowed_nodes = (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Alter, exp.Create, exp.Command, exp.Pragma)
for node in parsed.find_all(disallowed_nodes):
    return False, f"Prohibited operation: {type(node).__name__}"
```

### Key Security Safeguards:
1. **Strictly Read-Only:** Only `exp.Select` statement roots are accepted.
2. **Single Statement Enforcement:** Rejects statement stacking (semicolon chaining).
3. **Table Scoping:** Validates that referenced tables in the query match the authenticated user's isolated table. Access to `users` or arbitrary system tables is blocked.
4. **Auto-Limit Protection:** If the query lacks a `LIMIT` clause, SQLGlot automatically injects `LIMIT 100` to prevent memory exhaustion.
5. **No Blind Fallback Masking:** If SQL generation fails validation, the system does not silently run an unrelated fallback query; it returns:
   ```text
   I couldn't confidently translate your question into a business data query. Could you rephrase it or specify the metric you want to analyze?
   ```
