# INSLIGHT — Scheduled Reports Architecture
**Phase 2: In-Process Automated Reporting**

---

## 1. Overview

The Scheduled Reports module enables users to configure automated recurring executive digests (weekly or monthly) delivered directly to stakeholder email inboxes.

---

## 2. Design Principles (College Project Focus)

To avoid excessive operational overhead:
- **No Heavy Infrastructure:** Celery, Redis, RabbitMQ, and external crontab daemons were deliberately avoided.
- **Lightweight Async Task Loop:** Uses standard Python `asyncio` task loop running inside FastAPI's application lifespan.
- **Resilient Execution:** Failed tasks update `last_status = 'failed'` without crashing the loop. Next run times advance predictably.

---

## 3. Database Schema (`scheduled_reports`)

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | Primary Key | UUID identifier |
| `user_id` | `VARCHAR(36)` | Foreign Key (`users.id` CASCADE), Index | Schedule creator |
| `dataset_id` | `VARCHAR(36)` | Foreign Key (`datasets.id` CASCADE), Index | Target analytical dataset |
| `report_name` | `VARCHAR(255)` | Non-null | Name of the recurring report |
| `frequency` | `VARCHAR(20)` | Non-null | Frequency: `weekly` or `monthly` |
| `report_format`| `VARCHAR(20)` | Default `'pdf'` | Format: `pdf`, `excel`, `both` |
| `recipients` | `VARCHAR(500)` | Non-null | Comma-separated recipient list |
| `email_subject`| `VARCHAR(255)`| Non-null | Email subject line |
| `email_body` | `TEXT` | Non-null | Email text body |
| `is_active` | `BOOLEAN` | Default `True` | Active status toggle |
| `next_run_at` | `DATETIME` | Non-null, Index | Next scheduled trigger time |
| `last_run_at` | `DATETIME` | Nullable | Previous execution timestamp |
| `last_status` | `VARCHAR(50)` | Default `'pending'` | Status: `pending`, `success`, `failed` |
| `created_at` | `DATETIME` | Non-null, default UTC now | Schedule creation date |

---

## 4. Execution Workflow

```text
[FastAPI Lifespan Startup]
        │
        ▼
SchedulerService.start() ──► Runs _loop() every 60s
                                    │
                                    ▼
                          execute_due_schedules()
                                    │
               ┌────────────────────┴────────────────────┐
               │                                         │
        (No due jobs)                             (Found due jobs)
               │                                         │
          Sleep 60s                                      ▼
                                            Resolve User & Dataset
                                                         │
                                                         ▼
                                            Synthesize Report (PDF/Excel)
                                                         │
                                                         ▼
                                            Send via Gmail API
                                                         │
                                                         ▼
                                            Advance next_run_at (+7d / +30d)
                                            Update last_status = 'success'
```

---

## 5. Frequency Advancement Logic

```python
if schedule.frequency == "weekly":
    schedule.next_run_at = now + timedelta(days=7)
elif schedule.frequency == "monthly":
    schedule.next_run_at = now + timedelta(days=30)
```
Duplicate triggers are prevented by immediately recording `last_run_at` and advancing `next_run_at` within the same database transaction.
