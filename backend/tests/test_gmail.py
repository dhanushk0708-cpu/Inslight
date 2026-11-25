import io
import pytest
from unittest.mock import patch, AsyncMock
from app.services.gmail_service import GmailService
from app.core.security import create_access_token


def register_user(client, name="Gmail User", email="gmail_user@domain.com"):
    res = client.post("/api/v1/auth/register", json={
        "name": name,
        "email": email,
        "password": "Password123!"
    })
    assert res.status_code == 201
    return res.json()["access_token"], res.json()["user"]


def test_gmail_authorization_url_generation(client):
    """Verify that authorize endpoint returns Google OAuth URL with CSRF state token."""
    token, user = register_user(client, "OAuth User", "oauth_user@domain.com")

    res = client.get("/api/v1/integrations/gmail/authorize", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "authorization_url" in data
    auth_url = data["authorization_url"]
    assert "accounts.google.com" in auth_url
    assert "client_id=" in auth_url
    assert "state=" in auth_url
    assert "https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fgmail.send" in auth_url


def test_gmail_status_and_disconnect(client):
    """Verify Gmail connection status check and disconnect endpoint."""
    token, user = register_user(client, "Status User", "status_user@domain.com")

    # Initially disconnected
    res = client.get("/api/v1/integrations/gmail/status", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["is_connected"] is False

    # Disconnect when not connected should succeed cleanly
    dis_res = client.post("/api/v1/integrations/gmail/disconnect", headers={"Authorization": f"Bearer {token}"})
    assert dis_res.status_code == 200


def test_gmail_oauth_callback_handling(client, db_session):
    """Test OAuth callback handling with mocked Google token exchange."""
    token, user = register_user(client, "Callback User", "callback_user@domain.com")
    user_id = user["id"]

    # Generate valid state token
    state = create_access_token(subject=user_id)

    import httpx
    mock_token_res = httpx.Response(200, json={
        "access_token": "mock-access-token-12345",
        "refresh_token": "mock-refresh-token-67890",
        "expires_in": 3600
    })
    mock_userinfo_res = httpx.Response(200, json={"email": "connected_gmail@gmail.com"})

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
         patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_post.return_value = mock_token_res
        mock_get.return_value = mock_userinfo_res

        res = client.get(f"/api/v1/integrations/gmail/callback?code=mock_code&state={state}", follow_redirects=False)
        assert res.status_code == 307
        assert "gmail_connected=true" in res.headers["location"]

    # Verify user now shows as connected
    status_res = client.get("/api/v1/integrations/gmail/status", headers={"Authorization": f"Bearer {token}"})
    assert status_res.status_code == 200
    assert status_res.json()["is_connected"] is True
    assert status_res.json()["email"] == "connected_gmail@gmail.com"


def test_gmail_email_send_mock(client, db_session):
    """Verify that email send endpoint correctly composes message and invokes Gmail API."""
    token, user = register_user(client, "Sender User", "sender_user@domain.com")

    # 1. Connect user directly via OAuthRepository
    from app.repositories.oauth_repository import OAuthRepository
    from datetime import datetime, timedelta, timezone
    OAuthRepository.save_or_update(
        db=db_session,
        user_id=user["id"],
        access_token="mock-valid-access-token",
        refresh_token="mock-refresh-token",
        email="sender@gmail.com",
        token_expiry=datetime.now(timezone.utc) + timedelta(hours=1)
    )

    # 2. Upload dataset and generate report
    csv_data = "metric,value\nRevenue,5000"
    upload_res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("test.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")},
        headers={"Authorization": f"Bearer {token}"}
    )
    dataset_id = upload_res.json()["dataset_id"]

    gen_res = client.post(
        "/api/v1/reports/generate",
        json={"title": "Q1 Report", "report_format": "pdf", "dataset_id": dataset_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    report_id = gen_res.json()["id"]

    # 3. Send email with mocked Gmail API endpoint
    import httpx
    mock_send_res = httpx.Response(200, json={"id": "18c123456789abcdef", "threadId": "18c123456789abcdef"})

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_send_res
        mail_res = client.post(
            "/api/v1/reports/email",
            json={
                "report_id": report_id,
                "recipients": ["cfo@company.com"],
                "subject": "Monthly Business Report",
                "body": "Please find attached the latest report."
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        if mail_res.status_code != 200:
            print("FAILED DETAIL:", mail_res.json())
        assert mail_res.status_code == 200
        data = mail_res.json()
        assert data["status"] == "success"
        assert data["gmail_message_id"] == "18c123456789abcdef"

    # 4. Verify report record now reflects 'sent' status
    rep_res = client.get(f"/api/v1/reports/{report_id}", headers={"Authorization": f"Bearer {token}"})
    assert rep_res.status_code == 200
    assert rep_res.json()["status"] == "sent"
    assert rep_res.json()["gmail_message_id"] == "18c123456789abcdef"
