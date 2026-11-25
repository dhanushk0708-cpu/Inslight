import io
import pytest
from app.services.pdf_generator import PDFReportGenerator
from app.services.excel_generator import ExcelReportGenerator, sanitize_formula_injection
from app.services.csv_generator import CSVReportGenerator
import openpyxl


def register_user(client, name="Report User", email="report_user@domain.com"):
    res = client.post("/api/v1/auth/register", json={
        "name": name,
        "email": email,
        "password": "Password123!"
    })
    assert res.status_code == 201
    return res.json()["access_token"], res.json()["user"]


def test_formula_injection_sanitization():
    """Verify that dangerous spreadsheet formulas are neutralized with a single quote."""
    dangerous = [
        "=SUM(A1:A10)",
        "+1+1",
        "-5+cmd|' /C calc'!A0",
        "@SUM(1,2)",
        "\tmalicious",
        "\rmalicious"
    ]
    for d in dangerous:
        sanitized = sanitize_formula_injection(d)
        assert sanitized.startswith("'"), f"Failed to sanitize: {d}"

    safe = ["Sales Data", "Electronics", 12345, 99.99, None]
    for s in safe:
        assert sanitize_formula_injection(s) == s


def test_pdf_report_generation():
    """Verify that PDF generator creates valid PDF document bytes."""
    kpis = [{"label": "Total Revenue", "value": 50000, "formatted_value": "$50,000.00"}]
    data = [{"region": "North", "sales": 20000}, {"region": "South", "sales": 30000}]
    pdf_bytes = PDFReportGenerator.generate(
        title="Q3 Performance",
        dataset_name="sales.csv",
        kpi_cards=kpis,
        narrative="Revenue increased by 15% across all regions.",
        table_data=data
    )
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-")


def test_excel_report_generation():
    """Verify that Excel generator produces workbook with expected sheets and formulas sanitized."""
    kpis = [{"label": "Total Revenue", "value": 50000, "formatted_value": "$50,000.00"}]
    data = [{"region": "=SUM(A1:A2)", "sales": 20000}]
    excel_bytes = ExcelReportGenerator.generate(
        title="Executive Digest",
        dataset_name="sales.csv",
        kpi_cards=kpis,
        narrative="Test narrative",
        table_data=data
    )
    assert isinstance(excel_bytes, bytes)
    wb = openpyxl.load_workbook(io.BytesIO(excel_bytes))
    sheet_names = wb.sheetnames
    assert "Overview" in sheet_names
    assert "KPI Summary" in sheet_names
    assert "Query Results" in sheet_names
    assert "Business Insights" in sheet_names

    # Verify formula was sanitized in Query Results
    ws_results = wb["Query Results"]
    cell_val = ws_results.cell(row=2, column=1).value
    assert str(cell_val).startswith("'=")


def test_csv_report_generation():
    """Verify CSV generator outputs sanitized CSV bytes."""
    data = [{"product": "@calc", "price": 100}]
    csv_bytes = CSVReportGenerator.generate(data)
    csv_str = csv_bytes.decode("utf-8")
    assert "'@calc" in csv_str


def test_report_endpoints_and_isolation(client):
    """Verify report generation, listing, downloading, and isolation between users."""
    token_a, user_a = register_user(client, "Analyst A", "analyst_a@domain.com")
    token_b, user_b = register_user(client, "Analyst B", "analyst_b@domain.com")

    # 1. User A uploads CSV
    csv_a = "product,revenue\nLaptop,1000\nPhone,500"
    upload_res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("sales_a.csv", io.BytesIO(csv_a.encode("utf-8")), "text/csv")},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert upload_res.status_code == 200
    dataset_a_id = upload_res.json()["dataset_id"]

    # 2. User A generates PDF report
    gen_res = client.post(
        "/api/v1/reports/generate",
        json={
            "title": "Analyst A Report",
            "report_format": "pdf",
            "dataset_id": dataset_a_id,
            "include_anomalies": False
        },
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert gen_res.status_code == 200
    report_a_id = gen_res.json()["id"]

    # 3. User A lists reports (sees 1 report)
    list_a = client.get("/api/v1/reports", headers={"Authorization": f"Bearer {token_a}"}).json()
    assert len(list_a) == 1
    assert list_a[0]["id"] == report_a_id

    # 4. User B lists reports (sees 0 reports)
    list_b = client.get("/api/v1/reports", headers={"Authorization": f"Bearer {token_b}"}).json()
    assert len(list_b) == 0

    # 5. User B attempts to download User A's report (MUST BE REJECTED)
    dl_b = client.get(f"/api/v1/reports/{report_a_id}/download", headers={"Authorization": f"Bearer {token_b}"})
    assert dl_b.status_code in (404, 403)

    # 6. User A downloads report (SUCCESS)
    dl_a = client.get(f"/api/v1/reports/{report_a_id}/download", headers={"Authorization": f"Bearer {token_a}"})
    assert dl_a.status_code == 200
    assert dl_a.headers["content-type"] == "application/pdf"
    assert dl_a.content.startswith(b"%PDF-")

    # 7. User B attempts to delete User A's report (MUST BE REJECTED)
    del_b = client.delete(f"/api/v1/reports/{report_a_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert del_b.status_code in (404, 403)

    # 8. User A deletes their report (SUCCESS)
    del_a = client.delete(f"/api/v1/reports/{report_a_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert del_a.status_code == 200


def test_comprehensive_pdf_report_and_pagination():
    """Verify that comprehensive PDF generation creates a rich multi-page (6-10 page) report."""
    import re
    from app.services.report_visualizer import ReportVisualizer

    analytics = {
        "dataset_name": "quarterly_sales.csv",
        "row_count": 500,
        "column_count": 8,
        "executive_narrative": "Paragraph 1: Top-line revenue surged to ₹50 Lakhs.\n\nParagraph 2: Electronics led contribution.\n\nParagraph 3: Reallocate promotional budget.",
        "kpis": {
            "total_revenue": 5000000,
            "total_cost": 3000000,
            "total_profit": 2000000,
            "gross_margin_pct": 40.0,
            "total_units": 12000,
            "total_orders": 500,
            "cards": [
                {"label": "Total Revenue", "formatted": "₹50.00 L", "status": "primary", "desc": "Gross turnover"},
                {"label": "Gross Profit", "formatted": "₹20.00 L", "status": "success", "desc": "Retained profit"},
                {"label": "Gross Margin", "formatted": "40.0%", "status": "success", "desc": "Margin efficiency"},
                {"label": "Total Units", "formatted": "12,000 Units", "status": "neutral", "desc": "Physical volume"},
            ]
        },
        "financials": {
            "revenue": 5000000,
            "cost": 3000000,
            "gross_profit": 2000000,
            "gross_margin_pct": 40.0,
            "cost_to_revenue_ratio": 60.0,
            "best_margin_category": "Software",
            "best_margin_region": "South"
        },
        "trends": {
            "available": True,
            "records": [
                {"month": "2024-01", "revenue": 1000000, "profit": 400000, "units": 2400, "orders": 100, "mom_growth_pct": None, "margin_pct": 40.0},
                {"month": "2024-02", "revenue": 1200000, "profit": 500000, "units": 2900, "orders": 120, "mom_growth_pct": 20.0, "margin_pct": 41.7},
                {"month": "2024-03", "revenue": 1500000, "profit": 600000, "units": 3600, "orders": 150, "mom_growth_pct": 25.0, "margin_pct": 40.0},
            ]
        },
        "regional": [
            {"name": "South", "revenue": 2500000, "profit": 1100000, "units": 6000, "orders": 250, "revenue_share_pct": 50.0, "margin_pct": 44.0},
            {"name": "North", "revenue": 2500000, "profit": 900000, "units": 6000, "orders": 250, "revenue_share_pct": 50.0, "margin_pct": 36.0},
        ],
        "products_top": [
            {"name": "Enterprise Suite", "revenue": 1500000, "profit": 750000, "units": 300, "revenue_share_pct": 30.0, "margin_pct": 50.0},
            {"name": "Cloud Storage", "revenue": 1000000, "profit": 450000, "units": 1500, "revenue_share_pct": 20.0, "margin_pct": 45.0},
        ],
        "categories": [
            {"name": "Software", "revenue": 3000000, "profit": 1500000, "units": 5000, "revenue_share_pct": 60.0, "margin_pct": 50.0},
            {"name": "Services", "revenue": 2000000, "profit": 500000, "units": 7000, "revenue_share_pct": 40.0, "margin_pct": 25.0},
        ],
        "anomalies": [
            {"category": "Revenue Outlier", "metric": "revenue", "detail": "Spike in Enterprise Suite orders", "severity": "HIGH", "implication": "Verify customer contract"},
        ],
        "analyst_insights": [
            {
                "title": "Software Margin Outperformance",
                "finding": "Software generates 60% of revenue and 75% of profit.",
                "evidence": "Software margin reached 50% vs Services at 25%.",
                "significance": "High profitability segment anchors bottom-line stability.",
                "action": "Prioritize direct outbound sales for software tiers."
            }
        ],
        "recommendations": [
            {
                "priority": "HIGH",
                "area": "Catalog Margin Mix",
                "action": "Package high-margin software licenses with services.",
                "expected_impact": "5-8% lift in blended gross margin."
            }
        ],
        "data_quality": {
            "total_rows": 500,
            "total_columns": 8,
            "completeness_score": 99.8,
            "duplicate_count": 0,
            "date_range": "2024-01-01 to 2024-03-31"
        },
        "metric_definitions": [
            {"metric": "Gross Margin", "definition": "(Revenue - COGS) / Revenue"}
        ]
    }

    pdf_bytes = PDFReportGenerator.generate_comprehensive_report(analytics, title="Executive Digest")
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-")
    pages = len(re.findall(rb'/Type\s*/Page\b', pdf_bytes))
    assert pages >= 6, f"Expected at least 6 pages, got {pages}"


def test_comprehensive_excel_multi_sheet_workbook():
    """Verify that comprehensive Excel generation builds structured multi-sheet workbook."""
    analytics = {
        "dataset_name": "finance.csv",
        "row_count": 100,
        "column_count": 5,
        "executive_narrative": "Comprehensive financial review.",
        "kpis": {"cards": [{"label": "Revenue", "formatted": "₹10.00 L", "status": "primary"}]},
        "trends": {"available": True, "records": [{"month": "2024-01", "revenue": 100000, "profit": 40000, "units": 500, "orders": 20, "mom_growth_pct": 0, "margin_pct": 40.0}]},
        "regional": [{"name": "West", "revenue": 100000, "profit": 40000, "units": 500, "orders": 20, "revenue_share_pct": 100.0, "margin_pct": 40.0}],
        "products_top": [{"name": "Alpha Item", "revenue": 100000, "profit": 40000, "units": 500, "revenue_share_pct": 100.0, "margin_pct": 40.0}],
        "categories": [{"name": "Tech", "revenue": 100000, "profit": 40000, "units": 500, "revenue_share_pct": 100.0, "margin_pct": 40.0}],
        "anomalies": [{"category": "Outlier", "metric": "price", "detail": "High price", "severity": "MEDIUM", "implication": "Review"}],
        "analyst_insights": [{"title": "Tech Lead", "finding": "Tech dominates", "evidence": "100%", "significance": "Key driver", "action": "Scale"}],
        "recommendations": [{"priority": "HIGH", "area": "Pricing", "action": "Optimize", "expected_impact": "High"}],
        "data_quality": {"total_rows": 100, "total_columns": 5, "completeness_score": 100.0, "duplicate_count": 0, "date_range": "2024-01-01"}
    }
    raw_data = [{"id": 1, "product": "Alpha", "revenue": "=100+200"}]
    xls_bytes = ExcelReportGenerator.generate_comprehensive_workbook(analytics, raw_table_data=raw_data)
    wb = openpyxl.load_workbook(io.BytesIO(xls_bytes))

    assert "Executive Summary" in wb.sheetnames
    assert "KPI Dashboard" in wb.sheetnames
    assert "Revenue Trends" in wb.sheetnames
    assert "Regional Performance" in wb.sheetnames
    assert "Product Performance" in wb.sheetnames
    assert "Category Breakdown" in wb.sheetnames
    assert "Anomaly Audit" in wb.sheetnames
    assert "Analyst Insights & Strategy" in wb.sheetnames
    assert "Source Data Partition" in wb.sheetnames

    # Check formula injection defense in source data sheet
    ws_src = wb["Source Data Partition"]
    assert str(ws_src.cell(row=2, column=3).value).startswith("'=")
