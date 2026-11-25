# Autonomous AI BI Agent
## Architecture, Orchestration & Safeguards

---

### 1. Architectural Concept
The **Inslight AI BI Agent** (`BIAgentService`) serves as an intelligent co-pilot for business executives, managers, and data analysts. Unlike simple chat wrappers that generate hallucinations or ungrounded SQL queries, the BI Agent utilizes a **multi-step reasoning loop**:
1. **Business Context Guard:** Filters out off-topic, malicious, or unanswerable queries before triggering LLM calls.
2. **Intent Classification & Routing:** Classifies user intent into distinct analytical tools:
   - Root Cause Analysis (`rca`)
   - Time Series Forecasting (`forecast`)
   - Anomaly Detection (`anomaly`)
   - Period / Segment Comparison (`compare`)
   - Direct Metric / SQL Retrieval (`query`)
3. **Tool Execution:** Executes deterministic computational algorithms (DuckDB SQL aggregations, Scikit-learn regressors, statistical anomaly detectors) on the user's active dataset.
4. **Evidence-Backed Synthesis:** Formulates actionable executive conclusions using the real computational output.
5. **Transparency & Audit Trail:** Emits step-by-step reasoning logs (`thought`, `action`, `observation`) back to the frontend UI so users can audit the AI's internal process.

---

### 2. Guardrails & Security
- **Strict Data Isolation:** The agent only accesses datasets owned by the authenticated `current_user.id`.
- **SQL Injection Prevention:** All SQL queries are sanitized through `SQLSecurityService`, strictly prohibiting DDL, DML, file operations (`read_csv`, `COPY`), and unbounded multi-statement execution.
- **Off-Topic Rejection:** Questions unrelated to the business domain or uploaded data are gracefully rejected with a helpful suggestion message.

---

### 3. API Contract
- **Endpoint:** `POST /api/v1/agent/query`
- **Request Body:**
  ```json
  {
    "query": "Why did electronics revenue drop in November compared to October?",
    "dataset_id": "optional-uuid"
  }
  ```
- **Response Structure:**
  ```json
  {
    "query": "Why did electronics revenue drop...",
    "intent": "rca",
    "summary": "Revenue dropped by ₹1,42,000 primarily due to 28% drop in SKU-104 sales volume.",
    "steps": [
      {
        "step": 1,
        "thought": "Decomposing revenue change across product categories and SKUs",
        "action": "execute_rca",
        "observation": "Found significant negative volume contribution in Electronics."
      }
    ],
    "data": { ... },
    "recommendations": [
      "Review supplier inventory for SKU-104",
      "Investigate promotional campaigns run during October"
    ]
  }
  ```
