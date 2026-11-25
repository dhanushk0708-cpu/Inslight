import io
import pytest
from tests.test_reports import register_user


def test_multi_dataset_sales_and_catalog_join_workflow(client):
    """
    Test complete Multi-Dataset Relational Intelligence workflow:
    1. Upload sales orders (order_id, product_id, quantity, revenue)
    2. Upload product catalog (product_id, product_name, category)
    3. Auto-detect candidate join keys (identifies product_id)
    4. Validate join integrity and assert Many-to-One (N:1) cardinality
    5. Execute DuckDB join preview and verify merged record structure
    6. Save relationship with N:1 type
    7. List relationships and verify dataset names are populated
    8. Delete relationship
    """
    token, user = register_user(client, "Rel Multi", "rel_multi@inslight.ai")
    auth_headers = {"Authorization": f"Bearer {token}"}

    # Upload Sales Orders (source, 4 rows, multiple orders referencing same products)
    csv_orders = (
        "order_id,product_id,quantity,revenue\n"
        "ORD001,P100,2,1000\n"
        "ORD002,P100,1,500\n"
        "ORD003,P200,3,1500\n"
        "ORD004,P300,1,300\n"
    )
    up_orders = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("inslight_sales_orders.csv", io.BytesIO(csv_orders.encode("utf-8")), "text/csv")},
        headers=auth_headers
    )
    assert up_orders.status_code == 200
    orders_id = up_orders.json()["dataset_id"]

    # Upload Product Catalog (target, 3 rows, unique product_ids)
    csv_catalog = (
        "product_id,product_name,category\n"
        "P100,AeroBook Pro,Laptops\n"
        "P200,ErgoChair 900,Furniture\n"
        "P300,NoiseCancel Headset,Audio\n"
    )
    up_catalog = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("inslight_product_catalog.csv", io.BytesIO(csv_catalog.encode("utf-8")), "text/csv")},
        headers=auth_headers
    )
    assert up_catalog.status_code == 200
    catalog_id = up_catalog.json()["dataset_id"]

    # 1. Fetch user datasets and verify columns list is populated
    ds_list_res = client.get("/api/v1/datasets", headers=auth_headers)
    assert ds_list_res.status_code == 200
    ds_list = ds_list_res.json()
    assert len(ds_list) >= 2
    orders_meta = next(d for d in ds_list if d["id"] == orders_id)
    assert "product_id" in orders_meta["columns"]
    assert "order_id" in orders_meta["columns"]

    # 2. Get specific dataset columns endpoint
    col_res = client.get(f"/api/v1/datasets/{catalog_id}/columns", headers=auth_headers)
    assert col_res.status_code == 200
    assert "product_id" in col_res.json()["columns"]
    assert "product_name" in col_res.json()["columns"]

    # 3. Detect candidate join keys
    cand_res = client.post(
        "/api/v1/relationships/candidates",
        json={"source_dataset_id": orders_id, "target_dataset_id": catalog_id},
        headers=auth_headers
    )
    assert cand_res.status_code == 200
    candidates = cand_res.json()
    assert len(candidates) > 0
    match = next(c for c in candidates if c["source_column"] == "product_id" and c["target_column"] == "product_id")
    assert match["match_type"] == "Exact Name Match"

    # 4. Validate join relationship (expecting Many-to-One / N:1)
    val_res = client.post(
        "/api/v1/relationships/validate",
        json={
            "source_dataset_id": orders_id,
            "target_dataset_id": catalog_id,
            "source_column": "product_id",
            "target_column": "product_id"
        },
        headers=auth_headers
    )
    assert val_res.status_code == 200
    val_data = val_res.json()
    assert val_data["is_valid"] is True
    assert val_data["cardinality"] == "many_to_one"
    assert val_data["risk_level"] == "LOW"
    assert val_data["source_stats"]["total_rows"] == 4
    assert val_data["source_stats"]["is_unique"] is False  # duplicates in orders
    assert val_data["target_stats"]["total_rows"] == 3
    assert val_data["target_stats"]["is_unique"] is True   # unique in catalog

    # 5. Preview joined records in DuckDB
    preview_res = client.post(
        "/api/v1/relationships/preview",
        json={
            "source_dataset_id": orders_id,
            "target_dataset_id": catalog_id,
            "source_column": "product_id",
            "target_column": "product_id",
            "limit": 10
        },
        headers=auth_headers
    )
    assert preview_res.status_code == 200
    preview_data = preview_res.json()
    assert preview_data["status"] == "success"
    assert len(preview_data["records"]) == 4
    assert "order_id" in preview_data["columns"]
    assert "product_name" in preview_data["columns"]

    # 6. Save relationship with shorthand or standard type
    create_res = client.post(
        "/api/v1/relationships",
        json={
            "source_dataset_id": orders_id,
            "target_dataset_id": catalog_id,
            "source_column": "product_id",
            "target_column": "product_id",
            "relationship_type": "N:1"
        },
        headers=auth_headers
    )
    assert create_res.status_code == 200
    rel_data = create_res.json()
    assert rel_data["relationship_type"] == "many_to_one"
    assert rel_data["source_dataset_name"] == "inslight_sales_orders.csv"
    assert rel_data["target_dataset_name"] == "inslight_product_catalog.csv"
    rel_id = rel_data["id"]

    # 7. List relationships
    list_res = client.get("/api/v1/relationships", headers=auth_headers)
    assert list_res.status_code == 200
    all_rels = list_res.json()
    assert any(r["id"] == rel_id for r in all_rels)

    # 8. Delete relationship
    del_res = client.delete(f"/api/v1/relationships/{rel_id}", headers=auth_headers)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"
