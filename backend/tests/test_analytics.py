import io
import pytest


def register_user(client, name="Analyst", email="analyst@domain.com"):
    res = client.post("/api/v1/auth/register", json={
        "name": name,
        "email": email,
        "password": "Password123!"
    })
    assert res.status_code == 201
    return res.json()["access_token"]


def test_what_if_analysis(client):
    token = register_user(client, "WhatIf User", "whatif@domain.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Upload test CSV
    csv_data = "date,revenue,cost,units_sold\n2024-01-01,10000,5000,100\n2024-02-01,15000,7500,150"
    upload_res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("test.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")},
        headers=headers
    )
    assert upload_res.status_code == 200

    # Run what-if
    wi_res = client.post(
        "/api/v1/what-if",
        json={
            "price_change": 10.0,
            "discount_change": 0.0,
            "units_change": 5.0
        },
        headers=headers
    )
    assert wi_res.status_code == 200
    data = wi_res.json()
    assert "current" in data
    assert "projected" in data
    assert "change" in data
    assert data["current"]["revenue"] == 25000
    assert data["projected"]["revenue"] > 25000


def test_anomalies_detection(client):
    token = register_user(client, "Anomaly User", "anomaly@domain.com")
    headers = {"Authorization": f"Bearer {token}"}

    csv_data = "date,revenue\n" + "\n".join([f"2024-{i+1:02d}-01,1000" for i in range(11)]) + "\n2024-12-01,999999\n"
    upload_res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("anomaly_test.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")},
        headers=headers
    )
    assert upload_res.status_code == 200

    anom_res = client.get("/api/v1/anomalies", headers=headers)
    assert anom_res.status_code == 200
    data = anom_res.json()
    assert "anomalies" in data
    assert data["count"] >= 1
