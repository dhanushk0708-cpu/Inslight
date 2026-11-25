import io
import pytest


def register_user(client, name, email, password):
    res = client.post("/api/v1/auth/register", json={
        "name": name,
        "email": email,
        "password": password
    })
    assert res.status_code == 201
    return res.json()["access_token"], res.json()["user"]


def test_dataset_isolation_between_users(client):
    # 1. Register User A and User B
    token_a, user_a = register_user(client, "User A", "user_a@domain.com", "PasswordA123!")
    token_b, user_b = register_user(client, "User B", "user_b@domain.com", "PasswordB123!")

    # 2. User A uploads sales dataset
    csv_a = "date,revenue,category\n2024-01-01,1000,Electronics\n2024-01-02,2000,Furniture"
    res_a = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("dataset_a.csv", io.BytesIO(csv_a.encode("utf-8")), "text/csv")},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert res_a.status_code == 200
    dataset_a_id = res_a.json()["dataset_id"]

    # 3. User B uploads customer dataset
    csv_b = "customer_name,country,spend\nAlice,USA,500\nBob,Canada,750"
    res_b = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("dataset_b.csv", io.BytesIO(csv_b.encode("utf-8")), "text/csv")},
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert res_b.status_code == 200
    dataset_b_id = res_b.json()["dataset_id"]

    # 4. Verify User A only sees dataset A
    list_a = client.get("/api/v1/datasets", headers={"Authorization": f"Bearer {token_a}"}).json()
    assert len(list_a) == 1
    assert list_a[0]["id"] == dataset_a_id
    assert list_a[0]["original_filename"] == "dataset_a.csv"

    # 5. Verify User B only sees dataset B
    list_b = client.get("/api/v1/datasets", headers={"Authorization": f"Bearer {token_b}"}).json()
    assert len(list_b) == 1
    assert list_b[0]["id"] == dataset_b_id
    assert list_b[0]["original_filename"] == "dataset_b.csv"

    # 6. User B attempts to DELETE User A's dataset (MUST BE REJECTED)
    del_res = client.delete(f"/api/v1/datasets/{dataset_a_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert del_res.status_code in [404, 403]

    # 7. User B attempts to run What-If simulation with User A's dataset_id (MUST BE REJECTED)
    what_if_res = client.post(
        "/api/v1/what-if",
        json={"dataset_id": dataset_a_id, "price_change": 10},
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert what_if_res.status_code in [404, 403]

    # 8. User B attempts to query User A's dataset_id (MUST BE REJECTED)
    query_res = client.post(
        "/api/v1/query",
        json={"question": "What is total revenue?", "dataset_id": dataset_a_id},
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert query_res.status_code == 200
    assert "not found or access denied" in query_res.json()["error"]

    # 9. Verify physical DuckDB storage isolation
    from app.services.dataset_service import DatasetService
    path_a = DatasetService.get_duckdb_path(user_a["id"], dataset_a_id)
    path_b = DatasetService.get_duckdb_path(user_b["id"], dataset_b_id)
    assert user_a["id"] in str(path_a)
    assert user_b["id"] in str(path_b)
    assert path_a != path_b

    # Verify User A's dataset still exists
    list_a_after = client.get("/api/v1/datasets", headers={"Authorization": f"Bearer {token_a}"}).json()
    assert len(list_a_after) == 1
    assert list_a_after[0]["id"] == dataset_a_id
