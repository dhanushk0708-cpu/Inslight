# INSLIGHT — Phase 1: Backend Architecture Specification

**Document ID:** `PHASE1-ARCH-01`

**Target:** `backend/`
---

## 1. Architectural Pattern: Layered Modular Monolith

Rather than introducing distributed microservices prematurely, INSLIGHT adopts a **high-cohesion, loosely coupled Modular Monolith**. This structure cleanly separates HTTP presentation, business logic, data access, and infrastructure while maintaining simple local deployment.

```text
backend/
├── alembic/                         # Database migration environment
│   ├── env.py                       # Migration runner loading SQLAlchemy Base
│   └── versions/                    # Versioned migration scripts
│
├── app/
│   ├── main.py                      # FastAPI application factory and router inclusion
│   │
│   ├── core/                        # Core system configuration
│   │   ├── config.py                # Environment variables and runtime settings
│   │   ├── database.py              # SQLAlchemy engine, sessionmaker, and Base
│   │   ├── security.py              # Bcrypt password hashing and JWT operations
│   │   └── logging.py               # Structured logging configuration
│   │
│   ├── models/                      # SQLAlchemy ORM entity definitions
│   │   ├── user.py                  # User account model
│   │   ├── dataset.py               # Dataset metadata and storage path model
│   │   └── chat.py                  # ChatSession and ChatMessage models
│   │
│   ├── schemas/                     # Pydantic DTO request and response models
│   │   ├── auth.py                  # User registration, login, and token schemas
│   │   ├── dataset.py               # Upload response and profile schemas
│   │   ├── query.py                 # Natural language query requests and visual responses
│   │   └── analytics.py             # What-if, deep-dive, and anomaly schemas
│   │
│   ├── repositories/                # Data access layer (Repository Pattern)
│   │   ├── user_repository.py       # User queries and creations
│   │   ├── dataset_repository.py    # Dataset metadata CRUD and ownership checks
│   │   └── chat_repository.py       # Chat session and message persistence
│   │
│   ├── services/                    # Business logic and external orchestrations
│   │   ├── auth_service.py          # User registration and credential verification
│   │   ├── dataset_service.py       # Safe CSV parsing, normalization, and DuckDB creation
│   │   ├── ai_service.py            # Asynchronous Groq Cloud LLM client
│   │   ├── business_guard.py        # Five-layer Business Context Guard
│   │   ├── rag_service.py           # Dataset schema metadata catalog and context retrieval
│   │   ├── sql_service.py           # SQLGlot AST validation and DuckDB execution
│   │   └── query_service.py         # End-to-end analytical pipeline
│   │
│   ├── analytics/                   # Specialized analytical calculation engines
│   │   ├── insights.py              # Multi-dimensional deep-dive analysis
│   │   ├── scenario_engine.py       # What-if scenario sensitivity simulation
│   │   └── anomaly_detection.py    # Statistical outlier detection (>2 sigma)
│   │
│   ├── utils/                       # Reusable utilities
│   │   ├── csv_reader.py            # Multi-encoding CSV streaming reader
│   │   ├── formatters.py            # Metric formatters (currency, numbers, percentages)
│   │   └── helpers.py               # JSON parsers and SQL string cleaners
│   │
│   └── api/                         # HTTP presentation layer
│       ├── deps.py                  # FastAPI dependency injection (DB, current user)
│       └── v1/
│           ├── router.py            # Master API v1 router
│           └── routes/
│               ├── auth.py          # Registration, login, and current-user endpoints
│               ├── health.py        # Service health check
│               ├── datasets.py      # CSV upload, listing, deletion, and profiling
│               ├── query.py         # Natural language analytical queries
│               ├── profile.py       # Active dataset profiling
│               ├── deep_dive.py     # Deep-dive business insights
│               ├── what_if.py       # Scenario modeling
│               └── anomalies.py     # Statistical anomaly detection
│
├── tests/                           # Automated test suite (Pytest)
│   ├── conftest.py                  # In-memory test engine and client fixtures
│   ├── test_auth.py                 # Authentication and JWT test cases
│   ├── test_dataset_isolation.py    # Multi-tenant isolation and ownership tests
│   ├── test_business_guard.py       # Business Context Guard test cases
│   ├── test_sql_security.py         # SQLGlot AST parsing and injection prevention
│   └── test_analytics.py            # Scenario and anomaly regression tests
│
├── main.py                          # Root entry point forwarding to app.main:app
└── requirements.txt                 # Python dependencies
```

---

## 2. Separation of Concerns and Clean Architecture

### 2.1 API Layer (`app/api/`)

Responsible solely for:
- Parsing HTTP requests.
- Enforcing authentication through `Depends(get_current_user)`.
- Calling the service layer.
- Returning validated Pydantic schemas.

### 2.2 Service Layer (`app/services/`)

Contains business logic and orchestration.

Services are decoupled from HTTP frameworks so they can be tested independently or invoked through CLI scripts.

### 2.3 Repository Layer (`app/repositories/`)

Isolates database querying logic.

Other layers access persistent data through repository interfaces rather than directly implementing database queries.

### 2.4 Analytics Layer (`app/analytics/`)

Contains specialized calculation algorithms, including:
- Pandas and DuckDB analytical calculations.
- Z-score calculations.
- Sensitivity modeling.
- Statistical anomaly detection.

These calculations remain decoupled from HTTP requests.