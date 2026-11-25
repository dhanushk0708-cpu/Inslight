# API Performance & Security Controls

## Rate Limiting (`backend/app/core/rate_limit.py`)
Uses a thread-safe in-memory sliding-window `SlidingWindowRateLimiter` (no Redis required):
- **Authentication endpoints** (`/api/v1/auth/login`, `/api/v1/auth/register`): `30 requests / 60s` per client IP (`RATE_LIMIT_AUTH_PER_MIN`).
- **AI query & outline endpoints** (`/api/v1/agent/query`, `/api/v1/query`, `/api/v1/presentations/outline`): `45 requests / 60s` per client IP (`RATE_LIMIT_AI_PER_MIN`).
- Exceeding limits returns `429 Too Many Requests` with `Retry-After: 60`.
- Can be toggled via `RATE_LIMIT_ENABLED=true|false` in `.env`.

## Upload, Query & Tenant Protections
- CSV uploads capped at `100 MB` with UTF-8/CSV validation.
- All SQL queries validated via SQLGlot AST (`SELECT`-only, single statement, table/column allowlist).
- All user resources (datasets, reports, schedules, dashboards, alerts, notifications, presentations) enforce strict `user_id` ownership checks.
- Pagination (`limit`, `offset`) enforced on `/notifications` and `/admin/audit-logs` / `/admin/users`.
