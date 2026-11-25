# INSLIGHT — Technical Audit: Project Overview
**Document ID:** `AUDIT-DOC-01`
**Date of Audit:** November 2026
**Auditor Roles:** Senior Software Architect, Senior Full-Stack Engineer, Backend Architect, AI Engineer, Database Engineer, Application Security Auditor
**Scope:** Entire repository (`dash-ai` / Inslight) with strict read-only compliance for application source code.

---

## 1. Executive Project Summary

**Inslight** (labeled in legacy source code and manifests as `DASH.AI` / `dash-ai`) is an AI-powered conversational Business Intelligence (BI) assistant designed to allow business users and executives to analyze structured tabular datasets using natural language instead of writing complex SQL queries or building manual BI dashboards.

The application ingests tabular CSV files, profiles dataset schema and data quality, translates natural language inquiries into SQL dialect queries, executes them against an embedded database engine, and synthesizes the returned tabular records into dynamic Key Performance Indicator (KPI) cards, data visualizations (bar, line, and pie charts), and executive text narratives with actionable business recommendations.

Additionally, the application offers three analytical exploration features:
1. **Deep Dive Analysis:** Identifies top revenue drivers, risk categories, root cause summaries, and strategic recommendations.
2. **What-If Scenario Simulator:** Adjusts price, discount, and unit volume assumptions via interactive sliders and calculates projected revenue impacts.
3. **Anomaly Detection:** Performs statistical Z-score outlier detection across numeric features and flags notable month-over-month revenue drops.

---

## 2. Repository Layout & Workspace Structure

```
dash-ai/
├── .git/                      # Git repository metadata
├── .gitignore                 # Root gitignore file
├── README.md                  # Hackathon project documentation
├── package-lock.json          # Root npm lockfile (minimal placeholder)
│
├── backend/                   # Python FastAPI Backend
│   ├── .env                   # Local environment file (GROQ_API_KEY)
│   ├── main.py                # Monolithic backend file (1,342 lines)
│   ├── requirements.txt       # Python package dependencies
│   ├── runtime.txt            # Python runtime specification (python-3.11.9)
│   ├── data/
│   │   └── sample_sales.csv   # Seed dataset (97 rows of retail sales data)
│   └── .venv/ / venv/         # Local virtual environments
│
├── frontend/                  # Next.js 14 App Router Frontend (PRIMARY TARGET)
│   ├── .env.local             # Local frontend environment config
│   ├── next.config.js         # Next.js build configuration (reactStrictMode: true)
│   ├── package.json           # Node.js dependencies & scripts
│   ├── package-lock.json      # Node.js dependency lockfile
│   ├── postcss.config.js      # PostCSS configuration for Tailwind
│   ├── tailwind.config.js     # Tailwind CSS theme configuration
│   ├── tsconfig.json          # TypeScript compiler configuration (strict: false)
│   └── src/
│       └── app/
│           ├── globals.css    # Global CSS definitions
│           ├── layout.tsx     # Root App Router layout
│           └── page.tsx       # Monolithic frontend page (1,082 lines)
│
└── frontend-react/            # Legacy Vite + React SPA (PRESERVED & FROZEN)
    ├── package.json           # React 18, Vite, Tailwind dependencies
    ├── vite.config.js         # Vite bundler configuration
    └── src/                   # Multi-file component tree (read-only reference)
```

---

## 3. Technology Stack & Installed Versions

| Component | Technology | Version | Purpose / Status |
|---|---|---|---|
| **Primary Frontend** | Next.js (App Router) | `14.0.4` | Application layout, SSR framework, and client UI |
| | React / React DOM | `18.2.0` | UI rendering library |
| | TypeScript | `5.3.3` | Type system (`strict: false` in current config) |
| | Tailwind CSS | `3.4.0` | Utility CSS framework (partially bypassed by inline styles) |
| | Recharts | `2.10.3` | Charting library (**declared in package.json but unused in page.tsx**) |
| | Lucide React | `0.303.0` | Icon system (**declared in package.json but unused in page.tsx**) |
| | React Dropzone | `14.2.3` | File drag-and-drop (**declared in package.json but unused in page.tsx**) |
| **Backend Framework** | FastAPI | `0.104.1` | REST API framework |
| | Uvicorn | `0.24.0` | ASGI web server |
| | Python Runtime | `3.11.9` | CPython interpreter specified in `runtime.txt` |
| | Pydantic | In bundled FastAPI | Request validation schemas |
| **Data Engine** | Pandas | `2.1.4` | In-memory data manipulation, type coercion, profiling |
| | NumPy | `1.26.4` | Numerical operations, outlier std dev calculation |
| | SQLite (`sqlite3`) | Standard Library | Embedded SQL query engine (`:memory:` database) |
| **AI Integration** | Groq API | HTTP REST | External LLM inference endpoint |
| | Groq Python SDK | `0.12.0` | Installed in virtualenv (**bypassed in main.py via raw `requests.post`**) |
| | Model | `llama-3.3-70b-versatile` | Hardcoded model identifier in `LLM` class |
| **Legacy Frontend** | Vite + React | React 18.2.0 | Preserved separate frontend application (frozen) |

---

## 4. End-to-End Application Execution Flow

```
[User Browser (Next.js)]
       │
       ▼ (1) Upload CSV or Ask Question
[FastAPI Backend (main.py)]
       │
       ├─► [CSV Upload Flow]
       │        │
       │        ├─► read_csv_safe(): Fallback encoding detection (UTF-8 -> cp1252 -> Latin-1)
       │        ├─► DatabaseManager._process(): Column normalization, date parsing, numeric cleaning
       │        ├─► df.to_sql(table_name, conn, if_exists="replace")
       │        ├─► CREATE INDEX IF NOT EXISTS on candidate columns
       │        └─► profile_data(): Computes nulls, types, quality score, LLM CXO questions
       │
       └─► [Query Processing Flow]
                │
                ├─► Step 1: LLM.chat(SQL_PROMPT) generates SQLite SQL (or build_fallback_query)
                ├─► Step 2: smart_execute() executes query, retries with SQL_FIX_PROMPT on error
                ├─► Step 3: LLM.chat(CHART_PROMPT) generates JSON dashboard configuration
                ├─► Step 4: LLM.chat(STORY_PROMPT) generates executive narrative
                ├─► Step 5: LLM.chat(SUGGEST_PROMPT) generates follow-up question array
                └─► Response JSON returned to Next.js client for rendering
```

---

## 5. Implementation vs. Documentation Discrepancies

A comparative evaluation between the project `README.md` and actual code revealed multiple discrepancies:

1. **Voice Query Support Claim:**
   - *README Claim:* Section "Voice Query Support — Users can ask questions using voice through browser speech recognition".
   - *Actual Code:* `frontend/src/app/page.tsx` contains zero Web Speech API or microphone integration code. No speech-to-text listener exists in the active Next.js interface.
2. **UI Dependency Utilization:**
   - *README Claim:* Lists `Recharts` and `Lucide Icons` as core frontend technologies.
   - *Actual Code:* `package.json` installs `recharts` (`2.10.3`) and `lucide-react` (`0.303.0`), but `frontend/src/app/page.tsx` imports neither. It renders hand-calculated `<svg>` elements and raw Unicode emojis.
3. **Groq SDK Utilization:**
   - *README Claim:* Implements Groq API.
   - *Actual Code:* `requirements.txt` specifies `groq==0.12.0`, but `backend/main.py` ignores the installed Groq client library and directly executes blocking `requests.post()` calls to `https://api.groq.com/openai/v1/chat/completions`.
4. **AI Model Discrepancy:**
   - *README Claim:* "Llama-3 Large Language Model".
   - *Actual Code:* `main.py` hardcodes `self.model = "llama-3.3-70b-versatile"`.
5. **Database Multi-Tenancy & Persistence:**
   - *README Claim:* Architecture diagram implies a clean database tier.
   - *Actual Code:* Database is an ephemeral, volatile in-memory SQLite database (`:memory:`) bound to a single shared global instance.
