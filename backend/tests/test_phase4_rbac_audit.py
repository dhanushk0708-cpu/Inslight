import io
from tests.test_reports import register_user
from app.models.user import User


def test_rbac_blocks_analyst_and_allows_admin(client, db_session):
    """Verify analyst cannot access /admin/* routes while promoted admin can."""
    t_analyst, u_analyst = register_user(client, "Analyst One", "analyst_rbac@inslight.ai")
    t_admin, u_admin = register_user(client, "Admin One", "admin_rbac@inslight.ai")

    # Promote u_admin directly in DB (simulating secure CLI script)
    db_user = db_session.query(User).filter(User.id == u_admin["id"]).first()
    db_user.role = "admin"
    db_session.commit()

    # Analyst blocked with 403
    res_forbidden = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {t_analyst}"})
    assert res_forbidden.status_code == 403

    res_logs_forbidden = client.get("/api/v1/admin/audit-logs", headers={"Authorization": f"Bearer {t_analyst}"})
    assert res_logs_forbidden.status_code == 403

    # Admin allowed
    res_users = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {t_admin}"})
    assert res_users.status_code == 200
    assert len(res_users.json()) >= 2

    # Admin cannot demote self
    res_self = client.patch(
        f"/api/v1/admin/users/{u_admin['id']}/role",
        json={"role": "analyst"},
        headers={"Authorization": f"Bearer {t_admin}"},
    )
    assert res_self.status_code == 400

    # Admin can promote analyst -> admin and back
    res_promote = client.patch(
        f"/api/v1/admin/users/{u_analyst['id']}/role",
        json={"role": "admin"},
        headers={"Authorization": f"Bearer {t_admin}"},
    )
    assert res_promote.status_code == 200
    assert res_promote.json()["role"] == "admin"


def test_audit_logs_recorded_without_secrets(client, db_session):
    """Verify important actions emit audit logs and sensitive fields are never exposed."""
    t_admin, u_admin = register_user(client, "Audit Admin", "audit_admin@inslight.ai")
    db_user = db_session.query(User).filter(User.id == u_admin["id"]).first()
    db_user.role = "admin"
    db_session.commit()

    # Upload dataset to generate audit record
    csv_data = "date,region,revenue\n2024-01-01,East,1000\n"
    client.post(
        "/api/v1/datasets/upload",
        files={"file": ("audit.csv", io.BytesIO(csv_data.encode()), "text/csv")},
        headers={"Authorization": f"Bearer {t_admin}"},
    )

    res = client.get("/api/v1/admin/audit-logs?limit=50", headers={"Authorization": f"Bearer {t_admin}"})
    assert res.status_code == 200
    body = res.json()
    actions = [item["action"] for item in body["items"]]
    assert "register" in actions
    assert "dataset_upload" in actions
    for item in body["items"]:
        meta = item.get("metadata_json") or ""
        assert "password" not in meta.lower() or "[redacted]" in meta.lower()
