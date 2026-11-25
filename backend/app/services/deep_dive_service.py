import json
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple
import duckdb
import pandas as pd

from app.core.logging import logger
from app.models.dataset import Dataset
from app.services.advanced_anomaly_service import AdvancedAnomalyService
from app.services.ai_service import ai_service
from app.services.data_quality_service import DataQualityService
from app.services.dataset_service import DatasetService
from app.services.forecasting_service import ForecastingService
from app.services.strategic_analysis_service import StrategicAnalysisService

# Bounded dataset-specific cache: key=(user_id, dataset_id, row_count)
_DEEP_DIVE_CACHE: OrderedDict[Tuple[str, str, int], Dict[str, Any]] = OrderedDict()
_MAX_CACHE_ENTRIES = 32


def _fmt_inr(val: float) -> str:
    if abs(val) >= 10000000:
        return f"₹{val / 10000000:.2f} Cr"
    if abs(val) >= 100000:
        return f"₹{val / 100000:.2f} Lakhs"
    return f"₹{val:,.0f}"


class DeepDiveResearchService:
    """
    Comprehensive 10-Section AI Business Intelligence Deep Dive Engine.
    1. Computes all metrics deterministically in DuckDB / Pandas / scikit-learn.
    2. Adapts dynamically to any dataset schema (never fabricates customer, profit, or inventory data).
    3. Uses LLM strictly to polish narrative explanations of verified numbers (with deterministic fallback).
    """

    @classmethod
    async def analyze_dataset(
        cls,
        dataset: Dataset,
        refresh: bool = False,
    ) -> Dict[str, Any]:
        cache_key = (dataset.user_id, dataset.id, int(dataset.row_count or 0))
        if not refresh and cache_key in _DEEP_DIVE_CACHE:
            _DEEP_DIVE_CACHE.move_to_end(cache_key)
            return _DEEP_DIVE_CACHE[cache_key]

        stages: List[str] = []
        try:
            conn = DatasetService.get_duckdb_connection(dataset.storage_path, read_only=True)
        except Exception as e:
            logger.error(f"Deep Dive DuckDB open failed: {e}")
            return {"error": "Failed to open dataset for Deep Dive analysis."}

        try:
            stages.append(f"Inspected dataset structure ({dataset.original_filename}, {dataset.row_count:,} rows)")
            cols_meta = conn.execute(f"DESCRIBE {dataset.table_name}").fetchall()
            cols = [c[0] for c in cols_meta]
            types = {c[0]: c[1] for c in cols_meta}
            total_rows = int(conn.execute(f"SELECT COUNT(*) FROM {dataset.table_name}").fetchone()[0])

            # ── 1. Schema & Capability Detection ──
            rev_col = next((c for c in cols if any(k == c.lower() for k in ["revenue", "total_revenue", "sales", "total_sales", "amount", "total_amount", "turnover"])), None)
            if not rev_col:
                rev_col = next((c for c in cols if any(k in c.lower() for k in ["rev", "sale", "amount", "price"]) and any(t in types[c].upper() for t in ["INT", "DOUBLE", "FLOAT", "DECIMAL", "NUMERIC"])), None)

            profit_col = next((c for c in cols if any(k == c.lower() for k in ["profit", "net_profit", "gross_profit", "margin_amount", "earnings"])), None)
            cost_col = next((c for c in cols if any(k == c.lower() for k in ["cost", "total_cost", "expense", "cogs"])), None)
            units_col = next((c for c in cols if any(k in c.lower() for k in ["units_sold", "unit_sold", "quantity", "qty", "volume"])), None)
            date_col = next((c for c in cols if any(k in c.lower() for k in ["date", "order_date", "transaction_date", "timestamp", "created_at", "month"])), None)
            cat_col = next((c for c in cols if any(k in c.lower() for k in ["product_category", "category", "department", "segment"])), None)
            prod_col = next((c for c in cols if any(k in c.lower() for k in ["product_name", "product", "item_name", "item", "sku"]) and c != cat_col), None)
            reg_col = next((c for c in cols if any(k in c.lower() for k in ["region", "territory", "zone", "country", "state", "city", "location"])), None)
            cust_col = next((c for c in cols if any(k in c.lower() for k in ["customer_id", "cust_id", "customer_name", "customer", "client_id", "client"])), None)
            order_col = next((c for c in cols if any(k == c.lower() for k in ["order_id", "transaction_id", "invoice_id", "basket_id", "bill_id"])), None)
            inv_col = next((c for c in cols if any(k in c.lower() for k in ["inventory", "stock_qty", "stock_value", "on_hand", "turnover"])), None)

            numeric_cols = [c for c in cols if any(t in types[c].upper() for t in ["INT", "DOUBLE", "FLOAT", "DECIMAL", "NUMERIC"])]
            categorical_cols = [c for c in cols if c not in numeric_cols and c != date_col]

            # Data quality snapshot (reuse DataQualityService)
            quality_report = DataQualityService.audit_dataset_quality(conn, dataset.table_name)
            stages.append("Identified available business metrics, dimensions, and data quality baseline")

            # Date coverage
            date_coverage = None
            if date_col:
                try:
                    d_min, d_max = conn.execute(
                        f"SELECT MIN(TRY_CAST({date_col} AS DATE)), MAX(TRY_CAST({date_col} AS DATE)) FROM {dataset.table_name}"
                    ).fetchone()
                    if d_min and d_max:
                        date_coverage = {"start": str(d_min), "end": str(d_max), "date_column": date_col}
                except Exception:
                    date_coverage = None

            limitations: List[str] = []
            if not profit_col and not cost_col:
                limitations.append("Profitability analysis unavailable: dataset contains no profit or cost columns.")
            if not cust_col:
                limitations.append("Customer intelligence unavailable: dataset contains no customer identifier column.")
            if not order_col:
                limitations.append("Order-level AOV & basket co-occurrence unavailable: no order/transaction ID column; using per-record averages.")
            if not inv_col:
                limitations.append("Inventory turnover unavailable: dataset contains no stock-on-hand or inventory columns.")

            available_analyses = [
                "Executive Overview",
                "Revenue Analysis" if rev_col else "Numeric Summary",
                *(["Profitability Analysis"] if (profit_col or cost_col) else []),
                *(["Product Intelligence"] if prod_col else []),
                *(["Category Analysis"] if cat_col else []),
                *(["Regional Intelligence"] if reg_col else []),
                *(["Customer Intelligence"] if cust_col else []),
                *(["Time & Seasonality"] if date_coverage else []),
                "Risks, Anomalies & Opportunities",
            ]

            dataset_metadata = {
                "dataset_id": dataset.id,
                "filename": dataset.original_filename,
                "row_count": total_rows,
                "column_count": len(cols),
                "columns": cols,
                "numeric_metrics": numeric_cols,
                "categorical_dimensions": categorical_cols,
                "date_coverage": date_coverage,
                "data_quality_score": quality_report.get("overall_score", 100),
                "issues_count": quality_report.get("issues_count", 0),
                "available_analyses": available_analyses,
                "limitations": limitations,
            }

            # ── 2. Executive KPIs ──
            total_revenue = float(conn.execute(f"SELECT COALESCE(SUM({rev_col}), 0) FROM {dataset.table_name}").fetchone()[0]) if rev_col else 0.0
            has_profit = bool(profit_col or (cost_col and rev_col))
            if profit_col:
                total_profit = float(conn.execute(f"SELECT COALESCE(SUM({profit_col}), 0) FROM {dataset.table_name}").fetchone()[0])
            elif cost_col and rev_col:
                total_profit = float(conn.execute(f"SELECT COALESCE(SUM({rev_col} - {cost_col}), 0) FROM {dataset.table_name}").fetchone()[0])
            else:
                total_profit = None

            gross_margin_pct = round((total_profit / total_revenue * 100), 1) if (total_profit is not None and total_revenue > 0) else None
            total_units = int(conn.execute(f"SELECT COALESCE(SUM({units_col}), 0) FROM {dataset.table_name}").fetchone()[0]) if units_col else None

            total_orders = None
            avg_order_value = None
            rev_per_record = round(total_revenue / total_rows, 2) if total_rows > 0 else 0.0
            if order_col:
                total_orders = int(conn.execute(f"SELECT COUNT(DISTINCT {order_col}) FROM {dataset.table_name}").fetchone()[0])
                avg_order_value = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0

            kpi_cards: List[Dict[str, Any]] = []
            if rev_col:
                kpi_cards.append({
                    "label": "Total Revenue",
                    "value": _fmt_inr(total_revenue),
                    "trend": f"{total_rows:,} records",
                    "trend_direction": "up",
                })
            if has_profit and total_profit is not None:
                kpi_cards.append({
                    "label": "Total Profit",
                    "value": _fmt_inr(total_profit),
                    "trend": f"{gross_margin_pct}% Margin" if gross_margin_pct is not None else None,
                    "trend_direction": "up" if (gross_margin_pct or 0) >= 30 else "neutral",
                })
            if gross_margin_pct is not None:
                kpi_cards.append({
                    "label": "Gross Margin",
                    "value": f"{gross_margin_pct}%",
                    "trend": "Healthy" if gross_margin_pct >= 35 else "Moderate",
                    "trend_direction": "up" if gross_margin_pct >= 35 else "neutral",
                })
            if total_units is not None:
                kpi_cards.append({
                    "label": "Units Sold",
                    "value": f"{total_units:,}",
                    "trend": f"Avg/Rec: {_fmt_inr(rev_per_record)}" if not avg_order_value else f"AOV: {_fmt_inr(avg_order_value)}",
                    "trend_direction": "neutral",
                })
            elif total_orders is not None:
                kpi_cards.append({
                    "label": "Total Orders",
                    "value": f"{total_orders:,}",
                    "trend": f"AOV: {_fmt_inr(avg_order_value or 0)}",
                    "trend_direction": "neutral",
                })
            else:
                kpi_cards.append({
                    "label": "Records Analyzed",
                    "value": f"{total_rows:,}",
                    "trend": f"Rev/Record: {_fmt_inr(rev_per_record)}",
                    "trend_direction": "neutral",
                })

            stages.append("Calculated executive KPIs and performance baselines")

            # ── 3. Time-Series Trends (Monthly & Quarterly) ──
            monthly_trend: List[Dict[str, Any]] = []
            monthly_growth: List[Dict[str, Any]] = []
            quarterly_trend: List[Dict[str, Any]] = []
            mom_growth_pct: Optional[float] = None
            qoq_growth_pct: Optional[float] = None
            highest_period = None
            lowest_period = None

            if date_col and rev_col:
                profit_expr = (
                    f"COALESCE(SUM({profit_col}), 0)"
                    if profit_col
                    else (f"COALESCE(SUM({rev_col} - {cost_col}), 0)" if cost_col else "0")
                )
                m_rows = conn.execute(f"""
                    SELECT strftime(TRY_CAST({date_col} AS DATE), '%Y-%m') AS month,
                           COALESCE(SUM({rev_col}), 0) AS total_revenue,
                           {profit_expr} AS total_profit,
                           {'COALESCE(SUM(' + units_col + '), 0)' if units_col else 'COUNT(*)'} AS units
                    FROM {dataset.table_name}
                    WHERE TRY_CAST({date_col} AS DATE) IS NOT NULL
                    GROUP BY 1
                    ORDER BY 1 ASC
                """).fetchall()
                for r in m_rows:
                    rev_v = float(r[1])
                    prof_v = float(r[2]) if has_profit else None
                    monthly_trend.append({
                        "month": str(r[0]),
                        "total_revenue": rev_v,
                        "total_profit": prof_v if prof_v is not None else 0.0,
                        "margin_pct": round((prof_v / rev_v * 100), 1) if (prof_v is not None and rev_v > 0) else None,
                        "units": int(r[3]),
                    })

                if len(monthly_trend) >= 2:
                    for idx in range(1, len(monthly_trend)):
                        prev_r = monthly_trend[idx - 1]["total_revenue"]
                        curr_r = monthly_trend[idx]["total_revenue"]
                        g_pct = round(((curr_r - prev_r) / prev_r * 100), 1) if prev_r > 0 else 0.0
                        monthly_growth.append({
                            "month": monthly_trend[idx]["month"],
                            "growth_pct": g_pct,
                            "revenue": curr_r,
                        })
                    mom_growth_pct = monthly_growth[-1]["growth_pct"]

                if monthly_trend:
                    highest_period = max(monthly_trend, key=lambda x: x["total_revenue"])
                    lowest_period = min(monthly_trend, key=lambda x: x["total_revenue"])

                q_rows = conn.execute(f"""
                    SELECT CONCAT(strftime(TRY_CAST({date_col} AS DATE), '%Y'), '-Q', CAST(EXTRACT(QUARTER FROM TRY_CAST({date_col} AS DATE)) AS VARCHAR)) AS quarter,
                           COALESCE(SUM({rev_col}), 0) AS total_revenue
                    FROM {dataset.table_name}
                    WHERE TRY_CAST({date_col} AS DATE) IS NOT NULL
                    GROUP BY 1
                    ORDER BY 1 ASC
                """).fetchall()
                quarterly_trend = [{"quarter": str(r[0]), "total_revenue": float(r[1])} for r in q_rows]
                if len(quarterly_trend) >= 2 and quarterly_trend[-2]["total_revenue"] > 0:
                    qoq_growth_pct = round(
                        ((quarterly_trend[-1]["total_revenue"] - quarterly_trend[-2]["total_revenue"]) / quarterly_trend[-2]["total_revenue"] * 100),
                        1,
                    )

            # Helper to aggregate any categorical dimension cleanly
            def _agg_dim(col_name: Optional[str]) -> List[Dict[str, Any]]:
                if not col_name or not rev_col:
                    return []
                p_expr = (
                    f"COALESCE(SUM({profit_col}), 0)"
                    if profit_col
                    else (f"COALESCE(SUM({rev_col} - {cost_col}), 0)" if cost_col else "0")
                )
                u_expr = f"COALESCE(SUM({units_col}), 0)" if units_col else "COUNT(*)"
                rows = conn.execute(f"""
                    SELECT CAST({col_name} AS VARCHAR) AS name,
                           COALESCE(SUM({rev_col}), 0) AS total_revenue,
                           {p_expr} AS total_profit,
                           {u_expr} AS units
                    FROM {dataset.table_name}
                    WHERE {col_name} IS NOT NULL
                    GROUP BY 1
                    ORDER BY total_revenue DESC
                """).fetchall()
                out = []
                for r in rows:
                    rv = float(r[1])
                    pv = float(r[2]) if has_profit else None
                    out.append({
                        "name": str(r[0]),
                        "total_revenue": rv,
                        "total_profit": pv,
                        "margin_pct": round((pv / rv * 100), 1) if (pv is not None and rv > 0) else None,
                        "share_pct": round((rv / total_revenue * 100), 1) if total_revenue > 0 else 0.0,
                        "units": int(r[3]),
                    })
                return out

            by_category = _agg_dim(cat_col)
            by_product = _agg_dim(prod_col)
            by_region = _agg_dim(reg_col)

            stages.append("Analyzed revenue, profitability, category, product, and regional segments")

            # ── 4. Strategic Analysis (Opportunities, Risks, Recommendations) ──
            strat = StrategicAnalysisService.analyze_business_performance(
                conn=conn,
                table_name=dataset.table_name,
                question="Provide a comprehensive deep dive business analysis",
                dataset_name=dataset.original_filename,
            )

            # ── 5. Forecasting & Anomalies (Reuse Phase 3 Engines) ──
            forecast_res = None
            if date_col and rev_col:
                try:
                    forecast_res = ForecastingService.generate_forecast(conn, dataset.table_name, target_metric=rev_col, date_col=date_col, horizon=30)
                except Exception as fe:
                    forecast_res = {"status": "unavailable", "message": str(fe)}
            else:
                forecast_res = {"status": "unavailable", "message": "Forecasting requires valid date and revenue columns."}

            anomaly_res = AdvancedAnomalyService.detect_anomalies(conn, dataset.table_name)
            stages.append("Evaluated forecasting models, statistical anomalies, opportunities, and risks")

            # ── 6. Customer Analysis (Strict Guard: only if customer column exists) ──
            customer_analysis: Dict[str, Any]
            if cust_col and rev_col:
                cust_rows = _agg_dim(cust_col)
                customer_analysis = {
                    "available": True,
                    "unique_customers": len(cust_rows),
                    "avg_revenue_per_customer": round(total_revenue / len(cust_rows), 2) if cust_rows else 0.0,
                    "top_customers": cust_rows[:10],
                    "top_customer_concentration_pct": cust_rows[0]["share_pct"] if cust_rows else 0.0,
                }
            else:
                customer_analysis = {
                    "available": False,
                    "reason": "Dataset does not contain a customer identifier column; customer retention, churn, and LTV cannot be computed.",
                }

            # ── 7. Product & Profitability Details ──
            product_analysis: Optional[Dict[str, Any]] = None
            if by_product:
                top_prods = by_product[:7]
                bottom_prods = sorted(by_product, key=lambda x: x["total_revenue"])[:5]
                high_vol_low_rev = sorted(
                    [p for p in by_product if p["share_pct"] < 10.0],
                    key=lambda x: x["units"],
                    reverse=True,
                )[:3]
                high_rev_low_margin = [
                    p for p in by_product[:5]
                    if p["margin_pct"] is not None and gross_margin_pct is not None and p["margin_pct"] < gross_margin_pct
                ]
                product_analysis = {
                    "available": True,
                    "total_products": len(by_product),
                    "top_products": top_prods,
                    "bottom_products": bottom_prods,
                    "top_product_concentration_pct": by_product[0]["share_pct"],
                    "high_volume_low_revenue": high_vol_low_rev,
                    "high_revenue_below_avg_margin": high_rev_low_margin,
                    "inventory_note": None if inv_col else "No inventory/stock columns exist; low-revenue products reflect low sales velocity rather than stock accumulation.",
                }

            profitability_analysis: Dict[str, Any]
            if has_profit and total_profit is not None:
                neg_segments = [p for p in (by_product or by_category) if (p["total_profit"] or 0) < 0]
                profitability_analysis = {
                    "available": True,
                    "total_profit": total_profit,
                    "gross_margin_pct": gross_margin_pct,
                    "by_category": by_category,
                    "by_product": by_product[:10],
                    "by_region": by_region,
                    "highest_margin_products": sorted([p for p in by_product if p["margin_pct"] is not None], key=lambda x: x["margin_pct"], reverse=True)[:5],
                    "lowest_margin_products": sorted([p for p in by_product if p["margin_pct"] is not None], key=lambda x: x["margin_pct"])[:5],
                    "negative_profit_segments": neg_segments,
                }
            else:
                profitability_analysis = {
                    "available": False,
                    "reason": "Dataset lacks cost or profit columns; profitability cannot be inferred from revenue alone.",
                }

            # ── 8. Build Dynamic Charts Dictionary (only supported charts!) ──
            charts: Dict[str, Any] = {}
            if monthly_trend:
                charts["revenue_trend"] = {
                    "type": "line",
                    "title": "Revenue Over Time",
                    "x_axis": "month",
                    "y_axis": "total_revenue",
                    "data": monthly_trend,
                    "interpretation": f"Peak revenue in {highest_period['month']} ({_fmt_inr(highest_period['total_revenue'])}); lowest in {lowest_period['month']} ({_fmt_inr(lowest_period['total_revenue'])})." if highest_period else "",
                }
                if has_profit:
                    charts["profit_trend"] = {
                        "type": "line",
                        "title": "Profit Over Time",
                        "x_axis": "month",
                        "y_axis": "total_profit",
                        "data": monthly_trend,
                        "interpretation": f"Blended gross margin across the timeline is {gross_margin_pct}%.",
                    }
            if monthly_growth:
                charts["monthly_growth"] = {
                    "type": "line",
                    "title": "Month-over-Month Revenue Growth (%)",
                    "x_axis": "month",
                    "y_axis": "growth_pct",
                    "data": monthly_growth,
                    "interpretation": f"Latest MoM change: {mom_growth_pct:+.1f}%." if mom_growth_pct is not None else "",
                }
            if by_category:
                charts["revenue_by_category"] = {
                    "type": "bar",
                    "title": "Revenue by Category",
                    "x_axis": "name",
                    "y_axis": "total_revenue",
                    "data": by_category,
                    "interpretation": f"{by_category[0]['name']} leads with {by_category[0]['share_pct']}% of total revenue.",
                }
                charts["revenue_share"] = {
                    "type": "pie",
                    "title": "Category Revenue Contribution",
                    "x_axis": "name",
                    "y_axis": "total_revenue",
                    "data": by_category,
                    "interpretation": "Broad-based diversification reduces single-category risk." if by_category[0]["share_pct"] < 45 else f"High concentration: {by_category[0]['name']} represents {by_category[0]['share_pct']}% of turnover.",
                }
                if has_profit:
                    charts["profit_by_category"] = {
                        "type": "bar",
                        "title": "Profit by Category",
                        "x_axis": "name",
                        "y_axis": "total_profit",
                        "data": by_category,
                        "interpretation": f"Highest category margin: {max(by_category, key=lambda x: x['margin_pct'] or 0)['name']}.",
                    }
            if by_product:
                charts["top_products"] = {
                    "type": "horizontal_bar",
                    "title": "Top Products by Revenue",
                    "x_axis": "name",
                    "y_axis": "total_revenue",
                    "data": by_product[:7],
                    "interpretation": f"Top revenue product: {by_product[0]['name']} ({_fmt_inr(by_product[0]['total_revenue'])}).",
                }
                charts["bottom_products"] = {
                    "type": "horizontal_bar",
                    "title": "Lowest Sales Velocity Products",
                    "x_axis": "name",
                    "y_axis": "total_revenue",
                    "data": sorted(by_product, key=lambda x: x["total_revenue"])[:5],
                    "interpretation": "Reflects lower unit/revenue velocity (not stock accumulation unless inventory data is present).",
                }
                if has_profit:
                    charts["product_margins"] = {
                        "type": "bar",
                        "title": "Product Gross Margin (%)",
                        "x_axis": "name",
                        "y_axis": "margin_pct",
                        "data": by_product[:8],
                        "interpretation": f"Compares top products against the {gross_margin_pct}% portfolio margin benchmark.",
                    }
                    charts["revenue_vs_profit_scatter"] = {
                        "type": "scatter",
                        "title": "Product Revenue vs. Profit",
                        "x_axis": "total_revenue",
                        "y_axis": "total_profit",
                        "data": [{"name": p["name"], "total_revenue": p["total_revenue"], "total_profit": p["total_profit"]} for p in by_product],
                        "interpretation": "Upper-left items deliver higher margin efficiency; lower-right items carry high volume with lower unit margin.",
                    }
            if by_region:
                charts["regional_performance"] = {
                    "type": "bar",
                    "title": "Regional Revenue Performance",
                    "x_axis": "name",
                    "y_axis": "total_revenue",
                    "data": by_region,
                    "interpretation": f"{by_region[0]['name']} leads ({_fmt_inr(by_region[0]['total_revenue'])}); {by_region[-1]['name']} trails ({_fmt_inr(by_region[-1]['total_revenue'])}).",
                }
            if forecast_res and forecast_res.get("status") == "success" and forecast_res.get("forecast_data"):
                charts["forecast_vs_actual"] = {
                    "type": "line",
                    "title": f"Revenue Forecast ({forecast_res.get('method_used', 'auto').replace('_', ' ').title()})",
                    "x_axis": "date",
                    "y_axis": "predicted",
                    "data": forecast_res["forecast_data"],
                    "interpretation": f"Projected 30-period total: {forecast_res.get('formatted_forecast_total')}.",
                }
            if customer_analysis.get("available") and customer_analysis.get("top_customers"):
                charts["customer_concentration"] = {
                    "type": "bar",
                    "title": "Top Customers by Revenue",
                    "x_axis": "name",
                    "y_axis": "total_revenue",
                    "data": customer_analysis["top_customers"][:8],
                    "interpretation": f"{customer_analysis['unique_customers']} unique customers identified.",
                }

            stages.append(f"Prepared {len(charts)} verified analytical visualizations")

            # ── 9. Executive Narrative Synthesis (Grounded in Computed Facts) ──
            key_findings = [
                f"Total Revenue reached {_fmt_inr(total_revenue)} across {total_rows:,} records.",
                *(
                    [f"Net Profit stands at {_fmt_inr(total_profit)} ({gross_margin_pct}% gross margin)."]
                    if has_profit and total_profit is not None
                    else ["Profitability metrics excluded because dataset lacks cost/profit columns."]
                ),
                *(
                    [f"Category '{by_category[0]['name']}' accounts for {by_category[0]['share_pct']}% of total revenue."]
                    if by_category
                    else []
                ),
                *(
                    [f"Regional spread: '{by_region[0]['name']}' leads at {_fmt_inr(by_region[0]['total_revenue'])} vs '{by_region[-1]['name']}' at {_fmt_inr(by_region[-1]['total_revenue'])}."]
                    if len(by_region) >= 2
                    else []
                ),
            ]

            deterministic_summary = " ".join(key_findings)
            try:
                ai_narrative = await ai_service.generate_text(
                    prompt=(
                        f"Write a concise 3-sentence executive business assessment strictly from these verified facts:\n"
                        f"{json.dumps(key_findings)}\n"
                        f"Top Risk: {strat['risks'][0]['title'] if strat.get('risks') else 'None'}.\n"
                        f"Top Opportunity: {strat['opportunities'][0]['title'] if strat.get('opportunities') else 'None'}.\n"
                        f"Use Indian Rupees (₹, Lakhs, Crores). Do not invent any statistics."
                    ),
                    system="You are INSLIGHT Senior Business Intelligence Analyst.",
                )
            except Exception:
                ai_narrative = deterministic_summary

            # Prioritized Action Plan
            opps = strat.get("opportunities") or []
            risks = strat.get("risks") or []
            recommendations_legacy = [
                {
                    "action": o["recommendation"],
                    "expected_impact": o["actual_value"],
                    "priority": "high" if o["rank"] == 1 else "medium",
                }
                for o in opps
            ]

            strategic_action_plan = {
                "short_term": [
                    {
                        "priority": "high",
                        "problem": risks[0]["title"] if risks else "Revenue Concentration",
                        "evidence": risks[0]["actual_value"] if risks else deterministic_summary,
                        "action": risks[0]["mitigation"] if risks else "Diversify revenue segments.",
                        "expected_direction": "Risk reduction & revenue resilience",
                        "difficulty": "Medium",
                        "metric_to_monitor": risks[0]["supporting_metric"] if risks else "Category Share %",
                    },
                    *(
                        [{
                            "priority": "high",
                            "problem": f"Under-monetized High Margin ({opps[0]['title']})",
                            "evidence": opps[0]["actual_value"],
                            "action": opps[0]["recommendation"],
                            "expected_direction": "Gross margin & net profit expansion",
                            "difficulty": "Low",
                            "metric_to_monitor": opps[0]["supporting_metric"],
                        }]
                        if opps
                        else []
                    ),
                ],
                "medium_term": [
                    {
                        "priority": "medium",
                        "problem": o["title"],
                        "evidence": o["actual_value"],
                        "action": o["recommendation"],
                        "expected_direction": "Incremental revenue growth (requires validation)" if o.get("is_hypothesis") else "Measured revenue expansion",
                        "difficulty": "Medium",
                        "metric_to_monitor": o["supporting_metric"],
                    }
                    for o in opps[1:]
                ],
            }

            result: Dict[str, Any] = {
                # Legacy DeepDiveResponse compatibility fields
                "top_revenue_drivers": [
                    {"name": d["name"], "revenue": d["total_revenue"], "trend": "up"}
                    for d in (by_category or by_product)[:5]
                ],
                "risk_areas": [
                    {"name": r["title"], "issue": r["business_interpretation"], "impact_amount": 0, "severity": r["severity"]}
                    for r in risks
                ],
                "root_cause_analysis": ai_narrative,
                "recommendations": recommendations_legacy,
                "monthly_trend": monthly_trend or None,
                "revenue_by_category": [
                    {"product_category": c["name"], "total_revenue": c["total_revenue"]}
                    for c in by_category
                ] if by_category else None,
                "error": None,

                # Comprehensive 10-Section Research Workspace Payload
                "dataset_metadata": dataset_metadata,
                "executive_summary": {
                    "health_summary": ai_narrative,
                    "kpi_cards": kpi_cards,
                    "key_findings": key_findings,
                    "warnings": limitations,
                },
                "revenue_analysis": {
                    "total_revenue": total_revenue,
                    "mom_growth_pct": mom_growth_pct,
                    "qoq_growth_pct": qoq_growth_pct,
                    "highest_period": highest_period,
                    "lowest_period": lowest_period,
                    "top_category_concentration_pct": by_category[0]["share_pct"] if by_category else None,
                    "top_product_concentration_pct": by_product[0]["share_pct"] if by_product else None,
                    "is_broad_based": (by_category[0]["share_pct"] < 45.0) if by_category else True,
                    "monthly_trend": monthly_trend,
                    "quarterly_trend": quarterly_trend,
                    "by_category": by_category,
                    "by_region": by_region,
                },
                "profitability_analysis": profitability_analysis,
                "product_analysis": product_analysis,
                "category_analysis": {
                    "available": bool(by_category),
                    "categories": by_category,
                    "concentration_risk": (by_category[0]["share_pct"] > 50.0) if by_category else False,
                },
                "regional_analysis": {
                    "available": bool(by_region),
                    "regions": by_region,
                    "leader": by_region[0] if by_region else None,
                    "trailing": by_region[-1] if len(by_region) > 1 else None,
                },
                "customer_analysis": customer_analysis,
                "trend_and_forecast": {
                    "monthly_trend": monthly_trend,
                    "monthly_growth": monthly_growth,
                    "forecast": forecast_res,
                },
                "anomalies_and_risks": {
                    "anomalies": anomaly_res,
                    "risks": risks,
                },
                "opportunities": opps,
                "strategic_action_plan": strategic_action_plan,
                "charts": charts,
                "execution_stages": stages,
            }

            _DEEP_DIVE_CACHE[cache_key] = result
            if len(_DEEP_DIVE_CACHE) > _MAX_CACHE_ENTRIES:
                _DEEP_DIVE_CACHE.popitem(last=False)

            return result
        finally:
            conn.close()
