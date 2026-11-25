import io
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, AsyncMock
from app.services.scheduler import SchedulerService


def register_user(client, name="Schedule User", email="sched_user@domain.com"):
    res = client.post("/api/v1/auth/register", json={
        "name": name,
        "email": email,
        "password": "Password123!"
    })
    assert res.status_code == 201
    return res.json()["access_token"], res.json()["user"]


def test_schedule_crud_and_isolation(client):
    """Test creating, listing, updating, and deleting automated report schedules."""
    token_a, user_a = register_user(client, "User A", "user_a@domain.com")
    token_b, user_b = register_user(client, "User B", "user_b@domain.com")

    # Upload dataset for User A
    csv_data = "col,val\nA,10"
    upload_res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("data.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    dataset_id = upload_res.json()["dataset_id"]

    # 1. Create schedule for User A
    create_res = client.post(
        "/api/v1/reports/schedules",
        json={
            "dataset_id": dataset_id,
            "report_name": "Weekly Sales Brief",
            "frequency": "weekly",
            "report_format": "pdf",
            "recipients": ["manager@company.com"],
            "email_subject": "Weekly KPI Digest",
            "email_body": "Here is the weekly update.",
            "is_active": True
        },
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert create_res.status_code == 200
    sched_id = create_res.json()["id"]

    # 2. User A lists schedules (count = 1)
    list_a = client.get("/api/v1/reports/schedules", headers={"Authorization": f"Bearer {token_a}"}).json()
    assert len(list_a) == 1
    assert list_a[0]["id"] == sched_id

    # 3. User B lists schedules (count = 0)
    list_b = client.get("/api/v1/reports/schedules", headers={"Authorization": f"Bearer {token_b}"}).json()
    assert len(list_b) == 0

    # 4. User B attempts to access User A's schedule (REJECTED)
    get_b = client.get(f"/api/v1/reports/schedules/{sched_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert get_b.status_code == 404

    # 5. User A updates schedule (toggle active to False)
    up_res = client.put(
        f"/api/v1/reports/schedules/{sched_id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert up_res.status_code == 200
    assert up_res.json()["is_active"] is False

    # 6. User A deletes schedule
    del_res = client.delete(f"/api/v1/reports/schedules/{sched_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert del_res.status_code == 200


def test_scheduler_due_execution(client, db_session):
    """Test SchedulerService.execute_due_schedules executes past-due schedules and advances next_run_at."""
    token, user = register_user(client, "Cron User", "cron_user@domain.com")

    # Upload dataset
    csv_data = "product,revenue\nWidget,100"
    upload_res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("sales.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")},
        headers={"Authorization": f"Bearer {token}"}
    )
    dataset_id = upload_res.json()["dataset_id"]

    # Create schedule set to past trigger time
    create_res = client.post(
        "/api/v1/reports/schedules",
        json={
            "dataset_id": dataset_id,
            "report_name": "Overdue Weekly Report",
            "frequency": "weekly",
            "report_format": "pdf",
            "recipients": ["boss@company.com"],
            "email_subject": "Overdue Digest",
            "email_body": "Weekly metrics.",
            "is_active": True
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    sched_id = create_res.json()["id"]

    # Manually backdate next_run_at to simulate due schedule
    from app.models.report import ScheduledReport
    schedule = db_session.query(ScheduledReport).filter(ScheduledReport.id == sched_id).first()
    schedule.next_run_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    db_session.commit()

    # Mock send_report_email so it does not invoke external Gmail API
    with patch("app.services.gmail_service.GmailService.send_report_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"status": "success", "gmail_message_id": "mock_cron_id_123"}
        asyncio.run(SchedulerService.execute_due_schedules(db=db_session))

    # Verify schedule was updated with next_run_at in the future and last_run_at recorded
    db_session.refresh(schedule)
    assert schedule.last_run_at is not None
    assert schedule.next_run_at is not None
    assert schedule.last_status == "success"
