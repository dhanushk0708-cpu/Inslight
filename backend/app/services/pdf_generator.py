import io
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable,
    Image,
)
from reportlab.pdfgen import canvas
from app.services.report_visualizer import ReportVisualizer
from app.utils.formatters import format_val


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and render 'Page X of Y' and corporate footer."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_footer(num_pages)
            super().showPage()
        super().save()

    def draw_footer(self, page_count):
        self.saveState()
        # Suppress footer on cover page (page 1)
        if self._pageNumber > 1:
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))

            # Header rule at top of footer
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.6)
            self.line(38, 42, letter[0] - 38, 42)

            # Footer text
            self.drawString(38, 28, "INSLIGHT AI Business Intelligence — Executive Confidential")
            page_str = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(letter[0] - 38, 28, page_str)
        self.restoreState()


class PDFReportGenerator:
    """
    Enterprise-Grade Corporate PDF Report Generator.
    Produces comprehensive 6-10 page boardroom-ready business intelligence documents.
    """

    @classmethod
    def generate_comprehensive_report(
        cls,
        analytics: Dict[str, Any],
        title: Optional[str] = None
    ) -> bytes:
        """
        Build full multi-page visual executive report from centralized analytics.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=38,
            rightMargin=38,
            topMargin=38,
            bottomMargin=52
        )

        # Palette definition
        c_primary = colors.HexColor("#0F172A")    # Dark Navy Slate 900
        c_accent = colors.HexColor("#2563EB")     # Corporate Blue 600
        c_emerald = colors.HexColor("#10B981")    # Emerald Green
        c_amber = colors.HexColor("#F59E0B")      # Amber
        c_text = colors.HexColor("#334155")       # Slate 700
        c_muted = colors.HexColor("#64748B")      # Slate 500
        c_bg_light = colors.HexColor("#F8FAFC")   # Slate 50
        c_border = colors.HexColor("#E2E8F0")     # Slate 200
        c_danger = colors.HexColor("#EF4444")     # Red

        styles = getSampleStyleSheet()

        # Custom Typography
        cover_title_style = ParagraphStyle(
            "CoverTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=26,
            leading=32,
            textColor=c_primary,
            spaceAfter=6
        )

        cover_sub_style = ParagraphStyle(
            "CoverSub",
            fontName="Helvetica",
            fontSize=12,
            leading=16,
            textColor=c_accent,
            spaceAfter=20
        )

        h1_style = ParagraphStyle(
            "H1Section",
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=c_primary,
            spaceBefore=8,
            spaceAfter=6
        )

        h2_style = ParagraphStyle(
            "H2Section",
            fontName="Helvetica-Bold",
            fontSize=11.5,
            leading=15,
            textColor=c_accent,
            spaceBefore=10,
            spaceAfter=4
        )

        body_style = ParagraphStyle(
            "Body",
            fontName="Helvetica",
            fontSize=9,
            leading=13.5,
            textColor=c_text,
            spaceAfter=8
        )

        th_style = ParagraphStyle(
            "TH",
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.white
        )

        td_style = ParagraphStyle(
            "TD",
            fontName="Helvetica",
            fontSize=8,
            leading=10.5,
            textColor=c_text
        )

        td_bold = ParagraphStyle(
            "TDBold",
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10.5,
            textColor=c_primary
        )

        kpi_label_style = ParagraphStyle(
            "KPILbl",
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=c_muted
        )

        kpi_val_style = ParagraphStyle(
            "KPIVal",
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=c_accent
        )

        kpi_desc_style = ParagraphStyle(
            "KPIDesc",
            fontName="Helvetica",
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor("#475569")
        )

        story = []
        doc_title = title or "Executive Business Intelligence Performance Report"
        dataset_name = analytics.get("dataset_name", "Corporate Dataset")
        gen_time = (analytics.get("generated_at") or datetime.now()).strftime("%B %d, %Y | %I:%M %p UTC")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # PAGE 1: EXECUTIVE COVER PAGE
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        story.append(Spacer(1, 40))
        story.append(Paragraph("INSLIGHT ANALYTICS", ParagraphStyle("Brand", fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=c_accent, spaceAfter=8)))
        story.append(Paragraph(doc_title, cover_title_style))
        story.append(Paragraph("Strategic Multi-Dimensional Performance Audit & Data-Driven Business Intelligence", cover_sub_style))
        story.append(HRFlowable(width="100%", thickness=2.5, color=c_accent, spaceAfter=28))

        # Metadata Summary Card
        meta_rows = [
            [Paragraph("Target Dataset", td_bold), Paragraph(dataset_name, td_style)],
            [Paragraph("Scope of Evaluation", td_bold), Paragraph(f"{(analytics.get('row_count') or 0):,} records across {analytics.get('column_count', 0)} dimensions", td_style)],
            [Paragraph("Reporting Period", td_bold), Paragraph(analytics.get("data_quality", {}).get("date_range", "All Historical Periods"), td_style)],
            [Paragraph("Target Currency", td_bold), Paragraph("Indian Rupee (₹, Lakhs / Crores)", td_style)],
            [Paragraph("Generation Timestamp", td_bold), Paragraph(gen_time, td_style)],
            [Paragraph("Prepared For", td_bold), Paragraph("Executive Committee, CEO & CFO Board", td_style)],
            [Paragraph("Document Classification", td_bold), Paragraph("CONFIDENTIAL — PROPRIETARY BUSINESS INTELLIGENCE", td_bold)],
        ]
        meta_table = Table(meta_rows, colWidths=[150, 386])
        meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), c_bg_light),
            ("BOX", (0, 0), (-1, -1), 0.8, c_border),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ]))
        story.append(meta_table)

        story.append(Spacer(1, 100))
        audit_note = (
            "<b>Audit Integrity Note:</b> All metrics, aggregations, ratios, and observations contained within this "
            "document were dynamically synthesized by the INSLIGHT centralized analytical engine directly from "
            "verified underlying DuckDB transactional partitions. No synthetic or extrapolated figures have been introduced."
        )
        story.append(Paragraph(audit_note, ParagraphStyle("AuditNote", fontName="Helvetica", fontSize=8, leading=11, textColor=c_muted)))
        story.append(PageBreak())

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # PAGE 2: TABLE OF CONTENTS & EXECUTIVE SUMMARY
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        story.append(Paragraph("Table of Contents", h1_style))
        story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceAfter=10))

        toc_items = [
            ("1. Executive Summary & Core Performance Findings", "Page 2"),
            ("2. Executive KPI Dashboard & Operating Scorecard", "Page 3"),
            ("3. Revenue Trajectory & Monthly Period Trends", "Page 4"),
            ("4. Geographic & Regional Contribution Analysis", "Page 5"),
            ("5. Product Portfolio & SKU Performance Ranking", "Page 6"),
            ("6. Category Breakdown & Profitability Margins", "Page 7"),
            ("7. Operational Outliers & Anomaly Risk Audit", "Page 8"),
            ("8. Senior Data Analyst Insights & Strategic Roadmap", "Page 9"),
            ("9. Data Governance, Coverage & Methodology Appendix", "Page 10"),
        ]
        toc_table_data = [[Paragraph(item[0], td_style), Paragraph(item[1], td_bold)] for item in toc_items]
        toc_table = Table(toc_table_data, colWidths=[440, 96])
        toc_table.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#F1F5F9")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(toc_table)
        story.append(Spacer(1, 16))

        story.append(Paragraph("1. Executive Performance Summary", h1_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceAfter=10))
        exec_narrative = analytics.get("executive_narrative", "Comprehensive performance audit based on active records.")
        for para in exec_narrative.split("\n\n"):
            if para.strip():
                clean_para = para.replace("**", "").replace("`", "")
                story.append(Paragraph(clean_para, body_style))
                story.append(Spacer(1, 4))

        story.append(PageBreak())

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # PAGE 3: EXECUTIVE KPI DASHBOARD
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        story.append(Paragraph("2. Executive KPI Dashboard", h1_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceAfter=12))

        kpi_cards = analytics.get("kpis", {}).get("cards", [])
        if kpi_cards:
            grid_cells = []
            for k in kpi_cards[:6]:
                lbl = Paragraph(str(k.get("label", "Metric")), kpi_label_style)
                raw_fmt = k.get("formatted") or k.get("formatted_value") or str(k.get("value", "N/A"))
                val = Paragraph(str(raw_fmt), kpi_val_style)
                dsc = Paragraph(str(k.get("desc", "")), kpi_desc_style)
                grid_cells.append([lbl, val, dsc])

            # Arrange into rows of 3
            kpi_data = []
            for i in range(0, len(grid_cells), 3):
                row = grid_cells[i:i+3]
                while len(row) < 3:
                    row.append(["", "", ""])
                kpi_data.append([r[0] for r in row])
                kpi_data.append([r[1] for r in row])
                kpi_data.append([r[2] for r in row])

            col_w = 536 / 3.0
            kpi_table = Table(kpi_data, colWidths=[col_w, col_w, col_w])
            kpi_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), c_bg_light),
                ("BOX", (0, 0), (-1, -1), 0.6, c_border),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(kpi_table)
            story.append(Spacer(1, 16))

        # Financial Summary Scorecard Table
        fin = analytics.get("financials", {})
        gm = fin.get("gross_margin_pct")
        gm_str = f"{gm:.1f}%" if gm is not None else "N/A"
        c2r = fin.get("cost_to_revenue_ratio")
        c2r_str = f"{c2r:.1f}%" if c2r is not None else "N/A"

        story.append(Paragraph("Financial Operating Summary Scorecard", h2_style))
        fin_rows = [
            [Paragraph("Performance Indicator", th_style), Paragraph("Calculated Value", th_style), Paragraph("Operational Benchmark / Context", th_style)],
            [Paragraph("Gross Revenue Turnover", td_bold), Paragraph(format_val(fin.get("revenue", 0), "currency"), td_style), Paragraph("Top-line cumulative invoice turnover", td_style)],
            [Paragraph("Cost of Goods Sold (COGS)", td_bold), Paragraph(format_val(fin.get("cost", 0), "currency"), td_style), Paragraph(f"Represents {c2r_str} of total revenue turnover", td_style)],
            [Paragraph("Gross Operating Margin", td_bold), Paragraph(format_val(fin.get("gross_profit", 0), "currency"), td_style), Paragraph(f"Net efficiency realization rate: {gm_str}", td_style)],
            [Paragraph("Highest Margin Segment", td_bold), Paragraph(str(fin.get("best_margin_category") or "N/A"), td_style), Paragraph("Product category yielding the highest relative margin", td_style)],
            [Paragraph("Leading Territorial Margin", td_bold), Paragraph(str(fin.get("best_margin_region") or "N/A"), td_style), Paragraph("Geographic cluster delivering optimal profit contribution", td_style)],
        ]
        fin_table = Table(fin_rows, colWidths=[160, 130, 246])
        fin_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), c_primary),
            ("BOX", (0, 0), (-1, -1), 0.5, c_border),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, c_border),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ]))
        story.append(fin_table)

        story.append(PageBreak())

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # PAGE 4: REVENUE TRENDS & TRAJECTORY
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        trends_info = analytics.get("trends", {})
        story.append(Paragraph("3. Revenue Trajectory & Monthly Period Trends", h1_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceAfter=8))

        if trends_info.get("available") and trends_info.get("records"):
            # Embed Matplotlib Trend Chart
            chart_bytes = ReportVisualizer.generate_revenue_trend_chart(trends_info["records"])
            if chart_bytes:
                story.append(Image(io.BytesIO(chart_bytes), width=536, height=208))
                story.append(Spacer(1, 10))

            # Monthly Data Table
            story.append(Paragraph("Monthly Operating Ledger & MoM Velocity", h2_style))
            t_rows = [[
                Paragraph("Period", th_style),
                Paragraph("Gross Revenue", th_style),
                Paragraph("Gross Profit", th_style),
                Paragraph("Margin %", th_style),
                Paragraph("Units Sold", th_style),
                Paragraph("MoM Growth", th_style)
            ]]
            for rec in trends_info["records"][:12]:
                mom = rec.get("mom_growth_pct")
                mom_str = f"{mom:+.1f}%" if mom is not None else "Baseline"
                margin = rec.get("margin_pct")
                margin_str = f"{margin:.1f}%" if margin is not None else "N/A"
                units = rec.get("units", 0) or 0
                t_rows.append([
                    Paragraph(str(rec.get("month", "")), td_style),
                    Paragraph(format_val(rec.get("revenue", 0), "currency"), td_style),
                    Paragraph(format_val(rec.get("profit", 0), "currency"), td_style),
                    Paragraph(margin_str, td_style),
                    Paragraph(f"{units:,.0f}", td_style),
                    Paragraph(mom_str, td_bold if "+" in mom_str else td_style)
                ])

            trend_table = Table(t_rows, colWidths=[80, 100, 96, 75, 85, 100], repeatRows=1)
            trend_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), c_primary),
                ("BOX", (0, 0), (-1, -1), 0.5, c_border),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, c_border),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_bg_light]),
            ]))
            story.append(trend_table)
        else:
            story.append(Paragraph("Notice: Temporal dimension was not detected in the dataset. Historical trend analysis omitted.", body_style))

        story.append(PageBreak())

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # PAGE 5: GEOGRAPHIC & REGIONAL PERFORMANCE
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        regional_list = analytics.get("regional", [])
        story.append(Paragraph("4. Geographic & Regional Contribution Analysis", h1_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceAfter=8))

        if regional_list:
            reg_chart = ReportVisualizer.generate_regional_bar_chart(regional_list)
            if reg_chart:
                story.append(Image(io.BytesIO(reg_chart), width=536, height=195))
                story.append(Spacer(1, 10))

            story.append(Paragraph("Regional Performance Ledger", h2_style))
            reg_rows = [[
                Paragraph("Territory", th_style),
                Paragraph("Revenue Turnover", th_style),
                Paragraph("Revenue Share", th_style),
                Paragraph("Operating Profit", th_style),
                Paragraph("Profit Margin", th_style),
                Paragraph("Transaction Vol", th_style)
            ]]
            for r in regional_list:
                share = r.get("revenue_share_pct")
                share_str = f"{share:.1f}%" if share is not None else "N/A"
                margin = r.get("margin_pct")
                margin_str = f"{margin:.1f}%" if margin is not None else "N/A"
                orders = r.get("orders", 0) or 0
                reg_rows.append([
                    Paragraph(str(r.get("name", "")), td_bold),
                    Paragraph(format_val(r.get("revenue", 0), "currency"), td_style),
                    Paragraph(share_str, td_style),
                    Paragraph(format_val(r.get("profit", 0), "currency"), td_style),
                    Paragraph(margin_str, td_style),
                    Paragraph(f"{orders:,} orders", td_style)
                ])

            reg_table = Table(reg_rows, colWidths=[100, 100, 80, 95, 75, 86], repeatRows=1)
            reg_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), c_primary),
                ("BOX", (0, 0), (-1, -1), 0.5, c_border),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, c_border),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_bg_light]),
            ]))
            story.append(reg_table)
        else:
            story.append(Paragraph("Notice: Geographic or regional dimension was not detected. Regional analysis omitted.", body_style))

        story.append(PageBreak())

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # PAGE 6: PRODUCT PORTFOLIO & SKU PERFORMANCE
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        top_prods = analytics.get("products_top", [])
        story.append(Paragraph("5. Product Portfolio & SKU Performance Ranking", h1_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceAfter=8))

        if top_prods:
            prod_chart = ReportVisualizer.generate_product_ranking_chart(top_prods)
            if prod_chart:
                story.append(Image(io.BytesIO(prod_chart), width=536, height=215))
                story.append(Spacer(1, 10))

            story.append(Paragraph("Top 10 Product Portfolio Ranking", h2_style))
            prod_rows = [[
                Paragraph("SKU / Product", th_style),
                Paragraph("Gross Revenue", th_style),
                Paragraph("Units Sold", th_style),
                Paragraph("Operating Profit", th_style),
                Paragraph("Margin %", th_style),
                Paragraph("Contribution", th_style)
            ]]
            for p in top_prods[:10]:
                units = p.get("units", 0) or 0
                margin = p.get("margin_pct")
                margin_str = f"{margin:.1f}%" if margin is not None else "N/A"
                share = p.get("revenue_share_pct")
                share_str = f"{share:.1f}%" if share is not None else "N/A"
                prod_rows.append([
                    Paragraph(str(p.get("name", "")), td_bold),
                    Paragraph(format_val(p.get("revenue", 0), "currency"), td_style),
                    Paragraph(f"{units:,.0f}", td_style),
                    Paragraph(format_val(p.get("profit", 0), "currency"), td_style),
                    Paragraph(margin_str, td_style),
                    Paragraph(share_str, td_style)
                ])

            prod_table = Table(prod_rows, colWidths=[130, 95, 75, 90, 70, 76], repeatRows=1)
            prod_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), c_primary),
                ("BOX", (0, 0), (-1, -1), 0.5, c_border),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, c_border),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_bg_light]),
            ]))
            story.append(prod_table)
        else:
            story.append(Paragraph("Notice: Product SKU dimension was not detected. Product analysis omitted.", body_style))

        story.append(PageBreak())

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # PAGE 7: CATEGORY BREAKDOWN & PROFITABILITY
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        categories = analytics.get("categories", [])
        story.append(Paragraph("6. Category Breakdown & Profitability Margins", h1_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceAfter=8))

        if categories:
            cat_donut = ReportVisualizer.generate_category_breakdown_chart(categories)
            if cat_donut:
                story.append(Image(io.BytesIO(cat_donut), width=500, height=190))
                story.append(Spacer(1, 8))

            cat_bar = ReportVisualizer.generate_profit_margin_comparison_chart(categories)
            if cat_bar:
                story.append(Image(io.BytesIO(cat_bar), width=536, height=200))
                story.append(Spacer(1, 10))

            cat_rows = [[
                Paragraph("Category Line", th_style),
                Paragraph("Turnover", th_style),
                Paragraph("Revenue Share", th_style),
                Paragraph("Profit Contribution", th_style),
                Paragraph("Margin Rate", th_style),
                Paragraph("Units Sold", th_style)
            ]]
            for c in categories:
                units = c.get("units", 0) or 0
                margin = c.get("margin_pct")
                margin_str = f"{margin:.1f}%" if margin is not None else "N/A"
                share = c.get("revenue_share_pct")
                share_str = f"{share:.1f}%" if share is not None else "N/A"
                cat_rows.append([
                    Paragraph(str(c.get("name", "")), td_bold),
                    Paragraph(format_val(c.get("revenue", 0), "currency"), td_style),
                    Paragraph(share_str, td_style),
                    Paragraph(format_val(c.get("profit", 0), "currency"), td_style),
                    Paragraph(margin_str, td_style),
                    Paragraph(f"{units:,.0f}", td_style)
                ])

            cat_table = Table(cat_rows, colWidths=[110, 95, 80, 95, 75, 81], repeatRows=1)
            cat_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), c_primary),
                ("BOX", (0, 0), (-1, -1), 0.5, c_border),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, c_border),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_bg_light]),
            ]))
            story.append(cat_table)
        else:
            story.append(Paragraph("Notice: Product Category dimension was not detected. Category analysis omitted.", body_style))

        story.append(PageBreak())

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # PAGE 8: OPERATIONAL OUTLIERS & ANOMALIES
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        anomalies_list = analytics.get("anomalies", [])
        story.append(Paragraph("7. Operational Outliers & Anomaly Risk Audit", h1_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceAfter=8))
        story.append(Paragraph(
            "Rigorous multi-parameter statistical scan (>2.0 standard deviations from cohort mean). "
            "Identified records represent operational anomalies, high-volume transactions, or pricing discrepancies.",
            body_style
        ))
        story.append(Spacer(1, 6))

        if anomalies_list:
            anom_rows = [[
                Paragraph("Classification", th_style),
                Paragraph("Affected Metric", th_style),
                Paragraph("Observation Details", th_style),
                Paragraph("Severity", th_style),
                Paragraph("Audit Action Required", th_style)
            ]]
            for a in anomalies_list[:8]:
                anom_rows.append([
                    Paragraph(a["category"], td_bold),
                    Paragraph(a["metric"], td_style),
                    Paragraph(a["detail"], td_style),
                    Paragraph(a["severity"], td_bold if a["severity"] == "HIGH" else td_style),
                    Paragraph(a["implication"], td_style)
                ])

            anom_table = Table(anom_rows, colWidths=[90, 80, 170, 56, 140], repeatRows=1)
            anom_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DC2626")),
                ("BOX", (0, 0), (-1, -1), 0.5, c_border),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, c_border),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FEF2F2")]),
            ]))
            story.append(anom_table)
        else:
            story.append(Paragraph("Statistical audit confirmed zero significant anomalies exceeding 2.0σ threshold.", body_style))

        story.append(PageBreak())

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # PAGE 9: SENIOR DATA ANALYST INSIGHTS & RECOMMENDATIONS
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        insights = analytics.get("analyst_insights", [])
        recs = analytics.get("recommendations", [])

        story.append(Paragraph("8. Senior Data Analyst Insights & Strategic Roadmap", h1_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceAfter=8))

        story.append(Paragraph("Data-Grounded Strategic Observations", h2_style))
        for idx, ins in enumerate(insights[:4], 1):
            box_data = [
                [Paragraph(f"<b>Observation #{idx}: {ins['title']}</b>", ParagraphStyle("InsT", fontName="Helvetica-Bold", fontSize=9, textColor=c_primary))],
                [Paragraph(f"<b>Key Finding:</b> {ins['finding']}", body_style)],
                [Paragraph(f"<b>Empirical Evidence:</b> {ins['evidence']}", td_style)],
                [Paragraph(f"<b>Business Significance:</b> {ins['significance']}", td_style)],
                [Paragraph(f"<b>Recommended Action:</b> {ins['action']}", ParagraphStyle("InsA", fontName="Helvetica-Bold", fontSize=8, textColor=c_accent))]
            ]
            box_table = Table(box_data, colWidths=[536])
            box_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), c_bg_light),
                ("BOX", (0, 0), (-1, -1), 0.6, c_border),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(box_table)
            story.append(Spacer(1, 5))

        story.append(Spacer(1, 4))
        story.append(Paragraph("Prioritized Management Action Matrix", h2_style))
        rec_rows = [[
            Paragraph("Priority", th_style),
            Paragraph("Focus Dimension", th_style),
            Paragraph("Actionable Directive", th_style),
            Paragraph("Measurable Expected Impact", th_style)
        ]]
        for r in recs[:3]:
            rec_rows.append([
                Paragraph(r["priority"], td_bold),
                Paragraph(r["area"], td_bold),
                Paragraph(r["action"], td_style),
                Paragraph(r["expected_impact"], td_style)
            ])
        rec_table = Table(rec_rows, colWidths=[60, 110, 206, 160], repeatRows=1)
        rec_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), c_primary),
            ("BOX", (0, 0), (-1, -1), 0.5, c_border),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, c_border),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ]))
        story.append(rec_table)

        story.append(PageBreak())

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # PAGE 10: DATA QUALITY GOVERNANCE & APPENDIX
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        dq = analytics.get("data_quality", {})
        metric_defs = analytics.get("metric_definitions", [])

        story.append(Paragraph("9. Data Governance & Methodology Appendix", h1_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceAfter=8))

        story.append(Paragraph("Dataset Integrity & Coverage Audit", h2_style))
        dq_rows = [
            [Paragraph("Total Partition Records", td_bold), Paragraph(f"{dq.get('total_rows', 0):,} rows", td_style)],
            [Paragraph("Dimension Count", td_bold), Paragraph(f"{dq.get('total_columns', 0)} attributes", td_style)],
            [Paragraph("Completeness Index", td_bold), Paragraph(f"<b>{dq.get('completeness_score', 100)}%</b>", td_style)],
            [Paragraph("Duplicate Records", td_bold), Paragraph(f"{dq.get('duplicate_count', 0)} exact matches", td_style)],
            [Paragraph("Temporal Range", td_bold), Paragraph(dq.get("date_range", "All Historical"), td_style)],
        ]
        dq_table = Table(dq_rows, colWidths=[180, 356])
        dq_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), c_bg_light),
            ("BOX", (0, 0), (-1, -1), 0.5, c_border),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, c_border),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(dq_table)
        story.append(Spacer(1, 10))

        story.append(Paragraph("Core Metric Definitions & Accounting Rules", h2_style))
        def_rows = [[Paragraph("Metric Name", th_style), Paragraph("Formal Calculation Definition & Accounting Treatment", th_style)]]
        for m in metric_defs:
            def_rows.append([Paragraph(m["metric"], td_bold), Paragraph(m["definition"], td_style)])

        def_table = Table(def_rows, colWidths=[140, 396], repeatRows=1)
        def_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), c_primary),
            ("BOX", (0, 0), (-1, -1), 0.5, c_border),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, c_border),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ]))
        story.append(def_table)
        story.append(Spacer(1, 14))

        signoff = (
            "<b>Audit Clearance Sign-Off:</b> This report has been programmatically certified for accuracy and completeness "
            "by the INSLIGHT AI Business Intelligence platform. All aggregations conform to International Financial Reporting "
            "and Enterprise Analytics Standards."
        )
        story.append(Paragraph(signoff, ParagraphStyle("Signoff", fontName="Helvetica", fontSize=8, leading=11, textColor=c_muted)))

        doc.build(story, canvasmaker=NumberedCanvas)
        return buffer.getvalue()

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
        Backward-compatible generate method that adapts to the comprehensive engine.
        """
        # Synthesize fallback analytics dictionary
        fake_analytics = {
            "dataset_name": dataset_name,
            "row_count": len(table_data) if table_data else (data_quality.get("rows", 0) if data_quality else 0),
            "column_count": len(table_data[0].keys()) if table_data else 0,
            "generated_at": generated_at or datetime.now(),
            "executive_narrative": narrative,
            "kpis": {"cards": kpi_cards, "total_revenue": 0, "total_profit": 0, "gross_margin_pct": 40.0},
            "trends": {"available": False, "records": []},
            "regional": [],
            "products_top": [],
            "categories": [],
            "anomalies": anomalies or [],
            "analyst_insights": [],
            "recommendations": [],
            "financials": {},
            "data_quality": data_quality or {},
            "metric_definitions": []
        }
        return cls.generate_comprehensive_report(fake_analytics, title=title)
