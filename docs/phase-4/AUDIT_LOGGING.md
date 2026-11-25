# Audit Logging & Activity Tracking

## Architecture
- **Model:** `backend/app/models/audit_log.py` (`AuditLog`: `id`, `user_id`, `action`, `resource_type`, `resource_id`, `status`, `request_id`, `metadata_json`, `created_at`).
- **Service:** `backend/app/services/audit_service.py` (`AuditService.log_action`, `AuditService.list_logs`).
- **Tracked Actions:** `register`, `login` (success & failure), `logout`, `dataset_upload`, `dataset_delete`, `ai_query`, `ai_agent_query`, `report_generate`, `email_send`, `pptx_generate`, `role_change`, `user_status_change`.
- **Security Controls:**
  - `_sanitize_metadata()` recursively redacts any keys containing `password`, `token`, `secret`, `api_key`, `authorization`, `jwt`, or `client_secret`.
  - Append-only API: no `PUT`, `PATCH`, or `DELETE` endpoints exist for audit logs.
  - Access restricted strictly to `admin` role via `GET /api/v1/admin/audit-logs`.
