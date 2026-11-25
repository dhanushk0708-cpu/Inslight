from tests.test_reports import register_user


def test_presentation_outline_generation_download_and_isolation(client):
    """Verify AI PowerPoint outline, .pptx binary generation, download, and user isolation."""
    t1, _ = register_user(client, "PPTX U1", "pptx_u1@inslight.ai")
    t2, _ = register_user(client, "PPTX U2", "pptx_u2@inslight.ai")

    with open("backend/data/sample_sales.csv", "rb") as f:
        up = client.post(
            "/api/v1/datasets/upload",
            files={"file": ("sample_sales.csv", f, "text/csv")},
            headers={"Authorization": f"Bearer {t1}"},
        )
    assert up.status_code == 200

    # 1. Non-business prompt rejected by Business Context Guard
    bad = client.post(
        "/api/v1/presentations/outline",
        json={"prompt": "Tell me a joke about cats", "presentation_type": "Executive Business Review"},
        headers={"Authorization": f"Bearer {t1}"},
    )
    assert bad.status_code == 400

    # 2. Valid business outline
    out = client.post(
        "/api/v1/presentations/outline",
        json={"prompt": "Analyze revenue performance, opportunities, and risks", "presentation_type": "Executive Business Review"},
        headers={"Authorization": f"Bearer {t1}"},
    )
    assert out.status_code == 200
    outline = out.json()
    assert len(outline["slides"]) >= 5

    # 3. Build .pptx from edited outline
    outline["slides"][0]["title"] = "Edited Executive Deck"
    gen = client.post(
        "/api/v1/presentations/generate",
        json={
            "dataset_id": outline["dataset_id"],
            "title": "Edited Executive Deck",
            "presentation_type": outline["presentation_type"],
            "slides": outline["slides"],
        },
        headers={"Authorization": f"Bearer {t1}"},
    )
    assert gen.status_code == 200
    pres_id = gen.json()["id"]

    # 4. Download .pptx binary (ZIP/PK header) and verify User 2 isolation
    dl = client.get(f"/api/v1/presentations/{pres_id}/download", headers={"Authorization": f"Bearer {t1}"})
    assert dl.status_code == 200
    assert dl.content[:2] == b"PK"
    assert len(dl.content) > 5000

    dl_u2 = client.get(f"/api/v1/presentations/{pres_id}/download", headers={"Authorization": f"Bearer {t2}"})
    assert dl_u2.status_code == 404
