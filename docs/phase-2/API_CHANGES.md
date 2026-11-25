# INSLIGHT — Phase 2 API Reference
**New Endpoints & Request/Response Schemas**

---

## 1. Reports API (`/api/v1/reports`)

### `POST /api/v1/reports/generate`
Generate a new PDF, Excel, or CSV report from real dataset analytics.
- **Auth:** `Bearer <JWT>`
- **Request Body (`ReportGenerateRequest`):**
  ```json
  {
    "dataset_id": "optional-uuid",
    "title": "Executive Performance Digest",
    "report_format": "pdf",
    "include_anomalies": true,
    "include_kpis": true,
    "custom_query_data": null
  }
  ```
- **Response (`ReportResponse`):**
  ```json
  {
    "id": "report-uuid",
    "user_id": "user-uuid",
    "dataset_id": "dataset-uuid",
    "name": "Executive Performance Digest",
    "report_format": "pdf",
    "file_size": 28400,
    "status": "generated",
    "created_at": "2026-11-24T13:20:00Z"
  }
  ```

### `GET /api/v1/reports`
List all reports owned by the authenticated user.
- **Auth:** `Bearer <JWT>`
- **Response:** `Array<ReportResponse>`

### `GET /api/v1/reports/{report_id}`
Fetch report metadata with ownership check.
- **Auth:** `Bearer <JWT>`

### `GET /api/v1/reports/{report_id}/download`
Download the report document (`FileResponse`).
- **Auth:** `Bearer <JWT>`
- **Headers:** Content-Type (`application/pdf`, `application/vnd.openxmlformats...`, `text/csv`)

### `DELETE /api/v1/reports/{report_id}`
Delete a report record and remove the file from disk.
- **Auth:** `Bearer <JWT>`

### `POST /api/v1/reports/email`
Send an email with the report attached via Gmail API.
- **Auth:** `Bearer <JWT>`
- **Request Body (`EmailSendRequest`):**
  ```json
  {
    "report_id": "report-uuid",
    "recipients": ["cfo@company.com"],
    "cc_recipients": ["analyst@company.com"],
    "subject": "Monthly BI Report",
    "body": "Attached is the report."
  }
  ```
- **Response (`EmailSendResponse`):**
  ```json
  {
    "status": "success",
    "message": "Report emailed successfully via Gmail API.",
    "gmail_message_id": "18c123456789abcdef",
    "recipients": ["cfo@company.com"],
    "delivered_at": "2026-11-24T13:21:00Z"
  }
  ```

---

## 2. Scheduled Reports API (`/api/v1/reports/schedules`)

### `POST /api/v1/reports/schedules`
Create an automated schedule.
- **Auth:** `Bearer <JWT>`
- **Request Body:**
  ```json
  {
    "dataset_id": "dataset-uuid",
    "report_name": "Weekly Executive Digest",
    "frequency": "weekly",
    "report_format": "pdf",
    "recipients": ["manager@company.com"],
    "email_subject": "Weekly KPI Update",
    "email_body": "Here is the weekly performance update.",
    "is_active": true
  }
  ```

### `GET /api/v1/reports/schedules`
List schedules belonging to the user.
- **Auth:** `Bearer <JWT>`

### `PUT /api/v1/reports/schedules/{schedule_id}`
Update schedule parameters or toggle active status.
- **Auth:** `Bearer <JWT>`

### `DELETE /api/v1/reports/schedules/{schedule_id}`
Delete schedule with ownership check.
- **Auth:** `Bearer <JWT>`

---

## 3. Gmail Integration API (`/api/v1/integrations/gmail`)

### `GET /api/v1/integrations/gmail/authorize`
Generate Google OAuth 2.0 authorization URL.
- **Auth:** `Bearer <JWT>`
- **Response:**
  ```json
  {
    "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...&state=..."
  }
  ```

### `GET /api/v1/integrations/gmail/callback`
OAuth 2.0 callback endpoint invoked by Google redirect.
- **Query Params:** `code`, `state`
- **Response:** Redirects to `http://localhost:3000?gmail_connected=true`

### `GET /api/v1/integrations/gmail/status`
Check connection status for authenticated user.
- **Auth:** `Bearer <JWT>`
- **Response:**
  ```json
  {
    "is_connected": true,
    "email": "user@gmail.com",
    "provider": "google"
  }
  ```

### `POST /api/v1/integrations/gmail/disconnect`
Disconnect Gmail integration and revoke saved access.
- **Auth:** `Bearer <JWT>`
