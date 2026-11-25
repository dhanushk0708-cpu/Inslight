# Role-Based Access Control (RBAC)

## Roles
1. **`analyst` (Default):** Can upload and manage their own datasets, run AI analytics/BI Agent queries, generate reports and PowerPoint decks, configure alerts, manage dashboards, and manage their own scheduled reports. Blocked (`403 Forbidden`) from all `/api/v1/admin/*` endpoints.
2. **`admin`:** Full analyst capabilities plus user management (`GET /api/v1/admin/users`, `PATCH /api/v1/admin/users/{id}/role`, `PATCH /api/v1/admin/users/{id}/status`), audit log review (`GET /api/v1/admin/audit-logs`), and sanitized system status (`GET /api/v1/admin/system-status`).

## Safeguards
- Enforced server-side via `require_admin` dependency in `backend/app/api/deps.py`.
- Administrators cannot demote or deactivate their own accounts (`400 Bad Request`).
- No hardcoded default admin password exists anywhere in the codebase.

## Creating the First Administrator Securely
From the `backend/` directory:
```cmd
.venv\Scripts\python.exe scripts\create_admin.py --email admin@inslight.ai --name "System Admin"
```
The script prompts interactively for a password (minimum 8 characters) or promotes an existing user by email.
