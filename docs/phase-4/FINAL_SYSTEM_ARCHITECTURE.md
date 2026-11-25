# INSLIGHT — Final System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Next.js 14 Frontend (frontend/)                      │
│  Chat + MarkdownRenderer + Voice (STT/TTS) + Results (KPI/Charts/Cards) │
│  RCA | Forecast | Alerts | Quality | Compare | Studio | Multi-Dataset   │
│  Reports | Presentations (.pptx) | Notifications | Admin RBAC & Audit   │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │ HTTPS / REST + Bearer JWT
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (backend/app/main.py)                  │
│  RequestID Middleware • CORS • Unified JSON Error Handlers • RateLimit  │
├──────────────────────────────────┬──────────────────────────────────────┤
│        Auth & RBAC Layer         │         AI & Analytics Layer         │
│  • JWT + bcrypt + Fernet         │  • Groq LLM + BusinessContextGuard   │
│  • Roles: admin / analyst        │  • SQLGlot AST Security Validator    │
│  • AuditService (append-only)    │  • BIAgent + StrategicAnalysis       │
│  • NotificationService           │  • RCA, Forecast (sklearn), Anomaly  │
├──────────────────────────────────┼──────────────────────────────────────┤
│       Reporting & Export         │          Storage & Data Layer        │
│  • PDF (ReportLab + Matplotlib)  │  • SQLite / PostgreSQL (Alembic)     │
│  • Excel (openpyxl) & CSV        │  • Isolated per-user DuckDB files    │
│  • PowerPoint (python-pptx)      │    (data/datasets/{user_id}/*.duckdb)│
│  • Gmail OAuth2 + Scheduler      │                                      │
└──────────────────────────────────┴──────────────────────────────────────┘
```
