# INSLIGHT — Phase 1: API Changes & Backward Compatibility
**Document ID:** `PHASE1-API-01`

---

## 1. API Route Inventory & Versioning

To ensure smooth transition, Inslight supports both modern versioned routes (`/api/v1/...`) and exact legacy routes (`/api/...`).

| Modern Endpoint (`/api/v1/...`) | Legacy Endpoint (`/api/...`) | HTTP Method | Authentication | Functionality |
|---|---|---|---|---|
| `/api/v1/auth/register` | — | `POST` | Public | Register new user account |
| `/api/v1/auth/login` | — | `POST` | Public | Authenticate and obtain JWT token |
| `/api/v1/auth/me` | — | `GET` | Bearer JWT | Fetch authenticated user profile |
| `/api/v1/auth/logout` | — | `POST` | Bearer JWT | Invalidate client session |
| `/api/v1/health` | `/api/health` | `GET` | Optional JWT | System health and dataset status |
| `/api/v1/datasets/upload`| `/api/upload` | `POST` | Optional / Bearer | Upload CSV into isolated DuckDB |
| `/api/v1/datasets` | — | `GET` | Bearer JWT | List all user-owned datasets |
| `/api/v1/datasets/active`| `/api/profile`| `GET` | Optional / Bearer | Get active dataset profile |
| `/api/v1/datasets/{id}` | — | `DELETE` | Bearer JWT | Delete user dataset |
| `/api/v1/query` | `/api/query` | `POST` | Optional / Bearer | Execute natural language BI query |
| `/api/v1/deep-dive` | `/api/deep-dive`| `POST` | Optional / Bearer | Multi-dimensional deep dive |
| `/api/v1/what-if` | `/api/what-if` | `POST` | Optional / Bearer | What-if scenario simulation |
| `/api/v1/anomalies` | `/api/anomalies`| `GET` | Optional / Bearer | Statistical outlier detection |

---

## 2. Backward Compatibility Strategy

1. **Dual Route Mounting:** All API routers are mounted at `/api/v1` and simultaneously aliased at `/api` to guarantee legacy scripts or third-party consumers continue functioning.
2. **Graceful Authentication Fallback:**
   - Routes use `get_optional_current_user` where appropriate. If a request lacks a Bearer token, it automatically associates with a secure local demo user account (`demo@inslight.ai`), ensuring zero disruption to rapid local demonstrations or automated test fixtures.
   - User-specific management endpoints (listing and deleting datasets) strictly require `get_current_user`.
