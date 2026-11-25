import pytest
from app.core.security import create_access_token
from datetime import timedelta


def test_user_registration_success(client):
    res = client.post("/api/v1/auth/register", json={
        "name": "Alice Analyst",
        "email": "alice@company.com",
        "password": "SecurePassword123!"
    })
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "alice@company.com"
    assert data["user"]["name"] == "Alice Analyst"
    assert "hashed_password" not in data["user"]


def test_user_registration_duplicate_fails(client):
    payload = {
        "name": "Alice Analyst",
        "email": "alice@company.com",
        "password": "SecurePassword123!"
    }
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_user_login_success(client):
    client.post("/api/v1/auth/register", json={
        "name": "Bob Trader",
        "email": "bob@company.com",
        "password": "SecretPassword123!"
    })

    res = client.post("/api/v1/auth/login", json={
        "email": "bob@company.com",
        "password": "SecretPassword123!"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "bob@company.com"


def test_user_login_invalid_password_fails(client):
    client.post("/api/v1/auth/register", json={
        "name": "Bob Trader",
        "email": "bob@company.com",
        "password": "SecretPassword123!"
    })

    res = client.post("/api/v1/auth/login", json={
        "email": "bob@company.com",
        "password": "WrongPassword!"
    })
    assert res.status_code == 401
    assert "Incorrect email or password" in res.json()["detail"]


def test_unauthenticated_access_to_all_protected_endpoints(client):
    """Verify that all core business endpoints strictly reject unauthenticated requests with 401."""
    protected_endpoints = [
        ("GET", "/api/v1/datasets"),
        ("GET", "/api/v1/datasets/active"),
        ("POST", "/api/v1/datasets/upload"),
        ("POST", "/api/v1/query"),
        ("GET", "/api/v1/profile"),
        ("POST", "/api/v1/deep-dive"),
        ("POST", "/api/v1/what-if"),
        ("GET", "/api/v1/anomalies"),
    ]
    for method, path in protected_endpoints:
        if method == "GET":
            res = client.get(path)
        else:
            res = client.post(path, json={})
        assert res.status_code == 401, f"Endpoint {method} {path} should require auth, got {res.status_code}"
        assert "Authentication token required" in res.json()["detail"]


def test_invalid_jwt_token_rejected(client):
    res = client.get("/api/v1/datasets", headers={"Authorization": "Bearer invalid.token.value"})
    assert res.status_code == 401
    assert "Invalid or expired" in res.json()["detail"]


def test_expired_jwt_token_rejected(client):
    expired_token = create_access_token(subject="fake-user-id", expires_delta=timedelta(seconds=-10))
    res = client.get("/api/v1/datasets", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401
    assert "Invalid or expired" in res.json()["detail"]
