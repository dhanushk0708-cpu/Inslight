import io
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pptx import Presentation as PptxPresentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.models.dataset import Dataset
from app.models.presentation import Presentation
from app.models.user import User
from app.services.business_guard import BusinessContextGuard, GUARD_REJECTION_MESSAGE
from app.services.dataset_service import DatasetService
from app.services.forecasting_service import ForecastingService
from app.services.strategic_analysis_service import StrategicAnalysisService

SUPPORTED_PRESENTATION_TYPES = [
    "Executive Business Review",
    "Monthly Sales Report",
    "Revenue Performance",
    "Regional Performance",
    "Product Performance",
    "Business Opportunities and Risks",
    "Forecasting Report",
    "Custom Business Presentation",
]


class PresentationService:
    """
    AI-Powered Business Presentation (.pptx) Generator.
    1. Grounds every statistic in actual DuckDB computations via StrategicAnalysisService & ForecastingService.
    2. Generates an editable structured slide outline for user review.
    3. Renders an executive 16:9 PowerPoint deck with embedded matplotlib charts.
    """

    @classmethod
    async def generate_outline(
        cls,
        dataset: Dataset,
        prompt: str,
        presentation_type: str,
    ) -> Dict[str, Any]:
        is_valid, reject_msg = await BusinessContextGuard.validate_query(
            question=prompt,
            has_dataset=True,
        )
        if not is_valid:
            raise ValueError(reject_msg or GUARD_REJECTION_MESSAGE)

        conn = DatasetService.get_duckdb_connection(dataset.storage_path, read_only=True)
        try:
            analysis = StrategicAnalysisService.analyze_business_performance(
                conn=conn,
                table_name=dataset.table_name,
                question=f"{presentation_type}: {prompt}",
                dataset_name=dataset.original_filename,
            )
            forecast = None
            if "forecast" in presentation_type.lower() or "forecast" in prompt.lower() or "executive" in presentation_type.lower():
                try:
                    forecast = ForecastingService.generate_forecast(conn, dataset.table_name, horizon=30)
                except Exception:
                    forecast = None
        finally:
            conn.close()

        kpis = analysis.get("kpi_results") or []
        opps = analysis.get("opportunities") or []
        risks = analysis.get("risks") or []
        charts = analysis.get("charts") or {}
        main_chart = charts.get("main_chart") or {}
        sec_chart = charts.get("secondary_chart") or {}
        evidence = analysis.get("evidence") or {}
        table = analysis.get("supporting_table") or {}

        deck_title = f"{presentation_type} — {dataset.original_filename.replace('.csv', '').replace('_', ' ').title()}"

        slides: List[Dict[str, Any]] = [
            {
                "slide_number": 1,
                "title": deck_title,
                "layout": "title",
                "bullets": [
                    f"Source Dataset: {dataset.original_filename} ({dataset.row_count:,} records)",
                    f"Focus: {prompt}",
                    f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
                ],
                "metric_highlight": f"{dataset.row_count:,} Verified Records",
                "notes": "Title slide grounded in verified dataset metadata.",
            },
            {
                "slide_number": 2,
                "title": "Executive Summary & Core Business KPIs",
                "layout": "kpis",
                "bullets": [
                    f"{k['label']}: {k['value']} ({k.get('trend', '')})" for k in kpis[:4]
                ] + [analysis.get("summary", "")],
                "metric_highlight": kpis[0]["value"] if kpis else None,
                "notes": "Calculated directly via DuckDB aggregations.",
            },
        ]

        slide_no = 3
        if main_chart and main_chart.get("data"):
            top_items = main_chart["data"][:4]
            slides.append({
                "slide_number": slide_no,
                "title": main_chart.get("title", "Segment Revenue Performance"),
                "layout": "chart_bar",
                "bullets": [
                    f"{d.get('name')}: ₹{float(d.get('Revenue', 0)):,.0f} revenue (Profit: ₹{float(d.get('Profit', 0)):,.0f})"
                    for d in top_items
                ],
                "metric_highlight": f"Top Segment: {top_items[0].get('name')}",
                "notes": "Bar chart generated from actual segment totals.",
            })
            slide_no += 1

        if sec_chart and sec_chart.get("data"):
            sec_items = sec_chart["data"][:4]
            slides.append({
                "slide_number": slide_no,
                "title": sec_chart.get("title", "Distribution Breakdown"),
                "layout": "chart_pie",
                "bullets": [
                    f"{d.get('name')}: ₹{float(d.get('Revenue', 0)):,.0f} ({d.get('Share', 0)}% share)"
                    for d in sec_items
                ],
                "metric_highlight": f"Leader Share: {sec_items[0].get('Share', 0)}%",
                "notes": "Share distribution computed from dataset records.",
            })
            slide_no += 1

        if table and table.get("rows"):
            top_rows = table["rows"][:5]
            slides.append({
                "slide_number": slide_no,
                "title": "Top Product & Segment Financial Breakdown",
                "layout": "bullets",
                "bullets": [
                    " | ".join(f"{k}: {v}" for k, v in list(r.items())[:4])
                    for r in top_rows
                ],
                "metric_highlight": f"Top {len(top_rows)} Performers",
                "notes": "Evidence table values.",
            })
            slide_no += 1

        if opps:
            slides.append({
                "slide_number": slide_no,
                "title": "Key Commercial Opportunities",
                "layout": "opportunities",
                "bullets": [
                    f"{'[HYPOTHESIS] ' if o.get('is_hypothesis') else ''}{o['title']} — {o.get('actual_value', o['impact'])}"
                    for o in opps[:3]
                ],
                "metric_highlight": f"{len(opps)} Identified Opportunities",
                "notes": "Distinguishes data-backed findings from hypothetical scenarios.",
            })
            slide_no += 1

        if risks:
            slides.append({
                "slide_number": slide_no,
                "title": "Structural Risks & Mitigations",
                "layout": "risks",
                "bullets": [
                    f"[{r['severity'].upper()}] {r['title']} — {r.get('mitigation', r['impact'])}"
                    for r in risks[:3]
                ],
                "metric_highlight": f"{len(risks)} Prioritized Risks",
                "notes": "Risk severity and evidence-backed mitigations.",
            })
            slide_no += 1

        if forecast and forecast.get("status") == "success":
            slides.append({
                "slide_number": slide_no,
                "title": "30-Period Predictive Revenue Forecast",
                "layout": "chart_line",
                "bullets": [
                    f"Selected Model: {forecast.get('method_used', 'auto').replace('_', ' ').title()}",
                    f"Projected Total: {forecast.get('formatted_forecast_total', 'N/A')}",
                    f"Trend Direction: {forecast.get('trend_direction', 'stable').title()}",
                    f"Backtest MAPE: {forecast.get('metrics', {}).get('mape', 'N/A')}%",
                ],
                "metric_highlight": forecast.get("formatted_forecast_total"),
                "notes": "Time-series forecast with 95% confidence bounds.",
            })
            slide_no += 1

        slides.append({
            "slide_number": slide_no,
            "title": "Strategic Recommendations & Next Steps",
            "layout": "conclusion",
            "bullets": [o["recommendation"] for o in opps[:2]] + [r["mitigation"] for r in risks[:2]],
            "metric_highlight": "Action Plan",
            "notes": "Recommended management actions grounded in dataset evidence.",
        })

        return {
            "status": "success",
            "dataset_id": dataset.id,
            "dataset_name": dataset.original_filename,
            "title": deck_title,
            "presentation_type": presentation_type,
            "slides": slides,
            "analytics_snapshot": {
                "kpi_results": kpis,
                "main_chart": main_chart,
                "secondary_chart": sec_chart,
                "evidence": evidence,
            },
        }

    @classmethod
    def _render_chart_png(cls, chart_cfg: Dict[str, Any], kind: str) -> Optional[io.BytesIO]:
        data = chart_cfg.get("data") or []
        if not data:
            return None

        fig, ax = plt.subplots(figsize=(6.2, 3.8), dpi=160)
        fig.patch.set_facecolor("#0f172a")
        ax.set_facecolor("#0f172a")

        labels = [str(d.get("name", ""))[:16] for d in data[:7]]
        values = [float(d.get("Revenue", 0)) for d in data[:7]]

        if kind == "pie":
            colors = ["#6366f1", "#10b981", "#38bdf8", "#f59e0b", "#ec4899", "#8b5cf6", "#14b8a6"]
            wedges, texts, autotexts = ax.pie(
                values,
                labels=labels,
                autopct="%1.1f%%",
                colors=colors[: len(labels)],
                textprops={"color": "#e2e8f0", "fontsize": 9},
                wedgeprops={"width": 0.48, "edgecolor": "#0f172a"},
            )
            for at in autotexts:
                at.set_color("#ffffff")
                at.set_fontsize(8)
        else:
            bars = ax.bar(labels, values, color="#6366f1", width=0.55)
            ax.tick_params(colors="#cbd5e1", labelsize=8)
            for spine in ["top", "right"]:
                ax.spines[spine].set_visible(False)
            for spine in ["bottom", "left"]:
                ax.spines[spine].set_color("#334155")
            ax.yaxis.grid(True, color="#1e293b", linestyle="--", linewidth=0.7)
            ax.set_axisbelow(True)
            for bar in bars:
                h = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    h,
                    f"₹{h/100000:.1f}L" if h >= 100000 else f"₹{h:,.0f}",
                    ha="center",
                    va="bottom",
                    color="#e2e8f0",
                    fontsize=7.5,
                )

        ax.set_title(chart_cfg.get("title", ""), color="#f8fafc", fontsize=11, fontweight="bold", pad=10)
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)
        return buf

    @classmethod
    def generate_pptx(
        cls,
        db: Session,
        user: User,
        dataset: Dataset,
        title: str,
        presentation_type: str,
        slides: List[Dict[str, Any]],
    ) -> Presentation:
        conn = DatasetService.get_duckdb_connection(dataset.storage_path, read_only=True)
        try:
            analysis = StrategicAnalysisService.analyze_business_performance(
                conn=conn,
                table_name=dataset.table_name,
                question=title,
                dataset_name=dataset.original_filename,
            )
        finally:
            conn.close()

        charts = analysis.get("charts") or {}
        main_chart = charts.get("main_chart")
        sec_chart = charts.get("secondary_chart")
        kpis = analysis.get("kpi_results") or []

        prs = PptxPresentation()
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)
        blank_layout = prs.slide_layouts[6]

        bg_dark = RGBColor(11, 15, 25)
        card_bg = RGBColor(20, 27, 45)
        accent = RGBColor(99, 102, 241)
        emerald = RGBColor(16, 185, 129)
        coral = RGBColor(248, 113, 113)
        text_light = RGBColor(243, 244, 246)
        text_muted = RGBColor(156, 163, 175)

        for idx, s in enumerate(slides):
            slide = prs.slides.add_slide(blank_layout)
            bg = slide.background.fill
            bg.solid()
            bg.fore_color.rgb = bg_dark

            # Top accent bar
            bar = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.333), Inches(0.08))
            bar.fill.solid()
            bar.fill.fore_color.rgb = accent
            bar.line.fill.background()

            layout = s.get("layout", "bullets")
            s_title = s.get("title", f"Slide {idx + 1}")
            bullets = s.get("bullets") or []
            highlight = s.get("metric_highlight")

            if layout == "title" or idx == 0:
                tb = slide.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(11.3), Inches(1.6))
                tf = tb.text_frame
                tf.word_wrap = True
                p = tf.paragraphs[0]
                p.text = s_title
                p.font.size = Pt(38)
                p.font.bold = True
                p.font.color.rgb = text_light

                sub_tb = slide.shapes.add_textbox(Inches(1.0), Inches(3.9), Inches(11.3), Inches(2.2))
                stf = sub_tb.text_frame
                stf.word_wrap = True
                for b_i, b in enumerate(bullets):
                    sp = stf.paragraphs[0] if b_i == 0 else stf.add_paragraph()
                    sp.text = f"•  {b}"
                    sp.font.size = Pt(18)
                    sp.font.color.rgb = text_muted
                    sp.space_after = Pt(10)

                footer = slide.shapes.add_textbox(Inches(1.0), Inches(6.6), Inches(11.3), Inches(0.4))
                fp = footer.text_frame.paragraphs[0]
                fp.text = f"INSLIGHT AI Business Intelligence  |  {presentation_type}"
                fp.font.size = Pt(12)
                fp.font.color.rgb = accent
                continue

            # Standard slide header
            hdr = slide.shapes.add_textbox(Inches(0.7), Inches(0.4), Inches(10.0), Inches(0.7))
            hp = hdr.text_frame.paragraphs[0]
            hp.text = s_title
            hp.font.size = Pt(24)
            hp.font.bold = True
            hp.font.color.rgb = text_light

            if highlight:
                badge = slide.shapes.add_textbox(Inches(10.2), Inches(0.42), Inches(2.5), Inches(0.5))
                bp = badge.text_frame.paragraphs[0]
                bp.alignment = PP_ALIGN.RIGHT
                bp.text = str(highlight)
                bp.font.size = Pt(13)
                bp.font.bold = True
                bp.font.color.rgb = emerald if layout == "opportunities" else (coral if layout == "risks" else accent)

            # KPI Cards row if layout == "kpis"
            content_top = 1.35
            if layout == "kpis" and kpis:
                card_w = Inches(2.8)
                gap = Inches(0.25)
                for k_i, k in enumerate(kpis[:4]):
                    left = Inches(0.7) + k_i * (card_w + gap)
                    rect = slide.shapes.add_shape(1, left, Inches(1.3), card_w, Inches(1.45))
                    rect.fill.solid()
                    rect.fill.fore_color.rgb = card_bg
                    rect.line.color.rgb = accent

                    ktb = slide.shapes.add_textbox(left + Inches(0.18), Inches(1.45), card_w - Inches(0.36), Inches(1.2))
                    ktf = ktb.text_frame
                    ktf.word_wrap = True
                    p1 = ktf.paragraphs[0]
                    p1.text = k["label"].upper()
                    p1.font.size = Pt(10)
                    p1.font.bold = True
                    p1.font.color.rgb = text_muted

                    p2 = ktf.add_paragraph()
                    p2.text = str(k["value"])
                    p2.font.size = Pt(22)
                    p2.font.bold = True
                    p2.font.color.rgb = text_light
                    p2.space_before = Pt(6)
                content_top = 3.1

            # Chart placement if chart slide
            chart_img = None
            if layout == "chart_bar" and main_chart:
                chart_img = cls._render_chart_png(main_chart, "bar")
            elif layout == "chart_pie" and sec_chart:
                chart_img = cls._render_chart_png(sec_chart, "pie")

            if chart_img:
                body_tb = slide.shapes.add_textbox(Inches(0.7), Inches(content_top), Inches(5.4), Inches(5.3))
                slide.shapes.add_picture(chart_img, Inches(6.35), Inches(1.4), width=Inches(6.3))
            else:
                body_tb = slide.shapes.add_textbox(Inches(0.7), Inches(content_top), Inches(11.9), Inches(5.4))

            btf = body_tb.text_frame
            btf.word_wrap = True
            for b_i, b in enumerate(bullets):
                bp = btf.paragraphs[0] if b_i == 0 else btf.add_paragraph()
                bp.text = f"▪  {b}"
                bp.font.size = Pt(15 if chart_img else 16)
                bp.font.color.rgb = text_light
                bp.space_after = Pt(12)

            # Footer
            ftr = slide.shapes.add_textbox(Inches(0.7), Inches(6.95), Inches(11.9), Inches(0.35))
            fp = ftr.text_frame.paragraphs[0]
            fp.text = f"INSLIGHT Analytics  •  {dataset.original_filename}  •  Slide {idx + 1} of {len(slides)}"
            fp.font.size = Pt(10)
            fp.font.color.rgb = text_muted

        os.makedirs(settings.REPORT_STORAGE_DIR, exist_ok=True)
        pres_id = str(uuid.uuid4())
        file_path = os.path.join(settings.REPORT_STORAGE_DIR, f"presentation_{pres_id}.pptx")
        prs.save(file_path)

        record = Presentation(
            id=pres_id,
            user_id=user.id,
            dataset_id=dataset.id,
            title=title[:255],
            presentation_type=presentation_type[:100],
            slide_count=len(slides),
            outline_json=json.dumps(slides),
            file_path=file_path,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        logger.info(f"Generated PowerPoint '{title}' ({len(slides)} slides) for user {user.id}")
        return record
