import io
import pytest
from tests.test_reports import register_user


def test_alert_rules_evaluation_and_deduplication(client):
    """Verify alert rule evaluation, trigger generation, and 24-hr deduplication."""
    token, user = register_user(client, "Alert Tester", "alert_tester@domain.com")

    # CSV with revenue drop in Feb
    csv_data = (
        "date,revenue\n"
        "2024-01-01,10000\n"
        "2024-02-01,5000\n"  # 50% drop
    )
    client.post(
        "/api/v1/datasets/upload",
        files={"file": ("alert_sales.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")},
        headers={"Authorization": f"Bearer {token}"}
    )

    # 1. Trigger scan
    scan_res = client.post("/api/v1/alerts/scan", headers={"Authorization": f"Bearer {token}"})
    assert scan_res.status_code == 200
    alerts = scan_res.json()
    assert len(alerts) >= 1
    alert_id = alerts[0]["id"]
    assert alerts[0]["is_read"] is False

    # 2. Immediate second scan should NOT create duplicates
    scan2_res = client.post("/api/v1/alerts/scan", headers={"Authorization": f"Bearer {token}"})
    assert scan2_res.status_code == 200
    assert len(scan2_res.json()) == 0  # 0 new alerts because deduplicated!

    # 3. Mark alert as read
    read_res = client.patch(f"/api/v1/alerts/{alert_id}/read", headers={"Authorization": f"Bearer {token}"})
    assert read_res.status_code == 200
    assert read_res.json()["is_read"] is True

    # 4. Resolve alert
    resolve_res = client.patch(f"/api/v1/alerts/{alert_id}/resolve", headers={"Authorization": f"Bearer {token}"})
    assert resolve_res.status_code == 200
    assert resolve_res.json()["is_resolved"] is True


def test_dashboard_generation_and_crud(client):
    """Verify AI dashboard synthesis and saved dashboard persistence."""
    token, user = register_user(client, "Dash User", "dash_user@domain.com")

    csv_data = "date,product,revenue\n2024-01-01,Laptop,1000\n2024-01-02,Phone,500"
    client.post(
        "/api/v1/datasets/upload",
        files={"file": ("dash_data.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")},
        headers={"Authorization": f"Bearer {token}"}
    )

    # 1. Generate dashboard from prompt
    gen_res = client.post(
        "/api/v1/dashboards/generate",
        json={"prompt": "Executive sales summary dashboard"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert gen_res.status_code == 200
    dash_config = gen_res.json()
    assert len(dash_config["widgets"]) >= 2

    # 2. Save dashboard
    save_res = client.post(
        "/api/v1/dashboards",
        json={"title": "Q1 Executive Sales", "description": "Boardroom KPI overview", "layout_config": dash_config},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert save_res.status_code == 200
    saved_id = save_res.json()["id"]

    # 3. List dashboards
    list_res = client.get("/api/v1/dashboards", headers={"Authorization": f"Bearer {token}"})
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1

    # 4. Duplicate dashboard
    dup_res = client.post(f"/api/v1/dashboards/{saved_id}/duplicate", headers={"Authorization": f"Bearer {token}"})
    assert dup_res.status_code == 200
    assert "Copy" in dup_res.json()["title"]

    # 5. Delete dashboard
    del_res = client.delete(f"/api/v1/dashboards/{saved_id}", headers={"Authorization": f"Bearer {token}"})
    assert del_res.status_code == 200


def test_dataset_relationship_candidates_and_validation(client):
    """Verify multi-dataset foreign key candidate detection and cardinality validation."""
    token, user = register_user(client, "Rel User", "rel_user@domain.com")

    # Upload Dataset 1: Orders
    csv_orders = "order_id,product_id,amount\n101,P1,500\n102,P2,300\n103,P1,500"
    up1 = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("orders.csv", io.BytesIO(csv_orders.encode("utf-8")), "text/csv")},
        headers={"Authorization": f"Bearer {token}"}
    )
    ds1_id = up1.json()["dataset_id"]

    # Upload Dataset 2: Products
    csv_prods = "product_id,product_name,category\nP1,Laptop,Electronics\nP2,Chair,Furniture"
    up2 = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("products.csv", io.BytesIO(csv_prods.encode("utf-8")), "text/csv")},
        headers={"Authorization": f"Bearer {token}"}
    )
    ds2_id = up2.json()["dataset_id"]

    # 1. Candidate detection
    cand_res = client.post(
        "/api/v1/relationships/candidates",
        json={"source_dataset_id": ds1_id, "target_dataset_id": ds2_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert cand_res.status_code == 200
    cands = cand_res.json()
    assert any(c["source_column"] == "product_id" for c in cands)

    # 2. Validation & Cardinality Assessment
    val_res = client.post(
        "/api/v1/relationships/validate",
        json={
            "source_dataset_id": ds1_id,
            "target_dataset_id": ds2_id,
            "source_column": "product_id",
            "target_column": "product_id"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert val_res.status_code == 200
    val_data = val_res.json()
    assert val_data["is_valid"] is True
    assert val_data["cardinality"] == "many_to_one"  # multiple orders per single product

    # 3. Create relationship
    create_res = client.post(
        "/api/v1/relationships",
        json={
            "source_dataset_id": ds1_id,
            "target_dataset_id": ds2_id,
            "source_column": "product_id",
            "target_column": "product_id",
            "relationship_type": "many_to_one"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_res.status_code == 200
    rel_id = create_res.json()["id"]

    # 4. List and delete
    list_res = client.get("/api/v1/relationships", headers={"Authorization": f"Bearer {token}"})
    assert len(list_res.json()) == 1

    del_res = client.delete(f"/api/v1/relationships/{rel_id}", headers={"Authorization": f"Bearer {token}"})
    assert del_res.status_code == 200
