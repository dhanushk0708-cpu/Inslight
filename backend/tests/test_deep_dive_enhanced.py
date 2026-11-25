import io
from tests.test_reports import register_user


def test_deep_dive_comprehensive_on_sample_sales(client):
    """Verify 10-section Deep Dive analysis on sample_sales.csv (96 rows)."""
    token, _ = register_user(client, "DD User", "dd_sample@inslight.ai")

    with open("backend/data/sample_sales.csv", "rb") as f:
        up = client.post(
            "/api/v1/datasets/upload",
            files={"file": ("sample_sales.csv", f, "text/csv")},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert up.status_code == 200

    res = client.post("/api/v1/deep-dive?refresh=true", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()

    assert data["dataset_metadata"]["row_count"] == 96
    assert len(data["executive_summary"]["kpi_cards"]) >= 3
    assert data["profitability_analysis"]["available"] is True
    assert data["product_analysis"]["available"] is True
    assert data["regional_analysis"]["available"] is True
    # sample_sales.csv has no customer_id column -> must NOT invent customer metrics
    assert data["customer_analysis"]["available"] is False
    # Must have dynamic charts
    assert "revenue_trend" in data["charts"]
    assert "revenue_by_category" in data["charts"]
    assert "top_products" in data["charts"]
    assert "regional_performance" in data["charts"]
    assert len(data["opportunities"]) == 3
    assert len(data["anomalies_and_risks"]["risks"]) == 3
    assert len(data["execution_stages"]) >= 4


def test_deep_dive_adapts_dynamically_to_alternate_schema(client):
    """Verify Deep Dive adapts to an alternate schema with customer_id & no profit/product columns."""
    token, _ = register_user(client, "DD Alt", "dd_alt@inslight.ai")

    alt_csv = (
        "date,region,customer_id,order_id,revenue\n"
        "2024-01-01,North,CUST-1,ORD-1,10000\n"
        "2024-02-01,North,CUST-1,ORD-2,15000\n"
        "2024-03-01,South,CUST-2,ORD-3,8000\n"
        "2024-04-01,East,CUST-3,ORD-4,22000\n"
        "2024-05-01,West,CUST-4,ORD-5,12000\n"
    )
    up = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("customers.csv", io.BytesIO(alt_csv.encode("utf-8")), "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert up.status_code == 200

    res = client.post("/api/v1/deep-dive?refresh=true", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()

    assert data["dataset_metadata"]["row_count"] == 5
    # No profit or cost column -> profitability must be marked unavailable
    assert data["profitability_analysis"]["available"] is False
    # Customer ID exists -> customer intelligence must be available with 4 unique customers
    assert data["customer_analysis"]["available"] is True
    assert data["customer_analysis"]["unique_customers"] == 4
    assert "customer_concentration" in data["charts"]
    assert "profit_trend" not in data["charts"]
