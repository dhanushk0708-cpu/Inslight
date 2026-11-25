# Structured Logging, Error Handling & Health Monitoring

## Request Correlation & Structured Logging
- `backend/app/core/logging.py` defines `request_id_ctx` (`ContextVar`) and `RequestIDFilter`, formatting every log line as:
  `YYYY-MM-DD HH:MM:SS [LEVEL] [req=<request_id>] inslight - <message>`
- `request_context_middleware` in `backend/app/main.py` reads or generates a 12-character `X-Request-ID` and returns it in every HTTP response header.

## Unified Error Responses
- `HTTPException`, `RequestValidationError` (`422`), and unhandled `Exception` (`500`) handlers in `backend/app/main.py` return consistent JSON:
  ```json
  {
    "status": "error",
    "detail": "Descriptive message without internal stack traces.",
    "request_id": "a1b2c3d4e5f6"
  }
  ```

## Health & Readiness Probes
- `GET /health` & `GET /api/v1/health`: Public service status (`healthy`).
- `GET /health/live` & `GET /api/v1/health/live`: Process liveness probe (`alive`).
- `GET /health/ready` & `GET /api/v1/health/ready`: Executes `SELECT 1` against the configured database and verifies storage directory availability (`200 ready` or `503 degraded`). Exposes zero credentials or paths.
