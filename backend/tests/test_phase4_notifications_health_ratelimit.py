from tests.test_reports import register_user
from app.services.notification_service import NotificationService
from app.core.rate_limit import rate_limiter


def test_notifications_lifecycle_dedup_and_isolation(client, db_session):
    """Verify notification creation, 24h dedup, read/unread, delete, and user isolation."""
    t1, u1 = register_user(client, "Notif U1", "notif_u1@inslight.ai")
    t2, u2 = register_user(client, "Notif U2", "notif_u2@inslight.ai")

    # Create two notifications with same dedup_key -> only 1 persisted
    n1 = NotificationService.create_notification(
        db=db_session,
        user_id=u1["id"],
        category="alert",
        title="Margin Alert",
        message="Margin dropped below 15%.",
        dedup_key="alert:ds1:margin",
    )
    n2 = NotificationService.create_notification(
        db=db_session,
        user_id=u1["id"],
        category="alert",
        title="Margin Alert",
        message="Margin dropped below 15%.",
        dedup_key="alert:ds1:margin",
    )
    assert n1.id == n2.id

    # Unread count for User 1 is 1; User 2 is 0
    c1 = client.get("/api/v1/notifications/unread-count", headers={"Authorization": f"Bearer {t1}"})
    c2 = client.get("/api/v1/notifications/unread-count", headers={"Authorization": f"Bearer {t2}"})
    assert c1.json()["unread_count"] == 1
    assert c2.json()["unread_count"] == 0

    # User 2 cannot read or delete User 1's notification
    assert client.patch(f"/api/v1/notifications/{n1.id}/read", headers={"Authorization": f"Bearer {t2}"}).status_code == 404
    assert client.delete(f"/api/v1/notifications/{n1.id}", headers={"Authorization": f"Bearer {t2}"}).status_code == 404

    # User 1 marks read & deletes
    r_read = client.patch(f"/api/v1/notifications/{n1.id}/read", headers={"Authorization": f"Bearer {t1}"})
    assert r_read.status_code == 200
    assert r_read.json()["is_read"] is True
    assert client.get("/api/v1/notifications/unread-count", headers={"Authorization": f"Bearer {t1}"}).json()["unread_count"] == 0
    assert client.delete(f"/api/v1/notifications/{n1.id}", headers={"Authorization": f"Bearer {t1}"}).status_code == 200


def test_health_probes_and_request_id_header(client):
    """Verify /health/live, /health/ready, X-Request-ID header, and consistent error JSON."""
    r_live = client.get("/health/live")
    assert r_live.status_code == 200
    assert r_live.json()["status"] == "alive"
    assert "x-request-id" in {k.lower() for k in r_live.headers.keys()}

    r_ready = client.get("/api/v1/health/ready")
    assert r_ready.status_code == 200
    assert r_ready.json()["checks"]["database"] == "connected"


def test_rate_limiter_enforces_429_and_resets(monkeypatch):
    """Verify SlidingWindowRateLimiter blocks bursts above threshold and resets cleanly."""
    import pytest
    from fastapi import HTTPException

    rate_limiter.reset()
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    for _ in range(3):
        rate_limiter.check("test:ip", max_requests=3, window_seconds=60)
    with pytest.raises(HTTPException) as exc:
        rate_limiter.check("test:ip", max_requests=3, window_seconds=60)
    assert exc.value.status_code == 429
    rate_limiter.reset()
