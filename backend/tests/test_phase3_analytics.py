import io
import pytest
from tests.test_reports import register_user


def test_root_cause_analysis_period_and_decomposition(client):
    """Test Root Cause Analysis with price vs volume decomposition and dimensional contributions."""
    token, user = register_user(client, "RCA User", "rca_user@domain.com")

    csv_data = (
        "order_date,product,region,revenue,quantity,unit_price\n"
        "2024-01-01,Laptop,North,10000,10,1000\n"
        "2024-01-05,Phone,South,6000,12,500\n"
        "2024-02-01,Laptop,North,5000,5,1000\n"
        "2024-02-05,Phone,South,4000,8,500\n"
    )
    client.post(
        "/api/v1/datasets/upload",
        files={"file": ("rca_sales.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")},
        headers={"Authorization": f"Bearer {token}"}
    )

    res = client.post(
        "/api/v1/analytics/rca",
        json={},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["direction"] == "decline"
    assert data["absolute_change"] == -7000.0
    assert len(data["top_contributors"]) > 0
    assert data["price_volume_decomposition"] is not None
    assert "primary_driver" in data["price_volume_decomposition"]


def test_forecasting_service_sufficient_and_insufficient_data(client):
    """Test forecasting handling of sufficient data vs under 5 historical periods."""
    token, user = register_user(client, "FC User", "fc_user@domain.com")

    # 1. Insufficient data (<5 points)
    csv_small = "date,revenue\n2024-01-01,100\n2024-01-02,200\n2024-01-03,300"
    up_small = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("small.csv", io.BytesIO(csv_small.encode("utf-8")), "text/csv")},
        headers={"Authorization": f"Bearer {token}"}
    )
    res_small = client.post(
        "/api/v1/analytics/forecast",
        json={"horizon": 7},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_small.status_code == 200
    assert res_small.json()["status"] == "insufficient_data"

    # 2. Sufficient data (>= 6 periods)
    rows = ["date,revenue"]
    for i in range(1, 10):
        rows.append(f"2024-0{i}-01,{1000 + i * 500}")
    csv_large = "\n".join(rows)
    client.post(
        "/api/v1/datasets/upload",
        files={"file": ("large.csv", io.BytesIO(csv_large.encode("utf-8")), "text/csv")},
        headers={"Authorization": f"Bearer {token}"}
    )
    res_large = client.post(
        "/api/v1/analytics/forecast",
        json={"horizon": 30, "method": "auto"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_large.status_code == 200
    fc_data = res_large.json()
    assert fc_data["status"] == "success"
    assert len(fc_data["forecast_data"]) > 0
    assert "mae" in fc_data["evaluation_metrics"]


def test_advanced_anomaly_detection_multi_methods(client):
    """Test anomaly detection detecting both statistical spikes and risks."""
    token, user = register_user(client, "Anom User", "anom_user@domain.com")

    rows = ["product,revenue,quantity"]
    for i in range(30):
        rows.append(f"Item_{i},100,5")
    # Add high spike
    rows.append("Outlier_Product,50000,500")

    csv_data = "\n".join(rows)
    client.post(
        "/api/v1/datasets/upload",
        files={"file": ("anom.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")},
        headers={"Authorization": f"Bearer {token}"}
    )

    res = client.post(
        "/api/v1/analytics/advanced-anomalies",
        json={"methods": ["zscore", "iqr"]},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["anomalies_detected_count"] >= 1
    outlier = next((a for a in data["anomalies"] if a["observed_value"] >= 50000), None)
    assert outlier is not None
    assert outlier["type"] == "opportunity"


def test_data_quality_audit_and_preview(client):
    """Test dataset hygiene auditing and non-destructive cleaned preview."""
    token, user = register_user(client, "Quality User", "quality_user@domain.com")

    # CSV with duplicate row, null category, and mixed casing
    csv_data = (
        "category,revenue\n"
        "Electronics,100\n"
        "electronics,200\n"
        "Electronics,100\n"  # duplicate
        ",300\n"              # null category
    )
    up = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("dirty.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")},
        headers={"Authorization": f"Bearer {token}"}
    )
    dataset_id = up.json()["dataset_id"]

    # 1. Audit
    res_audit = client.post(
        f"/api/v1/datasets/{dataset_id}/quality",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_audit.status_code == 200
    audit_data = res_audit.json()
    assert audit_data["overall_score"] < 100
    assert audit_data["issues_count"] >= 2

    # 2. Preview
    res_prev = client.get(
        f"/api/v1/datasets/{dataset_id}/quality/preview?limit=5",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_prev.status_code == 200
    prev_data = res_prev.json()
    assert len(prev_data["preview_records"]) > 0


def test_comparative_analytics_mom_and_segment(client):
    """Test period-over-period and dimension benchmark comparisons."""
    token, user = register_user(client, "Comp User", "comp_user@domain.com")

    csv_data = (
        "date,region,revenue\n"
        "2024-01-01,North,1000\n"
        "2024-01-02,South,2000\n"
        "2024-02-01,North,1500\n"
        "2024-02-02,South,2500\n"
    )
    client.post(
        "/api/v1/datasets/upload",
        files={"file": ("comp.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")},
        headers={"Authorization": f"Bearer {token}"}
    )

    # Period comparison
    res_p = client.post(
        "/api/v1/analytics/compare",
        json={"comparison_mode": "period"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_p.status_code == 200
    data_p = res_p.json()
    assert data_p["status"] == "success"
    assert data_p["latest_comparison"]["percentage_change"] == 33.3

    # Segment comparison
    res_s = client.post(
        "/api/v1/analytics/compare",
        json={"comparison_mode": "segment", "dimension_col": "region"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_s.status_code == 200
    data_s = res_s.json()
    assert data_s["status"] == "success"
    assert data_s["higher_segment"] == "South"
