import io
from typing import Dict, Any, List, Optional
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from app.utils.formatters import format_val


def sanitize_formula_injection(val: Any) -> Any:
    """
    Sanitize values to prevent spreadsheet formula injection vulnerabilities.
    Prepends a single quote to strings starting with '=', '+', '-', '@', '\t', '\r'.
    """
    if isinstance(val, str) and len(val) > 0:
        if val[0] in ("=", "+", "-", "@", "\t", "\r"):
            return f"'{val}"
    return val


class ExcelReportGenerator:
    """
    Corporate Multi-Sheet Excel Business Intelligence Generator.
    Exports verified analytics into a structured, executive-styled spreadsheet.
    """

    @classmethod
    def generate_comprehensive_workbook(
        cls,
        analytics: Dict[str, Any],
        raw_table_data: Optional[List[Dict[str, Any]]] = None
    ) -> bytes:
        wb = openpyxl.Workbook()
        # Remove default empty sheet
        default_sheet = wb.active

        # Corporate Styles
        font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        font_bold = Font(name="Calibri", size=10, bold=True, color="0F172A")
        font_regular = Font(name="Calibri", size=10, color="334155")
        font_title = Font(name="Calibri", size=14, bold=True, color="0F172A")
        font_sub = Font(name="Calibri", size=11, bold=True, color="2563EB")

        fill_header = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
        fill_sub = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
        fill_zebra = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
        fill_accent = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")

        border_side = Side(style="thin", color="E2E8F0")
        border_thin = Border(left=border_side, right=border_side, top=border_side, bottom=border_side)

        align_left = Alignment(horizontal="left", vertical="center")
        align_right = Alignment(horizontal="right", vertical="center")
        align_center = Alignment(horizontal="center", vertical="center")

        gen_time = (analytics.get("generated_at") or datetime.now()).strftime("%Y-%m-%d %H:%M:%S UTC")

        # ━━━━━━━━ 1. SHEET: Executive Summary ━━━━━━━━
        ws_exec = wb.create_sheet(title="Executive Summary")
        ws_exec.views.sheetView[0].showGridLines = True

        ws_exec.cell(row=1, column=1, value="INSLIGHT AI BUSINESS INTELLIGENCE — EXECUTIVE REPORT").font = font_title
        ws_exec.cell(row=2, column=1, value=f"Dataset: {analytics.get('dataset_name')} | Generated: {gen_time}").font = font_sub

        metadata = [
            ("Scope of Evaluation", f"{analytics.get('row_count', 0):,} records across {analytics.get('column_count', 0)} dimensions"),
            ("Date Coverage", analytics.get("data_quality", {}).get("date_range", "All Historical Periods")),
            ("Completeness Score", f"{analytics.get('data_quality', {}).get('completeness_score', 100)}%"),
            ("Target Currency", "Indian Rupee (₹, Lakhs / Crores)"),
            ("Document Classification", "CONFIDENTIAL — EXECUTIVE MANAGEMENT")
        ]
        row_idx = 4
        for k, v in metadata:
            c1 = ws_exec.cell(row=row_idx, column=1, value=sanitize_formula_injection(k))
            c2 = ws_exec.cell(row=row_idx, column=2, value=sanitize_formula_injection(v))
            c1.font = font_bold
            c2.font = font_regular
            c1.border = border_thin
            c2.border = border_thin
            row_idx += 1

        row_idx += 1
        ws_exec.cell(row=row_idx, column=1, value="EXECUTIVE COMMENTARY").font = font_bold
        row_idx += 1
        narrative = analytics.get("executive_narrative", "").replace("**", "").replace("`", "")
        for p in narrative.split("\n\n"):
            if p.strip():
                c = ws_exec.cell(row=row_idx, column=1, value=sanitize_formula_injection(p.strip()))
                c.font = font_regular
                row_idx += 1

        # ━━━━━━━━ 2. SHEET: KPI Dashboard ━━━━━━━━
        ws_kpi = wb.create_sheet(title="KPI Dashboard")
        ws_kpi.views.sheetView[0].showGridLines = True
        ws_kpi.freeze_panes = "A2"

        kpi_headers = ["Key Performance Indicator", "Reported Value", "Unit / Metric Type", "Business Definition"]
        for col_idx, h in enumerate(kpi_headers, 1):
            cell = ws_kpi.cell(row=1, column=col_idx, value=h)
            cell.font = font_header
            cell.fill = fill_header
            cell.border = border_thin

        kpi_cards = analytics.get("kpis", {}).get("cards", [])
        for r_idx, k in enumerate(kpi_cards, 2):
            vals = [
                sanitize_formula_injection(k["label"]),
                sanitize_formula_injection(str(k["formatted"])),
                sanitize_formula_injection(k.get("status", "neutral").upper()),
                sanitize_formula_injection(k.get("desc", ""))
            ]
            for c_idx, val in enumerate(vals, 1):
                c = ws_kpi.cell(row=r_idx, column=c_idx, value=val)
                c.font = font_bold if c_idx == 1 else font_regular
                c.border = border_thin
                if r_idx % 2 == 1:
                    c.fill = fill_zebra

        # ━━━━━━━━ 3. SHEET: Revenue Trends ━━━━━━━━
        trends_info = analytics.get("trends", {})
        if trends_info.get("available") and trends_info.get("records"):
            ws_trends = wb.create_sheet(title="Revenue Trends")
            ws_trends.views.sheetView[0].showGridLines = True
            ws_trends.freeze_panes = "A2"

            t_headers = ["Period Month", "Gross Revenue (₹)", "Operating Profit (₹)", "Gross Margin %", "Units Sold", "Order Volume", "MoM Velocity %"]
            for col_idx, h in enumerate(t_headers, 1):
                cell = ws_trends.cell(row=1, column=col_idx, value=h)
                cell.font = font_header
                cell.fill = fill_header
                cell.border = border_thin

            for r_idx, rec in enumerate(trends_info["records"], 2):
                mom = f"{rec['mom_growth_pct']:+.1f}%" if rec["mom_growth_pct"] is not None else "Baseline"
                row_data = [
                    rec["month"],
                    rec["revenue"],
                    rec["profit"],
                    f"{rec['margin_pct']:.1f}%",
                    rec["units"],
                    rec["orders"],
                    mom
                ]
                for c_idx, val in enumerate(row_data, 1):
                    c = ws_trends.cell(row=r_idx, column=c_idx, value=sanitize_formula_injection(val))
                    c.font = font_regular
                    c.border = border_thin
                    if c_idx in (2, 3, 5, 6):
                        c.alignment = align_right
                    if r_idx % 2 == 1:
                        c.fill = fill_zebra

        # ━━━━━━━━ 4. SHEET: Regional Analysis ━━━━━━━━
        regional = analytics.get("regional", [])
        if regional:
            ws_reg = wb.create_sheet(title="Regional Performance")
            ws_reg.views.sheetView[0].showGridLines = True
            ws_reg.freeze_panes = "A2"

            reg_headers = ["Geographic Territory", "Gross Revenue (₹)", "Operating Profit (₹)", "Revenue Share %", "Gross Margin %", "Order Volume", "Units Sold"]
            for col_idx, h in enumerate(reg_headers, 1):
                cell = ws_reg.cell(row=1, column=col_idx, value=h)
                cell.font = font_header
                cell.fill = fill_header
                cell.border = border_thin

            for r_idx, r in enumerate(regional, 2):
                row_data = [
                    r["name"],
                    r["revenue"],
                    r["profit"],
                    f"{r['revenue_share_pct']:.1f}%",
                    f"{r['margin_pct']:.1f}%",
                    r["orders"],
                    r["units"]
                ]
                for c_idx, val in enumerate(row_data, 1):
                    c = ws_reg.cell(row=r_idx, column=c_idx, value=sanitize_formula_injection(val))
                    c.font = font_bold if c_idx == 1 else font_regular
                    c.border = border_thin
                    if c_idx in (2, 3, 6, 7):
                        c.alignment = align_right
                    if r_idx % 2 == 1:
                        c.fill = fill_zebra

        # ━━━━━━━━ 5. SHEET: Product Analysis ━━━━━━━━
        products = analytics.get("products_top", [])
        if products:
            ws_prod = wb.create_sheet(title="Product Performance")
            ws_prod.views.sheetView[0].showGridLines = True
            ws_prod.freeze_panes = "A2"

            prod_headers = ["Product / SKU Name", "Gross Revenue (₹)", "Operating Profit (₹)", "Units Sold", "Contribution Share %", "Margin Rate %"]
            for col_idx, h in enumerate(prod_headers, 1):
                cell = ws_prod.cell(row=1, column=col_idx, value=h)
                cell.font = font_header
                cell.fill = fill_header
                cell.border = border_thin

            for r_idx, p in enumerate(products, 2):
                row_data = [
                    p["name"],
                    p["revenue"],
                    p["profit"],
                    p["units"],
                    f"{p['revenue_share_pct']:.1f}%",
                    f"{p['margin_pct']:.1f}%"
                ]
                for c_idx, val in enumerate(row_data, 1):
                    c = ws_prod.cell(row=r_idx, column=c_idx, value=sanitize_formula_injection(val))
                    c.font = font_bold if c_idx == 1 else font_regular
                    c.border = border_thin
                    if c_idx in (2, 3, 4):
                        c.alignment = align_right
                    if r_idx % 2 == 1:
                        c.fill = fill_zebra

        # ━━━━━━━━ 6. SHEET: Category Analysis ━━━━━━━━
        categories = analytics.get("categories", [])
        if categories:
            ws_cat = wb.create_sheet(title="Category Breakdown")
            ws_cat.views.sheetView[0].showGridLines = True
            ws_cat.freeze_panes = "A2"

            cat_headers = ["Product Category", "Gross Revenue (₹)", "Operating Profit (₹)", "Volume Units", "Revenue Share %", "Gross Margin %"]
            for col_idx, h in enumerate(cat_headers, 1):
                cell = ws_cat.cell(row=1, column=col_idx, value=h)
                cell.font = font_header
                cell.fill = fill_header
                cell.border = border_thin

            for r_idx, c in enumerate(categories, 2):
                row_data = [
                    c["name"],
                    c["revenue"],
                    c["profit"],
                    c["units"],
                    f"{c['revenue_share_pct']:.1f}%",
                    f"{c['margin_pct']:.1f}%"
                ]
                for c_idx, val in enumerate(row_data, 1):
                    cell = ws_cat.cell(row=r_idx, column=c_idx, value=sanitize_formula_injection(val))
                    cell.font = font_bold if c_idx == 1 else font_regular
                    cell.border = border_thin
                    if c_idx in (2, 3, 4):
                        cell.alignment = align_right
                    if r_idx % 2 == 1:
                        cell.fill = fill_zebra

        # ━━━━━━━━ 7. SHEET: Operational Anomalies ━━━━━━━━
        anomalies = analytics.get("anomalies", [])
        if anomalies:
            ws_anom = wb.create_sheet(title="Anomaly Audit")
            ws_anom.views.sheetView[0].showGridLines = True
            ws_anom.freeze_panes = "A2"

            anom_headers = ["Outlier Classification", "Target Metric", "Observed Transaction Detail", "Severity Level", "Audit Implication"]
            for col_idx, h in enumerate(anom_headers, 1):
                cell = ws_anom.cell(row=1, column=col_idx, value=h)
                cell.font = font_header
                cell.fill = fill_header
                cell.border = border_thin

            for r_idx, a in enumerate(anomalies, 2):
                row_data = [
                    a["category"],
                    a["metric"],
                    a["detail"],
                    a["severity"],
                    a["implication"]
                ]
                for c_idx, val in enumerate(row_data, 1):
                    cell = ws_anom.cell(row=r_idx, column=c_idx, value=sanitize_formula_injection(val))
                    cell.font = font_bold if c_idx in (1, 4) else font_regular
                    cell.border = border_thin
                    if r_idx % 2 == 1:
                        cell.fill = fill_zebra

        # ━━━━━━━━ 8. SHEET: Analyst Insights & Strategy ━━━━━━━━
        insights = analytics.get("analyst_insights", [])
        recs = analytics.get("recommendations", [])
        if insights or recs:
            ws_strat = wb.create_sheet(title="Analyst Insights & Strategy")
            ws_strat.views.sheetView[0].showGridLines = True
            ws_strat.freeze_panes = "A2"

            strat_headers = ["Insight Dimension", "Specific Finding", "Empirical Evidence", "Business Significance", "Actionable Directive"]
            for col_idx, h in enumerate(strat_headers, 1):
                cell = ws_strat.cell(row=1, column=col_idx, value=h)
                cell.font = font_header
                cell.fill = fill_header
                cell.border = border_thin

            for r_idx, ins in enumerate(insights, 2):
                row_data = [
                    ins["title"],
                    ins["finding"],
                    ins["evidence"],
                    ins["significance"],
                    ins["action"]
                ]
                for c_idx, val in enumerate(row_data, 1):
                    cell = ws_strat.cell(row=r_idx, column=c_idx, value=sanitize_formula_injection(val))
                    cell.font = font_bold if c_idx == 1 else font_regular
                    cell.border = border_thin
                    if r_idx % 2 == 1:
                        cell.fill = fill_zebra

        # ━━━━━━━━ 9. SHEET: Source Data Partition ━━━━━━━━
        if raw_table_data:
            ws_raw = wb.create_sheet(title="Source Data Partition")
            ws_raw.views.sheetView[0].showGridLines = True
            ws_raw.freeze_panes = "A2"

            raw_cols = list(raw_table_data[0].keys())
            for col_idx, col_name in enumerate(raw_cols, 1):
                cell = ws_raw.cell(row=1, column=col_idx, value=col_name.replace("_", " ").title())
                cell.font = font_header
                cell.fill = fill_header
                cell.border = border_thin

            for r_idx, row in enumerate(raw_table_data[:100], 2):
                for c_idx, col_name in enumerate(raw_cols, 1):
                    val = row.get(col_name)
                    cell = ws_raw.cell(row=r_idx, column=c_idx, value=sanitize_formula_injection(val))
                    cell.font = font_regular
                    cell.border = border_thin
                    if r_idx % 2 == 1:
                        cell.fill = fill_zebra

        # Remove default empty sheet if unused
        if default_sheet in wb.worksheets and len(wb.worksheets) > 1:
            wb.remove(default_sheet)

        # Auto-adjust column widths across all sheets
        for sheet in wb.worksheets:
            for col in sheet.columns:
                max_len = 0
                col_letter = get_column_letter(col[0].column)
                for cell in col[:35]:
                    val_str = str(cell.value or "")
                    if len(val_str) > max_len:
                        max_len = len(val_str)
                sheet.column_dimensions[col_letter].width = max(12, min(max_len + 4, 60))

        out_buffer = io.BytesIO()
        wb.save(out_buffer)
        wb.close()
        out_buffer.seek(0)
        return out_buffer.getvalue()

    @classmethod
    def generate(
        cls,
        title: str,
        dataset_name: str,
        kpi_cards: List[Dict[str, Any]],
        narrative: str,
        table_data: List[Dict[str, Any]],
        anomalies: Optional[List[Any]] = None,
        data_quality: Optional[Dict[str, Any]] = None,
        generated_at: Optional[datetime] = None
    ) -> bytes:
        """
        Legacy 4-sheet generate method for query exports and backward compatibility.
        """
        data_quality = data_quality or {}
        wb = openpyxl.Workbook()
        gen_time = (generated_at or datetime.now()).strftime("%Y-%m-%d %H:%M:%S UTC")

        font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        font_bold = Font(name="Calibri", size=10, bold=True, color="0F172A")
        font_regular = Font(name="Calibri", size=10, color="334155")
        font_title = Font(name="Calibri", size=14, bold=True, color="0F172A")
        font_sub = Font(name="Calibri", size=11, bold=True, color="2563EB")

        fill_header = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
        fill_zebra = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
        border_thin = Border(
            left=Side(style="thin", color="E2E8F0"),
            right=Side(style="thin", color="E2E8F0"),
            top=Side(style="thin", color="E2E8F0"),
            bottom=Side(style="thin", color="E2E8F0")
        )

        # ━━━━━━━━ SHEET 1: Overview ━━━━━━━━
        ws_overview = wb.active
        ws_overview.title = "Overview"
        ws_overview.views.sheetView[0].showGridLines = True

        ws_overview.cell(row=1, column=1, value=sanitize_formula_injection(title)).font = font_title
        ws_overview.cell(row=2, column=1, value=f"Dataset: {dataset_name} | Generated: {gen_time}").font = font_sub

        meta_rows = [
            ("Dataset Name", dataset_name),
            ("Generated At", gen_time),
            ("Record Count", len(table_data)),
            ("Quality Score", f"{data_quality.get('data_quality_score', 100)}%"),
            ("Currency", "Indian Rupee (₹)")
        ]
        row_idx = 4
        for attr, val in meta_rows:
            c1 = ws_overview.cell(row=row_idx, column=1, value=sanitize_formula_injection(str(attr)))
            c2 = ws_overview.cell(row=row_idx, column=2, value=sanitize_formula_injection(str(val)))
            c1.font = font_bold
            c2.font = font_regular
            c1.border = border_thin
            c2.border = border_thin
            row_idx += 1

        row_idx += 2
        ws_overview.cell(row=row_idx, column=1, value="Executive Summary").font = font_sub
        row_idx += 1
        clean_narrative = (narrative.replace("**", "").replace("`", "").replace("$", "₹") if narrative else "Standard analytics summary.")
        ws_overview.cell(row=row_idx, column=1, value=sanitize_formula_injection(clean_narrative))

        # ━━━━━━━━ SHEET 2: KPI Summary ━━━━━━━━
        ws_kpi = wb.create_sheet(title="KPI Summary")
        ws_kpi.views.sheetView[0].showGridLines = True
        kpi_headers = ["Metric Name", "Value", "Raw Column", "Aggregation", "Format"]
        for col_num, h in enumerate(kpi_headers, 1):
            cell = ws_kpi.cell(row=1, column=col_num, value=h)
            cell.font = font_header
            cell.fill = fill_header

        for r_idx, k in enumerate(kpi_cards, 2):
            val_raw = str(k.get("formatted_value") or k.get("value", 0)).replace("$", "₹")
            row_vals = [
                sanitize_formula_injection(k.get("label", "Metric")),
                sanitize_formula_injection(val_raw),
                sanitize_formula_injection(k.get("value_column", "-")),
                sanitize_formula_injection(k.get("aggregation", "sum")),
                sanitize_formula_injection(k.get("format", "number"))
            ]
            for c_num, v in enumerate(row_vals, 1):
                cell = ws_kpi.cell(row=r_idx, column=c_num, value=v)
                cell.border = border_thin
                if r_idx % 2 == 1:
                    cell.fill = fill_zebra

        # ━━━━━━━━ SHEET 3: Query Results ━━━━━━━━
        ws_data = wb.create_sheet(title="Query Results")
        ws_data.views.sheetView[0].showGridLines = True
        if table_data:
            columns = list(table_data[0].keys())
            for col_num, col_name in enumerate(columns, 1):
                cell = ws_data.cell(row=1, column=col_num, value=col_name.replace("_", " ").title())
                cell.font = font_header
                cell.fill = fill_header

            for r_idx, row in enumerate(table_data, 2):
                for c_num, col_name in enumerate(columns, 1):
                    raw_val = row.get(col_name)
                    safe_val = sanitize_formula_injection(raw_val)
                    cell = ws_data.cell(row=r_idx, column=c_num, value=safe_val)
                    cell.border = border_thin
                    if r_idx % 2 == 1:
                        cell.fill = fill_zebra

        # ━━━━━━━━ SHEET 4: Business Insights ━━━━━━━━
        ws_insights = wb.create_sheet(title="Business Insights")
        ws_insights.views.sheetView[0].showGridLines = True
        ws_insights.cell(row=1, column=1, value="Insight / Finding Category").font = font_header
        ws_insights.cell(row=1, column=1).fill = fill_header
        ws_insights.cell(row=1, column=2, value="Details & Recommended Actions").font = font_header
        ws_insights.cell(row=1, column=2).fill = fill_header

        insight_items = [
            ("Executive Summary", clean_narrative),
            ("Dataset Health", f"Data quality score is {data_quality.get('data_quality_score', 100)}% with {len(table_data)} evaluated rows."),
        ]
        if anomalies:
            for i, a in enumerate(anomalies[:5], 1):
                if isinstance(a, dict):
                    col = a.get("column", a.get("metric", "Metric"))
                    val = str(a.get("value", "N/A")).replace("$", "₹")
                    idx = a.get("date") or a.get("index", "N/A")
                    sev = a.get("severity", "medium")
                    anom_desc = f"Anomaly in {col}: observed {val} at {idx}, severity: {sev}"
                else:
                    anom_desc = f"Anomaly Alert: {str(a).replace('$', '₹')}"
                insight_items.append((f"Anomaly Alert #{i}", anom_desc))

        for r_idx, (cat, det) in enumerate(insight_items, 2):
            c1 = ws_insights.cell(row=r_idx, column=1, value=sanitize_formula_injection(cat))
            c2 = ws_insights.cell(row=r_idx, column=2, value=sanitize_formula_injection(det))
            c1.border = border_thin
            c2.border = border_thin
            c1.font = font_bold
            if r_idx % 2 == 1:
                c1.fill = fill_zebra

        # Auto column width
        for s in wb.worksheets:
            for col in s.columns:
                max_len = max(len(str(cell.value or "")) for cell in col[:20])
                col_letter = get_column_letter(col[0].column)
                s.column_dimensions[col_letter].width = max(12, min(max_len + 4, 50))

        out_buffer = io.BytesIO()
        wb.save(out_buffer)
        wb.close()
        out_buffer.seek(0)
        return out_buffer.getvalue()
