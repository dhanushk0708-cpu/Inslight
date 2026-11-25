# INSLIGHT — Technical Audit: AI & RAG Readiness
**Document ID:** `AUDIT-DOC-05`
**Date of Audit:** November 2026
**Auditor:** Senior AI Engineer & LLM Systems Architect

---

## 1. Current AI Integration Architecture

The existing AI implementation is located in `backend/main.py` (lines 350–486, 788–878) and interacts with the Groq Cloud API.

```python
class LLM:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.3-70b-versatile"

    def chat(self, system: str, user: str, temp: float = 0.1) -> str:
        # Synchronous requests.post call with 30s timeout
```

### Prompts & AI Tasks in `main.py`:
1. `SQL_PROMPT`: Directs LLM to generate raw SQLite queries from user questions and table schema.
2. `SQL_FIX_PROMPT`: Directs LLM to repair failed SQL queries given the SQLite error message.
3. `CHART_PROMPT`: Directs LLM to produce JSON specifying `main_chart`, `secondary_chart`, and `kpi_cards`.
4. `STORY_PROMPT`: Generates a 2–3 sentence executive summary of the aggregated query results.
5. `SUGGEST_PROMPT`: Suggests 3 contextual follow-up business questions.
6. `PROFILE_PROMPT`: Generates 3 CXO-level business questions upon dataset upload.
7. `DEEP_DIVE_PROMPT`: Analyzes pre-aggregated metric summaries to produce revenue drivers, risk areas, and root cause descriptions.
8. `WHATIF_PROMPT`: Provides executive commentary on mathematical scenario projections.
9. `ANOMALY_PROMPT`: Evaluates statistical outliers and generates risk descriptions and recommendations.

---

## 2. AI Code Quality & Operational Deficiencies

### 2.1 Sequential Latency Waterfall in `/api/query`
When a user asks a question, `process_query()` executes up to four sequential, blocking LLM calls:
```
User Question
    │
    ▼ (1) LLM.chat(SQL_PROMPT)       --> Latency: ~600ms - 1500ms
Execute SQL Query
    │
    ▼ (2) LLM.chat(CHART_PROMPT)     --> Latency: ~800ms - 2000ms
    │
    ▼ (3) LLM.chat(STORY_PROMPT)     --> Latency: ~500ms - 1200ms
    │
    ▼ (4) LLM.chat(SUGGEST_PROMPT)   --> Latency: ~400ms - 1000ms
    │
    └─► Combined Total Latency: 2.3s - 5.7s per single question!
```
- Steps 2, 3, and 4 depend only on the SQL execution results and could run in **parallel** via `asyncio.gather()`. In the current codebase, they run sequentially, severely degrading perceived performance.

### 2.2 Lack of Asynchronous SDK Usage
- `requirements.txt` specifies `groq==0.12.0`, but the code uses Python's standard `requests` library.
- Using `requests.post()` inside an ASGI framework blocks worker threads and forfeits native connection pooling, HTTP/2 multiplexing, automatic backoff retries, and streaming responses provided by `AsyncGroq`.

### 2.3 Hallucination Risks & Inadequate SQL Guardrails
- **Column Hallucination:** Even with schema injection, LLMs frequently invent columns (e.g., `profit_margin`, `region_name`) or assume standard table naming conventions not present in arbitrary user datasets.
- **Syntactic vs. Semantic Correctness:** A generated SQL query may be syntactically valid in SQLite, but semantically flawed from a business logic perspective (e.g., executing `SUM(unit_price)` instead of `SUM(unit_price * quantity)`).
- **Keyword Fallback Obfuscation:** If the query fails, `build_fallback_query` substitutes a hardcoded heuristic query without notifying the user that the LLM was unable to understand their question.

### 2.4 Token Consumption & Cost Inefficiencies
- Prompt formatting embeds full PRAGMA column listings, type descriptions, and up to 6 distinct sample values per column.
- For datasets with 50+ columns, schema context alone consumes 2,000–4,000 tokens per prompt invocation.
- Without semantic schema pruning or vector embeddings, token costs and Groq rate-limit consumption scale linearly with column count.

---

## 3. RAG Readiness Assessment

The project currently has **0% RAG readiness**:
- No embeddings generation pipeline.
- No vector database (e.g., Chroma, Qdrant, pgvector).
- No semantic chunking or indexing of unstructured domain knowledge.
- No business context guard to validate whether user questions pertain to the loaded dataset.

### Required Capabilities to Reach RAG & AI Agent Readiness:

1. **AI Business Context Guard:**
   - A classification layer that intercepts queries before SQL generation.
   - Categorizes queries into:
     - `IN_SCOPE_ANALYTICAL` (e.g., "What was our Q2 margin?") -> proceeds to SQL generation.
     - `OUT_OF_SCOPE` (e.g., "Write a poem about dogs") -> politely rejected without database execution.
     - `AMBIGUOUS / METRIC_CLARIFICATION` -> prompts user for clarification.
2. **Dataset-Aware Schema RAG:**
   - Rather than passing 100 columns into the prompt, compute embeddings for column headers, semantic data types, and business descriptions.
   - Retrieve only the top-K relevant columns for the specific user question.
3. **AST SQL Parser & Validator (SQLGlot):**
   - Replace primitive blacklist checks (`if "DROP" in upper`) with Abstract Syntax Tree (AST) parsing via `sqlglot`.
   - Enforce read-only semantics (`SELECT` statements only).
   - Restrict table access exclusively to the user's authorized dataset view.
4. **Parallelized Multi-Agent Orchestration:**
   - Refactor the 4-step pipeline into an asynchronous agentic workflow where SQL generation, chart selection, and executive storytelling execute cooperatively with structured Pydantic output parsers.
