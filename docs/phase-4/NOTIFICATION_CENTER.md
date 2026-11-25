# Notification Center

## Architecture
- **Model:** `backend/app/models/notification.py` (`Notification`: `id`, `user_id`, `category`, `title`, `message`, `is_read`, `resource_type`, `resource_id`, `dedup_key`, `created_at`).
- **Service:** `backend/app/services/notification_service.py` (`NotificationService`) with 24-hour `dedup_key` suppression and strict `user_id` ownership filtering.
- **API Endpoints:**
  - `GET /api/v1/notifications` (filterable by `category`, `unread_only`, paginated)
  - `GET /api/v1/notifications/unread-count`
  - `PATCH /api/v1/notifications/{id}/read`
  - `PATCH /api/v1/notifications/read-all`
  - `DELETE /api/v1/notifications/{id}`
- **Event Integrations:**
  - Business alerts (`AlertService._create_or_deduplicate_alert`)
  - Manual PDF/Excel/CSV report generation (`routes/reports.py`)
  - Email delivery failures (`routes/reports.py` and `SchedulerService`)
  - Scheduled report execution (`SchedulerService`)
  - PowerPoint deck generation (`routes/presentations.py`)
- **Frontend UI:** `frontend/src/features/notifications/NotificationsPanel.tsx` + 30-second unread count polling in `page.tsx`.
