# Intelligent Business Alerts & Anomaly Monitoring
## Rules Engine, Deduplication & Lifecycle Management

---

### 1. Purpose & Overview
Business conditions change constantly. Inslight's Alert Engine monitors datasets and calculated metrics against configurable business rules, notifying users of critical conditions (such as low gross margin, high refund rates, or revenue drops) while preventing notification fatigue through sliding-window deduplication.

---

### 2. Architecture & Data Model

#### A. Alert Rule Definition (`AlertRule`)
- `metric`: Target metric column (e.g. `margin`, `revenue`, `return_rate`).
- `operator`: Comparison operator (`gt`, `lt`, `gte`, `lte`, `eq`).
- `threshold`: Numerical threshold boundary.
- `severity`: Alert severity level (`info`, `warning`, `critical`).
- `cooldown_hours`: Cooldown period to suppress duplicate triggers (default: 24 hours).
- `is_active`: Toggle rule active/inactive.

#### B. Triggered Alert Entity (`Alert`)
- `status`: Lifecycle state (`unread`, `read`, `resolved`).
- `triggered_value`: The actual observed metric value that tripped the threshold.
- `context_data`: JSON payload containing snapshot data and affected segments.

---

### 3. Automated Deduplication Logic
To prevent overwhelming users with redundant notifications:
$$\text{Alert Suppressed if } \exists \text{ Alert for (User, Rule, Dataset) within past } 24 \text{ hours}$$
If a critical threshold is breached multiple times within the cooldown window, existing active alerts are updated or suppressed rather than generating duplicate inbox records.

---

### 4. API Endpoints
- `GET /api/v1/alerts`: Retrieve user alerts (filterable by unread, severity).
- `POST /api/v1/alerts/scan`: Trigger evaluation of active alert rules against active dataset.
- `PATCH /api/v1/alerts/{id}/read`: Mark alert as read.
- `PATCH /api/v1/alerts/{id}/resolve`: Mark alert as resolved.
- `GET /api/v1/alerts/rules`: List custom alert rules.
- `POST /api/v1/alerts/rules`: Create new alert rule.
- `DELETE /api/v1/alerts/rules/{id}`: Delete an alert rule.
