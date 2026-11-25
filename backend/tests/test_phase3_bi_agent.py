import pytest
from unittest.mock import patch, AsyncMock
from tests.test_reports import register_user


def test_bi_agent_tool_selection_rca(client, db_session):
    """Verify BI Agent identifies root cause analysis question and returns structured reasoning."""
    token, user = register_user(client, "Agent User", "agent_user@domain.com")

    # Upload test CSV
    csv_data = (
        "date,product,region,revenue,quantity\n"
        "2024-01-01,Laptop,North,10000,10\n"
        "2024-01-02,Phone,South,5000,10\n"
        "2024-02-01,Laptop,North,6000,6\n"
        "2024-02-02,Phone,South,4000,8\n"
    )
    import io
    client.post(
        "/api/v1/datasets/upload",
        files={"file": ("sales.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")},
        headers={"Authorization": f"Bearer {token}"}
    )

    with patch("app.services.ai_service.AIService.generate_text", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = "Revenue declined by 33.3% primarily driven by volume contraction in Laptops."

        res = client.post(
            "/api/v1/agent/query",
            json={"question": "Why did our revenue decline in February?"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["tool_used"] == "root_cause_analysis"
        assert len(data["reasoning_steps"]) >= 3
        assert "evidence" in data


def test_bi_agent_tool_selection_forecast(client, db_session):
    """Verify BI Agent selects forecasting tool for forward-looking projection questions."""
    token, user = register_user(client, "Forecaster User", "forecaster_user@domain.com")

    # Upload 6 months of data
    rows = ["date,revenue"]
    for i in range(1, 7):
        rows.append(f"2024-0{i}-01,{i * 10000}")
    csv_data = "\n".join(rows)

    import io
    client.post(
        "/api/v1/datasets/upload",
        files={"file": ("monthly.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")},
        headers={"Authorization": f"Bearer {token}"}
    )

    with patch("app.services.ai_service.AIService.generate_text", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = "Projected revenue demonstrates strong linear upward growth across the next 30 days."

        res = client.post(
            "/api/v1/agent/query",
            json={"question": "Can you forecast our revenue for the next month?"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["tool_used"] == "forecasting"
        assert "forecast_data" in data["data"]


def test_bi_agent_rejects_unrelated_questions(client):
    """Verify Business Context Guard rejects non-business questions in the agent."""
    token, user = register_user(client, "Guard User", "guard_user@domain.com")

    csv_data = "metric,value\nRevenue,100"
    import io
    client.post(
        "/api/v1/datasets/upload",
        files={"file": ("small.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")},
        headers={"Authorization": f"Bearer {token}"}
    )

    res = client.post(
        "/api/v1/agent/query",
        json={"question": "What is the capital of France?"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "rejected"
    assert data["tool_used"] == "business_guard"


def test_bi_agent_tool_selection_sql_fallback(client, db_session):
    """Verify BI Agent falls back to standard SQL analytics tool for ad-hoc aggregation queries."""
    token, user = register_user(client, "SQL User", "sql_user@domain.com")

    csv_data = (
        "product,revenue\n"
        "Laptop,10000\n"
        "Phone,5000\n"
    )
    import io
    client.post(
        "/api/v1/datasets/upload",
        files={"file": ("items.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")},
        headers={"Authorization": f"Bearer {token}"}
    )

    with patch("app.services.query_service.QueryService.process_user_query", new_callable=AsyncMock) as mock_query:
        mock_query.return_value = {
            "narrative": "Total revenue across products is ₹15,000.",
            "kpi_cards": [{"label": "Total Revenue", "value": "₹15,000"}],
            "main_chart": {"type": "bar"},
            "suggested_followups": ["What is revenue by product?"]
        }

        res = client.post(
            "/api/v1/agent/query",
            json={"question": "What is the total sales amount across all products?"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["tool_used"] == "sql_query"
        assert "₹15,000" in data["answer"]
        assert len(data["reasoning_steps"]) >= 3


def test_bi_agent_strategic_performance_opportunities_and_risks(client, db_session):
    """Verify BI Agent identifies broad performance inquiries and generates 3 opportunities, 3 risks, KPIs, and charts."""
    token, user = register_user(client, "Strategic User", "strategic_user@domain.com")

    with open("backend/data/sample_sales.csv", "rb") as f:
        client.post(
            "/api/v1/datasets/upload",
            files={"file": ("sample_sales.csv", f, "text/csv")},
            headers={"Authorization": f"Bearer {token}"}
        )

    res = client.post(
        "/api/v1/agent/query",
        json={"question": "Analyze my business performance and identify the three biggest opportunities and risks."},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["tool_used"] == "strategic_analysis"
    assert len(data["kpi_results"]) >= 3
    assert len(data["opportunities"]) == 3
    assert len(data["risks"]) == 3
    assert data["charts"]["main_chart"] is not None
    assert data["charts"]["secondary_chart"] is not None
    assert data["supporting_table"] is not None
    assert len(data["supporting_table"]["rows"]) > 0
    assert len(data["analytical_steps"]) >= 5


def test_bi_agent_business_overview_and_underperforming_regions(client, db_session):
    """Verify BI Agent handles overview and underperforming regions inquiries."""
    token, user = register_user(client, "Executive User", "exec_user@domain.com")

    with open("backend/data/sample_sales.csv", "rb") as f:
        client.post(
            "/api/v1/datasets/upload",
            files={"file": ("sample_sales.csv", f, "text/csv")},
            headers={"Authorization": f"Bearer {token}"}
        )

    # 1. Complete business overview
    res1 = client.post(
        "/api/v1/agent/query",
        json={"question": "Give me a complete business overview."},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res1.status_code == 200
    d1 = res1.json()
    assert d1["status"] == "success"
    assert d1["tool_used"] == "strategic_analysis"
    assert len(d1["opportunities"]) == 3

    # 2. Identify underperforming regions
    res2 = client.post(
        "/api/v1/agent/query",
        json={"question": "Identify underperforming regions."},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res2.status_code == 200
    d2 = res2.json()
    assert d2["status"] == "success"
    assert d2["tool_used"] == "strategic_analysis"
    assert d2["charts"]["secondary_chart"] is not None


def test_bi_agent_validation_rules_and_evidence_integrity(client, db_session):
    """Verify cross-sell, inventory, margin, opportunity calculation, and 5-field evidence rules."""
    token, user = register_user(client, "Validation User", "validation_user@domain.com")

    with open("backend/data/sample_sales.csv", "rb") as f:
        client.post(
            "/api/v1/datasets/upload",
            files={"file": ("sample_sales.csv", f, "text/csv")},
            headers={"Authorization": f"Bearer {token}"}
        )

    res = client.post(
        "/api/v1/agent/query",
        json={"question": "Analyze my business performance and identify the three biggest opportunities and risks."},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()
    opps = data["opportunities"]
    risks = data["risks"]

    # 1. Cross-sell on sample_sales.csv (no order_id) must be labeled hypothesis
    cross_sell = next(o for o in opps if o["rank"] == 2)
    assert cross_sell["is_hypothesis"] is True
    assert "hypothesis" in cross_sell["title"].lower()

    # 2. Regional opportunity must show calculation and hypothetical label
    reg_opp = next(o for o in opps if o["rank"] == 3)
    assert "hypothetical" in reg_opp["title"].lower()
    assert "40%" in reg_opp["impact"] or "0.40" in reg_opp["actual_value"]

    # 3. Inventory risk on sample_sales.csv (no inventory columns) must be low sales velocity, not inventory drag
    vel_risk = next(r for r in risks if r["rank"] == 3)
    assert "inventory drag" not in vel_risk["title"].lower()
    assert "velocity" in vel_risk["title"].lower()

    # 4. Margin risk without historical decline must not say "margin compression"
    margin_risk = next(r for r in risks if r["rank"] == 2)
    assert "margin compression" not in margin_risk["title"].lower()
    assert "below-average" in margin_risk["title"].lower()

    # 5. Every opportunity and risk has all 5 required evidence fields
    for o in opps:
        assert o["supporting_metric"]
        assert o["actual_value"]
        assert o["evidence_source"]
        assert o["business_interpretation"]
        assert o["recommendation"]
    for r in risks:
        assert r["supporting_metric"]
        assert r["actual_value"]
        assert r["evidence_source"]
        assert r["business_interpretation"]
        assert r["mitigation"]


def test_bi_agent_basket_cooccurrence_with_order_id(client, db_session):
    """Verify cross-sell is marked data-backed when order_id basket co-occurrence exists."""
    token, user = register_user(client, "Basket User", "basket_user@domain.com")

    csv_data = (
        "order_id,product_name,product_category,region,revenue,profit,units_sold\n"
        "ORD-1,Laptop Pro,Electronics,East,50000,15000,1\n"
        "ORD-1,Wireless Earbuds,Electronics,East,5000,3000,1\n"
        "ORD-2,Laptop Pro,Electronics,West,50000,15000,1\n"
        "ORD-2,Wireless Earbuds,Electronics,West,5000,3000,1\n"
        "ORD-3,Smartphone X,Electronics,North,30000,10000,1\n"
        "ORD-4,Bookshelf,Furniture,South,4000,2000,1\n"
    )
    import io
    client.post(
        "/api/v1/datasets/upload",
        files={"file": ("basket.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")},
        headers={"Authorization": f"Bearer {token}"}
    )

    res = client.post(
        "/api/v1/agent/query",
        json={"question": "Analyze my business performance and identify the three biggest opportunities and risks."},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()
    cross_sell = next(o for o in data["opportunities"] if o["rank"] == 2)
    assert cross_sell["is_hypothesis"] is False
    assert "data-backed" in cross_sell["title"].lower()
    assert "2 shared orders" in cross_sell["actual_value"].lower()
