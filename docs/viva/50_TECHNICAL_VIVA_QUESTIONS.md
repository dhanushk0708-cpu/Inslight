# INSLIGHT — 50 Technical Viva Questions & Answers

1. **What is INSLIGHT?**
   INSLIGHT is an AI-powered Business Intelligence platform built with FastAPI, Next.js, DuckDB, and scikit-learn that lets users analyze CSV datasets via natural language and voice, detect anomalies, forecast trends, and export PDF, Excel, and PowerPoint reports.
2. **Why did you choose FastAPI for the backend?**
   FastAPI offers async I/O for LLM API calls, automatic OpenAPI documentation, and strict Pydantic v2 request/response validation.
3. **Why do you use DuckDB alongside SQLite/PostgreSQL?**
   SQLite/PostgreSQL stores transactional metadata (users, reports, alerts, audit logs), while DuckDB runs fast columnar OLAP aggregations directly on uploaded datasets.
4. **How do you ensure multi-tenant dataset isolation?**
   Every dataset is stored in `data/datasets/{user_id}/{dataset_id}.duckdb`, and every repository query filters by `user_id == current_user.id`.
5. **How does the Business Context Guard work?**
   It uses a 2-layer pipeline: Layer 1 deterministic regex matching for fast allow/reject decisions, and Layer 2 LLM classification for ambiguous queries.
6. **How do you prevent SQL injection from LLM-generated queries?**
   `SQLService.validate_sql` parses the SQL into an Abstract Syntax Tree using `sqlglot`, rejecting non-`SELECT` statements, multi-statements, DDL/DML, and unauthorized tables.
7. **What is RAG in the context of INSLIGHT?**
   `RAGService` retrieves the active dataset's exact schema, data types, sample values, and stats and injects them into the LLM prompt so the model never hallucinates column names.
8. **How does the AI BI Agent avoid hallucinating numbers?**
   It routes questions to deterministic DuckDB and scikit-learn services first and only uses the LLM to summarize verified numerical outputs.
9. **What happens when an ad-hoc SQL query is too broad?**
   The BI Agent automatically upgrades it to `StrategicAnalysisService` to compute KPIs, segment rankings, opportunities, and risks.
10. **How did you validate cross-sell recommendations?**
    By checking for an `order_id`/transaction column and running a DuckDB self-join co-occurrence query; without basket IDs, it is labeled a `[Business Hypothesis — Requires Validation]`.
11. **Why shouldn't low sales volume be called "inventory drag"?**
    Low sales volume alone does not prove stock accumulation; unless inventory/stock columns exist, INSLIGHT strictly reports "Low Product Sales Velocity".
12. **When does INSLIGHT use the term "margin compression"?**
    Only when historical period-over-period margin queries show an actual decline; otherwise it reports "Below-Average Profitability".
13. **How does Root Cause Analysis work?**
    It decomposes period-over-period metric variance across categorical dimensions (contribution share %) and performs Price vs. Volume decomposition.
14. **Explain Price vs. Volume decomposition.**
    Revenue change $\Delta R$ is split into Price Effect $(P_1 - P_0) \times Q_1$ and Volume Effect $(Q_1 - Q_0) \times P_0$.
15. **Which forecasting models are implemented?**
    Moving Average, Holt's Linear Exponential Smoothing, Ridge Linear Regression, and Random Forest Regressor (`scikit-learn`).
16. **How does INSLIGHT select the best forecasting model?**
    It backtests candidate models on a hold-out split and selects the model with the lowest MAPE (alongside MAE and RMSE).
17. **How are forecast confidence intervals calculated?**
    Using residual standard deviation $\sigma_e$: $\hat{Y}_{t+h} \pm 1.96 \cdot \sigma_e \cdot \sqrt{1 + h/N}$.
18. **What happens if a dataset has fewer than 5 time points for forecasting?**
    A data-insufficiency guard returns a clean diagnostic message instead of crashing or overfitting.
19. **Which anomaly detection algorithms are used?**
    Z-Score ($|Z| > 2.5$), Interquartile Range (IQR), and unsupervised Isolation Forest (`scikit-learn`).
20. **How are anomalies classified for business action?**
    Positive revenue/margin spikes are tagged as commercial opportunities, while drops or cost spikes are tagged as negative risks.
21. **How does the Business Alert engine prevent alert fatigue?**
    By checking a 24-hour deduplication window per `(user_id, dataset_id, metric_name)` before inserting a new alert.
22. **How is the Data Quality Score computed?**
    A 0–100 score penalized by missing values, duplicate rows, casing inconsistencies, and negative values in positive measures.
23. **Does Data Quality cleaning overwrite the user's raw file?**
    No, the cleaned preview is computed non-destructively in memory.
24. **How does Comparative Analytics handle zero baselines?**
    Safe zero-denominator guards prevent `ZeroDivisionError` when calculating percentage change.
25. **How does Multi-Dataset Relational Intelligence prevent Cartesian explosions?**
    `RelationshipService` inspects distinct key ratios on both datasets and raises high-risk warnings if cardinality is `many_to_many`.
26. **How are passwords stored?**
    Hashed with `bcrypt` using per-password random salts (`bcrypt.gensalt()`).
27. **How are JWT tokens structured and validated?**
    Signed with `HS256` containing `sub` (user ID), `iat`, and `exp`; validated on every protected route via `HTTPBearer`.
28. **How are Gmail OAuth tokens protected at rest?**
    Encrypted symmetrically using `cryptography.fernet` before storage in `oauth_credentials`.
29. **How is CSRF prevented during the Gmail OAuth callback?**
    The `state` query parameter carries a short-lived signed JWT bound to the initiating `user_id`.
30. **How does Excel export prevent CSV/Formula Injection?**
    Cells starting with `=`, `+`, `-`, or `@` are prefixed/escaped before writing to the workbook.
31. **How does the PDF Report Generator build charts?**
    `ReportVisualizer` renders high-DPI `matplotlib` PNGs in memory and embeds them into `ReportLab` flowables.
32. **How does the AI PowerPoint Generator work?**
    First it computes verified metrics via DuckDB and returns an editable slide outline; after user approval, `python-pptx` builds a 16:9 `.pptx` deck with embedded charts.
33. **How does Voice Input support English, Hindi, and Kannada?**
    `VoiceInput.tsx` uses the browser's Web Speech API (`SpeechRecognition`) and sets `recognition.lang` to `en-IN`, `hi-IN`, or `kn-IN`.
34. **Why doesn't Voice Input auto-submit the query?**
    Transcripts populate an editable input field so users can review/correct speech recognition errors before explicit submission.
35. **How does RBAC work in INSLIGHT?**
    Users have a `role` (`analyst` or `admin`). Protected admin endpoints enforce `Depends(require_admin)`, returning `403 Forbidden` to analysts.
36. **How is the first Admin user created securely?**
    Via `backend/scripts/create_admin.py` using interactive password prompting, avoiding hardcoded default admin passwords.
37. **Can an Admin demote or deactivate themselves?**
    No, `admin.py` explicitly blocks self-demotion and self-deactivation with `400 Bad Request`.
38. **What does AuditService log and how are secrets protected?**
    It logs user ID, action, resource, status, and `request_id`, and recursively redacts any keys matching `password`, `token`, `secret`, `api_key`, or `jwt`.
39. **How does the Notification Center avoid duplicate notifications?**
    Using a `dedup_key` checked over a 24-hour sliding window per user.
40. **How are requests traced across logs and error responses?**
    `request_context_middleware` assigns an `X-Request-ID` stored in a `ContextVar` and injects it into both log lines and JSON error responses.
41. **How does rate limiting work without Redis?**
    `SlidingWindowRateLimiter` uses a thread-safe `collections.deque` per client IP in memory, returning `429 Too Many Requests` on bursts.
42. **What is the difference between `/health/live` and `/health/ready`?**
    `/health/live` confirms the FastAPI process is running; `/health/ready` executes `SELECT 1` on the database and checks storage writability.
43. **How are database schema changes managed?**
    Using Alembic migrations (`b4280f8d0630` -> `c7391abf0831` -> `2604d90ecb63`).
44. **How do you back up SQLite safely while the app is running?**
    `scripts/backup_db.py` uses Python's `sqlite3.Connection.backup()` API for a consistent online snapshot.
45. **How does the Scheduled Reports background loop avoid duplicate runs?**
    After generating/sending a due report, `SchedulerService` advances `next_run_at` (+7 or +30 days) and commits immediately.
46. **How does the frontend render AI Markdown responses safely?**
    `MarkdownRenderer.tsx` parses headings, bold, italic, code, and nested lists into React elements without `dangerouslySetInnerHTML`.
47. **What does the GitHub Actions CI pipeline check?**
    It runs `alembic upgrade head`, the full `pytest` suite, `npx tsc --noEmit`, and `npm run build` on pushes and PRs.
48. **Why is `frontend-react/` untouched?**
    It is a separate legacy React workspace explicitly excluded from Phase 1–4 modifications; `frontend/` (Next.js) is the active application.
49. **What are the main limitations of the current system?**
    In-memory rate limiting (single-process), UTC-only schedule intervals, and external Gmail OAuth requiring Google Cloud test-user setup.
50. **How would you scale INSLIGHT for 10,000 concurrent users?**
    Migrate metadata DB to managed PostgreSQL, move `SlidingWindowRateLimiter` to Redis, store `.duckdb`/reports in object storage (S3), and run multiple Uvicorn workers behind an HTTPS load balancer.
