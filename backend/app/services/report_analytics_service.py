import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import duckdb
from sqlalchemy.orm import Session
from app.models.dataset import Dataset
from app.services.dataset_service import DatasetService
from app.services.ai_service import ai_service
from app.analytics.anomaly_detection import AnomalyDetector
from app.utils.formatters import format_val
from app.core.logging import logger


class ReportAnalyticsService:
    """
    Centralized BI Analytics Engine for Executive Reports.
    Extracts verified metrics, multidimensional aggregations, trends,
    data governance checks, and senior analyst observations from DuckDB.
    """

    @classmethod
    async def analyze_dataset_for_report(
        cls,
        dataset: Dataset,
        include_anomalies: bool = True,
        report_type: str = "executive"
    ) -> Dict[str, Any]:
        """
        Orchestrate comprehensive analytics across all available dimensions and measures.
        """
        conn = DatasetService.get_duckdb_connection(dataset.storage_path, read_only=True)
        try:
            df_cols = conn.execute(f"DESCRIBE {dataset.table_name}").df()
            col_names = list(df_cols["column_name"])
            col_types = {row["column_name"]: str(row["column_type"]).lower() for _, row in df_cols.iterrows()}

            # 1. Semantic Column Mapping
            dimensions = cls._detect_dimensions(col_names, col_types)
            measures = cls._detect_measures(col_names, col_types)

            # 2. Executive KPIs Calculation
            kpis = cls._compute_kpis(conn, dataset.table_name, measures, dimensions)

            # 3. Monthly / Period Trends
            trends = cls._compute_trends(conn, dataset.table_name, dimensions.get("date"), measures)

            # 4. Regional Breakdown
            regional = cls._compute_group_breakdown(
                conn, dataset.table_name, dimensions.get("region"), measures, limit=10
            )

            # 5. Product Performance (Top & Bottom)
            products_top, products_bottom = cls._compute_product_performance(
                conn, dataset.table_name, dimensions.get("product"), measures
            )

            # 6. Category Analysis
            categories = cls._compute_group_breakdown(
                conn, dataset.table_name, dimensions.get("category"), measures, limit=8
            )

            # 7. Customer / Salesperson Breakdown
            salesperson_data = cls._compute_group_breakdown(
                conn, dataset.table_name, dimensions.get("salesperson") or dimensions.get("customer"), measures, limit=10
            )

            # 8. Financial & Profitability Margins
            financials = cls._compute_financial_ratios(kpis, categories, regional)

            # 9. Growth & Period Comparisons
            growth = cls._compute_growth_metrics(trends)

            # 10. Data Quality & Coverage Audit
            quality = cls._audit_data_quality(conn, dataset.table_name, col_names, dimensions.get("date"))

            # 11. Statistical & Operational Anomalies
            anomalies_list = []
            if include_anomalies:
                try:
                    anom_res = await AnomalyDetector.detect(dataset)
                    anomalies_list = anom_res.get("anomalies", [])
                except Exception as e:
                    logger.warning(f"Anomaly extraction warning in report analytics: {e}")

            structured_anomalies = cls._structure_anomalies(anomalies_list, kpis, measures)

            # 12. Senior Analyst Insights (Data-Grounded)
            analyst_insights = cls._generate_analyst_insights(
                kpis, trends, regional, categories, products_top, growth, structured_anomalies
            )

            # 13. Strategic Recommendations
            recommendations = cls._generate_recommendations(analyst_insights, kpis, financials, growth)

            # 14. Executive Summary Narrative (Data-grounded LLM synthesis)
            summary_narrative = await cls._synthesize_executive_summary(
                dataset_name=dataset.original_filename,
                kpis=kpis,
                trends=trends,
                growth=growth,
                regional=regional,
                categories=categories,
                insights=analyst_insights
            )

            # 15. Metric Definitions & Appendix
            metric_definitions = cls._build_metric_definitions(measures, dimensions)

            return {
                "dataset_name": dataset.original_filename,
                "table_name": dataset.table_name,
                "row_count": dataset.row_count,
                "column_count": len(col_names),
                "columns": col_names,
                "dimensions": dimensions,
                "measures": measures,
                "report_type": report_type,
                "generated_at": datetime.now(timezone.utc),
                "kpis": kpis,
                "trends": trends,
                "regional": regional,
                "products_top": products_top,
                "products_bottom": products_bottom,
                "categories": categories,
                "salesperson_data": salesperson_data,
                "financials": financials,
                "growth": growth,
                "data_quality": quality,
                "anomalies": structured_anomalies,
                "analyst_insights": analyst_insights,
                "recommendations": recommendations,
                "executive_narrative": summary_narrative,
                "metric_definitions": metric_definitions
            }

        finally:
            conn.close()

    # ━━━━━━━━ HELPERS: DIMENSION & MEASURE DETECTION ━━━━━━━━

    @staticmethod
    def _detect_dimensions(cols: List[str], types: Dict[str, str]) -> Dict[str, Optional[str]]:
        dims = {"date": None, "region": None, "product": None, "category": None, "salesperson": None, "customer": None}
        for c in cols:
            cl = c.lower()
            if not dims["date"] and any(k in cl for k in ["date", "timestamp", "created_at", "time", "order_date"]):
                dims["date"] = c
            elif not dims["region"] and any(k in cl for k in ["region", "state", "country", "territory", "zone", "city", "location"]):
                dims["region"] = c
            elif not dims["category"] and any(k in cl for k in ["category", "product_category", "department", "segment", "type"]):
                dims["category"] = c
            elif not dims["product"] and any(k in cl for k in ["product_name", "product", "item", "sku", "product_id"]) and "category" not in cl:
                dims["product"] = c
            elif not dims["salesperson"] and any(k in cl for k in ["salesperson", "rep", "agent", "seller", "employee"]):
                dims["salesperson"] = c
            elif not dims["customer"] and any(k in cl for k in ["customer", "client", "buyer", "account"]):
                dims["customer"] = c
        return dims

    @staticmethod
    def _detect_measures(cols: List[str], types: Dict[str, str]) -> Dict[str, Optional[str]]:
        meas = {"revenue": None, "cost": None, "profit": None, "quantity": None, "price": None, "discount": None}
        for c in cols:
            cl = c.lower()
            if not meas["revenue"] and any(k in cl for k in ["total_revenue", "revenue", "sales", "order_value", "amount"]):
                meas["revenue"] = c
            elif not meas["cost"] and any(k in cl for k in ["total_cost", "cost", "cogs", "expense"]):
                meas["cost"] = c
            elif not meas["profit"] and any(k in cl for k in ["gross_profit", "net_profit", "profit", "margin_val"]):
                meas["profit"] = c
            elif not meas["quantity"] and any(k in cl for k in ["units_sold", "quantity", "units", "qty", "volume"]):
                meas["quantity"] = c
            elif not meas["price"] and any(k in cl for k in ["unit_price", "price", "rate"]):
                meas["price"] = c
            elif not meas["discount"] and any(k in cl for k in ["discount", "discount_amount"]):
                meas["discount"] = c
        return meas

    # ━━━━━━━━ HELPERS: KPIS & TRENDS ━━━━━━━━

    @classmethod
    def _compute_kpis(
        cls, conn: duckdb.DuckDBPyConnection, table: str, meas: Dict[str, Optional[str]], dims: Dict[str, Optional[str]]
    ) -> Dict[str, Any]:
        """Compute verified business KPIs with safe mathematical operations."""
        row_count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] or 0
        rev_col = meas.get("revenue")
        cost_col = meas.get("cost")
        profit_col = meas.get("profit")
        qty_col = meas.get("quantity")
        price_col = meas.get("price")

        # Revenue
        total_rev = 0.0
        if rev_col:
            res = conn.execute(f"SELECT SUM({rev_col}), AVG({rev_col}) FROM {table}").fetchone()
            total_rev = float(res[0] or 0.0)

        # Cost
        total_cost = 0.0
        if cost_col:
            res = conn.execute(f"SELECT SUM({cost_col}) FROM {table}").fetchone()
            total_cost = float(res[0] or 0.0)

        # Profit
        total_profit = 0.0
        has_profit = False
        if profit_col:
            res = conn.execute(f"SELECT SUM({profit_col}) FROM {table}").fetchone()
            total_profit = float(res[0] or 0.0)
            has_profit = True
        elif rev_col and cost_col:
            total_profit = total_rev - total_cost
            has_profit = True

        # Gross Margin %
        gross_margin_pct = (total_profit / total_rev * 100.0) if (has_profit and total_rev > 0) else None

        # Units Sold
        total_units = 0.0
        if qty_col:
            res = conn.execute(f"SELECT SUM({qty_col}) FROM {table}").fetchone()
            total_units = float(res[0] or 0.0)

        # Average Order Value (AOV)
        aov = (total_rev / row_count) if (total_rev > 0 and row_count > 0) else None

        # Average Selling Price (ASP)
        asp = (total_rev / total_units) if (total_rev > 0 and total_units > 0) else None

        # Structure KPI Cards for Executive Presentation
        cards = []
        if rev_col:
            cards.append({
                "label": "Total Revenue",
                "value": total_rev,
                "formatted": format_val(total_rev, "currency"),
                "desc": "Aggregated top-line transaction value",
                "status": "primary"
            })
        if total_units > 0:
            cards.append({
                "label": "Total Volume Sold",
                "value": total_units,
                "formatted": f"{total_units:,.0f} Units",
                "desc": f"Across {row_count:,} recorded orders",
                "status": "neutral"
            })
        if has_profit:
            cards.append({
                "label": "Gross Profit",
                "value": total_profit,
                "formatted": format_val(total_profit, "currency"),
                "desc": "Total margin retained after direct costs",
                "status": "success"
            })
        if gross_margin_pct is not None:
            cards.append({
                "label": "Gross Profit Margin",
                "value": gross_margin_pct,
                "formatted": f"{gross_margin_pct:.1f}%",
                "desc": "Operating efficiency ratio (Profit / Revenue)",
                "status": "success" if gross_margin_pct >= 30 else "warning"
            })
        if aov:
            cards.append({
                "label": "Avg Transaction Value",
                "value": aov,
                "formatted": format_val(aov, "currency"),
                "desc": "Mean ticket size per transaction",
                "status": "neutral"
            })
        if asp:
            cards.append({
                "label": "Avg Selling Price (ASP)",
                "value": asp,
                "formatted": format_val(asp, "currency"),
                "desc": "Blended price realized per unit",
                "status": "neutral"
            })

        return {
            "total_revenue": total_rev,
            "total_cost": total_cost,
            "total_profit": total_profit,
            "gross_margin_pct": gross_margin_pct,
            "total_units": total_units,
            "total_orders": row_count,
            "aov": aov,
            "asp": asp,
            "cards": cards
        }

    @classmethod
    def _compute_trends(
        cls, conn: duckdb.DuckDBPyConnection, table: str, date_col: Optional[str], meas: Dict[str, Optional[str]]
    ) -> Dict[str, Any]:
        """Aggregate monthly revenue, profit, and volume trends over time."""
        if not date_col:
            return {"available": False, "records": [], "peak_month": None, "trough_month": None}

        rev_col = meas.get("revenue")
        profit_col = meas.get("profit")
        qty_col = meas.get("quantity")

        rev_expr = f"SUM({rev_col})" if rev_col else "0"
        profit_expr = f"SUM({profit_col})" if profit_col else "0"
        qty_expr = f"SUM({qty_col})" if qty_col else "0"

        query = f"""
            SELECT
                strftime(TRY_CAST({date_col} AS DATE), '%Y-%m') AS month,
                {rev_expr} AS revenue,
                {profit_expr} AS profit,
                {qty_expr} AS units,
                COUNT(*) AS order_count
            FROM {table}
            WHERE TRY_CAST({date_col} AS DATE) IS NOT NULL
            GROUP BY month
            ORDER BY month ASC
        """
        try:
            df = conn.execute(query).df()
            if df.empty or df["month"].isna().all():
                return {"available": False, "records": [], "peak_month": None, "trough_month": None}

            records = []
            prev_rev = None
            peak_val = -1.0
            peak_month = None
            trough_val = float("inf")
            trough_month = None

            for _, r in df.iterrows():
                m_rev = float(r["revenue"] or 0)
                m_prof = float(r["profit"] or 0)
                m_units = float(r["units"] or 0)
                m_orders = int(r["order_count"] or 0)

                # MoM growth
                mom_pct = None
                if prev_rev is not None and prev_rev > 0:
                    mom_pct = round(((m_rev - prev_rev) / prev_rev) * 100.0, 1)
                prev_rev = m_rev

                if m_rev > peak_val:
                    peak_val = m_rev
                    peak_month = str(r["month"])
                if m_rev < trough_val:
                    trough_val = m_rev
                    trough_month = str(r["month"])

                records.append({
                    "month": str(r["month"]),
                    "revenue": m_rev,
                    "profit": m_prof,
                    "units": m_units,
                    "orders": m_orders,
                    "mom_growth_pct": mom_pct,
                    "margin_pct": round((m_prof / m_rev * 100.0), 1) if (m_rev > 0 and m_prof > 0) else 0.0
                })

            return {
                "available": True,
                "records": records,
                "date_column": date_col,
                "start_month": records[0]["month"] if records else None,
                "end_month": records[-1]["month"] if records else None,
                "period_months": len(records),
                "peak_month": peak_month,
                "peak_revenue": peak_val,
                "trough_month": trough_month,
                "trough_revenue": trough_val
            }
        except Exception as e:
            logger.warning(f"Trend computation failed: {e}")
            return {"available": False, "records": [], "peak_month": None, "trough_month": None}

    # ━━━━━━━━ HELPERS: GROUP BREAKDOWNS ━━━━━━━━

    @classmethod
    def _compute_group_breakdown(
        cls, conn: duckdb.DuckDBPyConnection, table: str, group_col: Optional[str], meas: Dict[str, Optional[str]], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Compute aggregated metrics grouped by dimension (e.g. region, category)."""
        if not group_col:
            return []

        rev_col = meas.get("revenue")
        profit_col = meas.get("profit")
        qty_col = meas.get("quantity")

        rev_expr = f"SUM({rev_col})" if rev_col else "0"
        profit_expr = f"SUM({profit_col})" if profit_col else "0"
        qty_expr = f"SUM({qty_col})" if qty_col else "0"

        query = f"""
            SELECT
                {group_col} AS group_name,
                {rev_expr} AS revenue,
                {profit_expr} AS profit,
                {qty_expr} AS units,
                COUNT(*) AS order_count
            FROM {table}
            WHERE {group_col} IS NOT NULL
            GROUP BY {group_col}
            ORDER BY revenue DESC
            LIMIT {limit}
        """
        try:
            df = conn.execute(query).df()
            total_rev = df["revenue"].sum() if not df.empty else 0.0

            results = []
            for _, r in df.iterrows():
                rev = float(r["revenue"] or 0)
                prof = float(r["profit"] or 0)
                units = float(r["units"] or 0)
                share = (rev / total_rev * 100.0) if total_rev > 0 else 0.0
                margin = (prof / rev * 100.0) if rev > 0 else 0.0

                results.append({
                    "name": str(r["group_name"]),
                    "revenue": rev,
                    "profit": prof,
                    "units": units,
                    "orders": int(r["order_count"] or 0),
                    "revenue_share_pct": round(share, 1),
                    "margin_pct": round(margin, 1)
                })
            return results
        except Exception as e:
            logger.warning(f"Group breakdown failed for {group_col}: {e}")
            return []

    @classmethod
    def _compute_product_performance(
        cls, conn: duckdb.DuckDBPyConnection, table: str, prod_col: Optional[str], meas: Dict[str, Optional[str]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Compute top 10 and bottom 5 performing products by revenue."""
        if not prod_col:
            return [], []

        rev_col = meas.get("revenue")
        profit_col = meas.get("profit")
        qty_col = meas.get("quantity")

        rev_expr = f"SUM({rev_col})" if rev_col else "0"
        profit_expr = f"SUM({profit_col})" if profit_col else "0"
        qty_expr = f"SUM({qty_col})" if qty_col else "0"

        query = f"""
            SELECT
                {prod_col} AS product_name,
                {rev_expr} AS revenue,
                {profit_expr} AS profit,
                {qty_expr} AS units,
                COUNT(*) AS order_count
            FROM {table}
            WHERE {prod_col} IS NOT NULL
            GROUP BY {prod_col}
            ORDER BY revenue DESC
        """
        try:
            df = conn.execute(query).df()
            total_rev = df["revenue"].sum() if not df.empty else 0.0

            all_prods = []
            for _, r in df.iterrows():
                rev = float(r["revenue"] or 0)
                prof = float(r["profit"] or 0)
                units = float(r["units"] or 0)
                all_prods.append({
                    "name": str(r["product_name"]),
                    "revenue": rev,
                    "profit": prof,
                    "units": units,
                    "revenue_share_pct": round((rev / total_rev * 100.0), 1) if total_rev > 0 else 0.0,
                    "margin_pct": round((prof / rev * 100.0), 1) if rev > 0 else 0.0
                })

            top_10 = all_prods[:10]
            bottom_5 = all_prods[-5:] if len(all_prods) > 10 else []
            return top_10, bottom_5
        except Exception as e:
            logger.warning(f"Product performance failed: {e}")
            return [], []

    # ━━━━━━━━ HELPERS: FINANCIAL RATIOS & GROWTH ━━━━━━━━

    @classmethod
    def _compute_financial_ratios(
        cls, kpis: Dict[str, Any], categories: List[Dict[str, Any]], regional: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        rev = kpis.get("total_revenue", 0.0)
        cost = kpis.get("total_cost", 0.0)
        profit = kpis.get("total_profit", 0.0)

        cost_to_rev = round((cost / rev * 100.0), 1) if (rev > 0 and cost > 0) else None
        gross_margin = kpis.get("gross_margin_pct")

        # Highest margin category and region
        best_cat_margin = max(categories, key=lambda x: x["margin_pct"]) if categories else None
        best_reg_margin = max(regional, key=lambda x: x["margin_pct"]) if regional else None

        return {
            "revenue": rev,
            "cost": cost,
            "gross_profit": profit,
            "gross_margin_pct": gross_margin,
            "cost_to_revenue_ratio": cost_to_rev,
            "best_margin_category": best_cat_margin["name"] if best_cat_margin else None,
            "best_margin_region": best_reg_margin["name"] if best_reg_margin else None
        }

    @classmethod
    def _compute_growth_metrics(cls, trends: Dict[str, Any]) -> Dict[str, Any]:
        if not trends.get("available") or len(trends.get("records", [])) < 2:
            return {"available": False, "mom_average": None, "first_month": None, "last_month": None}

        records = trends["records"]
        first_m = records[0]
        last_m = records[-1]

        mom_vals = [r["mom_growth_pct"] for r in records if r.get("mom_growth_pct") is not None]
        avg_mom = round(sum(mom_vals) / len(mom_vals), 1) if mom_vals else 0.0

        period_growth_pct = None
        if first_m["revenue"] > 0:
            period_growth_pct = round(((last_m["revenue"] - first_m["revenue"]) / first_m["revenue"]) * 100.0, 1)

        return {
            "available": True,
            "first_month": first_m["month"],
            "first_month_revenue": first_m["revenue"],
            "last_month": last_m["month"],
            "last_month_revenue": last_m["revenue"],
            "period_growth_pct": period_growth_pct,
            "average_mom_growth": avg_mom
        }

    # ━━━━━━━━ HELPERS: DATA QUALITY AUDIT ━━━━━━━━

    @classmethod
    def _audit_data_quality(
        cls, conn: duckdb.DuckDBPyConnection, table: str, cols: List[str], date_col: Optional[str]
    ) -> Dict[str, Any]:
        """Audit dataset health: missing values, duplicates, date coverage, completeness."""
        total_rows = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] or 0

        # Null checks per column
        null_counts = {}
        for c in cols:
            cnt = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {c} IS NULL").fetchone()[0] or 0
            if cnt > 0:
                null_counts[c] = cnt

        # Duplicates check (if rows > 0)
        cols_joined = ", ".join(cols)
        dup_query = f"SELECT COUNT(*) - COUNT(DISTINCT {cols[0]}) FROM {table}" if len(cols) == 1 else f"SELECT COUNT(*) - COUNT(*) FROM (SELECT DISTINCT * FROM {table})"
        try:
            dup_count = conn.execute(f"SELECT COUNT(*) FROM (SELECT {cols_joined}, COUNT(*) as c FROM {table} GROUP BY {cols_joined} HAVING c > 1)").fetchone()[0] or 0
        except Exception:
            dup_count = 0

        # Date range
        date_range_str = "No temporal timestamp"
        if date_col:
            try:
                min_max = conn.execute(f"SELECT MIN({date_col}), MAX({date_col}) FROM {table}").fetchone()
                if min_max and min_max[0] and min_max[1]:
                    date_range_str = f"{min_max[0]} to {min_max[1]}"
            except Exception:
                pass

        total_cells = total_rows * len(cols) if total_rows > 0 else 1
        total_nulls = sum(null_counts.values())
        completeness_score = round(max(0.0, min(100.0, ((total_cells - total_nulls) / total_cells) * 100.0)), 1)

        return {
            "total_rows": total_rows,
            "total_columns": len(cols),
            "completeness_score": completeness_score,
            "null_counts": null_counts,
            "duplicate_count": dup_count,
            "date_range": date_range_str,
            "limitations": [
                f"Dataset comprises {total_rows:,} historical snapshots bounded to {date_range_str}.",
                f"Completeness is evaluated at {completeness_score}%; statistical aggregations assume consistent sample integrity."
            ]
        }

    # ━━━━━━━━ HELPERS: ANOMALIES & INSIGHTS ━━━━━━━━

    @classmethod
    def _structure_anomalies(
        cls, anomalies_raw: List[Any], kpis: Dict[str, Any], meas: Dict[str, Optional[str]]
    ) -> List[Dict[str, Any]]:
        """Structure raw anomaly strings/dicts into business, operational, and data quality categories."""
        structured = []
        for idx, item in enumerate(anomalies_raw[:8], 1):
            if isinstance(item, dict):
                col = item.get("column", item.get("metric", "Metric"))
                val = item.get("value", 0)
                severity = item.get("severity", "medium").upper()
                desc = item.get("description", f"Statistical outlier in {col}")
                category = "Operational Outlier" if any(k in col.lower() for k in ["unit", "qty", "volume"]) else "Financial Outlier"
            else:
                s_str = str(item)
                col = s_str.split(" ")[0] if " " in s_str else "Transaction"
                val = s_str
                severity = "HIGH" if "96,000" in s_str or "unusually high" in s_str else "MEDIUM"
                desc = s_str.replace("$", "₹")
                category = "Revenue Outlier" if "revenue" in s_str.lower() else "Volume Outlier" if "unit" in s_str.lower() else "Price Outlier"

            structured.append({
                "id": idx,
                "category": category,
                "metric": col,
                "detail": desc,
                "severity": severity,
                "implication": "Verify transaction record against customer invoices and batch receipts to confirm validity."
            })
        return structured

    @classmethod
    def _generate_analyst_insights(
        cls,
        kpis: Dict[str, Any],
        trends: Dict[str, Any],
        regional: List[Dict[str, Any]],
        categories: List[Dict[str, Any]],
        top_products: List[Dict[str, Any]],
        growth: Dict[str, Any],
        anomalies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Synthesize verified 4-part data analyst insights grounded strictly in computed facts."""
        insights = []

        # 1. Product Pareto Concentration
        if top_products and kpis.get("total_revenue", 0) > 0:
            top_3_rev = sum(p["revenue"] for p in top_products[:3])
            top_3_share = round((top_3_rev / kpis["total_revenue"]) * 100.0, 1)
            insights.append({
                "title": "Revenue Concentration in Flagship SKUs",
                "finding": f"The top 3 products account for {top_3_share}% of total gross revenue ({format_val(top_3_rev, 'currency')}).",
                "evidence": f"Top performers: {', '.join(p['name'] for p in top_products[:3])}.",
                "significance": "High concentration creates vulnerability if key product lines face supply chain disruptions or competitive pressure.",
                "action": "Diversify catalog promotions to elevate mid-tier product velocity while defending flagship margins."
            })

        # 2. Regional Dominance
        if regional and len(regional) > 1 and kpis.get("total_revenue", 0) > 0:
            lead_reg = regional[0]
            weak_reg = regional[-1]
            insights.append({
                "title": "Geographic Sales Asymmetry",
                "finding": f"{lead_reg['name']} region generates {lead_reg['revenue_share_pct']}% of total revenue, outperforming {weak_reg['name']} ({weak_reg['revenue_share_pct']}%).",
                "evidence": f"{lead_reg['name']} achieved {format_val(lead_reg['revenue'], 'currency')} vs {weak_reg['name']} at {format_val(weak_reg['revenue'], 'currency')}.",
                "significance": "Underperformance in trailing regions indicates either marketing deficiency, lower distribution penetration, or regional brand preference.",
                "action": "Audit logistics costs and localized marketing budgets in trailing territories to assess ROI expansion potential."
            })

        # 3. Category Margin Differential
        if categories and len(categories) > 1:
            cat_by_margin = sorted(categories, key=lambda x: x["margin_pct"], reverse=True)
            high_m = cat_by_margin[0]
            low_m = cat_by_margin[-1]
            insights.append({
                "title": "Category Profitability Disparity",
                "finding": f"{high_m['name']} yields the highest margin ({high_m['margin_pct']}%), while {low_m['name']} yields {low_m['margin_pct']}%.",
                "evidence": f"{high_m['name']} generated {format_val(high_m['profit'], 'currency')} margin on {format_val(high_m['revenue'], 'currency')} revenue.",
                "significance": "Focusing volume growth in lower-margin segments increases operating overhead without generating proportional retained earnings.",
                "action": "Implement minimum basket thresholds and bundle low-margin items with high-margin accessories."
            })

        # 4. Seasonal or Monthly Volatility
        if trends.get("available") and trends.get("peak_month"):
            insights.append({
                "title": "Temporal Demand Volatility",
                "finding": f"Revenue peaked in {trends['peak_month']} at {format_val(trends['peak_revenue'], 'currency')}, contrasting with the period trough in {trends['trough_month']} ({format_val(trends['trough_revenue'], 'currency')}).",
                "evidence": f"Peak-to-trough swing represents a difference of {format_val(trends['peak_revenue'] - trends['trough_revenue'], 'currency')}.",
                "significance": "Sharp cyclical swings strain inventory buffer stock and working capital commitments.",
                "action": "Align vendor procurement schedules and promotional calendars with observed seasonal peak cycles."
            })

        return insights

    @classmethod
    def _generate_recommendations(
        cls, insights: List[Dict[str, Any]], kpis: Dict[str, Any], financials: Dict[str, Any], growth: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Construct prioritized management recommendations."""
        margin_val = kpis.get("gross_margin_pct")
        margin_str = f"{margin_val:.1f}%" if margin_val is not None else "N/A"
        evidence_margin = (
            f"Blended gross margin stands at {margin_str}, with high-margin categories yielding up to {financials.get('best_margin_category', 'top tier')}."
            if margin_val is not None
            else "Profit metrics are not captured in the current schema; baseline margin audit recommended."
        )
        return [
            {
                "priority": "HIGH",
                "area": "Pricing & Margin Optimization",
                "issue": "Category margin variance and potential revenue leakage in discount-heavy products.",
                "evidence": evidence_margin,
                "action": "Review pricing tiers on top-selling volume products; conduct elasticity test with a 2-3% price adjustment.",
                "expected_impact": "Direct enhancement to retained operating profit without volume erosion."
            },
            {
                "priority": "MEDIUM",
                "area": "Regional Channel Expansion",
                "issue": "Disproportionate revenue dependence on lead regional hubs.",
                "evidence": "Top performing region contributes significantly higher revenue than trailing regional territories.",
                "action": "Reallocate digital acquisition spend and local distributor incentives toward underdeveloped regions.",
                "expected_impact": "Broadened revenue diversification and diminished single-region revenue vulnerability."
            },
            {
                "priority": "LOW",
                "area": "Operational Inventory & Demand Planning",
                "issue": "Cyclical peak-to-trough order fluctuations across months.",
                "evidence": "Observed historical seasonality swings across recorded order months.",
                "action": "Establish dynamic safety-stock buffers 45 days prior to historical peak operating months.",
                "expected_impact": "Minimized stock-outs during high-demand surges and reduced carrying costs during troughs."
            }
        ]

    @classmethod
    async def _synthesize_executive_summary(
        cls,
        dataset_name: str,
        kpis: Dict[str, Any],
        trends: Dict[str, Any],
        growth: Dict[str, Any],
        regional: List[Dict[str, Any]],
        categories: List[Dict[str, Any]],
        insights: List[Dict[str, Any]]
    ) -> str:
        """Ground LLM narrative prompt with verified metrics to prevent hallucination."""
        rev_str = format_val(kpis.get("total_revenue", 0), "currency")
        prof_str = format_val(kpis.get("total_profit", 0), "currency")
        margin_val = kpis.get("gross_margin_pct")
        margin_str = f"{margin_val:.1f}%" if margin_val is not None else "N/A"
        orders_val = kpis.get("total_orders")
        orders_str = f"{orders_val:,}" if orders_val is not None else "N/A"
        units_val = kpis.get("total_units")
        units_str = f"{units_val:,.0f}" if units_val is not None else "N/A"

        top_reg = regional[0]["name"] if regional else "Primary"
        top_reg_share = f"{regional[0]['revenue_share_pct']}%" if regional else "N/A"
        top_cat = categories[0]["name"] if categories else "Leading"
        top_cat_share = f"{categories[0]['revenue_share_pct']}%" if categories else "N/A"

        facts = (
            f"Dataset: {dataset_name}\n"
            f"Total Orders: {orders_str}, Total Units: {units_str}\n"
            f"Total Revenue: {rev_str}, Gross Profit: {prof_str}, Margin: {margin_str}\n"
            f"Lead Region: {top_reg} ({top_reg_share} of revenue)\n"
            f"Lead Category: {top_cat} ({top_cat_share} of revenue)\n"
            f"Peak Month: {trends.get('peak_month', 'N/A')}\n"
        )

        prompt = f"""You are a Principal Business Intelligence Consultant.
Write a 3-paragraph executive performance summary for the CEO/CFO based STRICTLY on these verified facts:
{facts}

Guidelines:
1. Paragraph 1: High-level financial performance, total revenue, units sold, and overall profitability.
2. Paragraph 2: Core drivers, regional leaders, and category contributions.
3. Paragraph 3: Strategic implications and high-priority forward outlook.
4. Express ALL amounts in Indian Rupees (₹, Lakhs, Crores). Never use US dollars ($).
5. DO NOT invent numbers or metrics not present in the verified facts.
6. Professional, boardroom-ready consulting tone."""

        try:
            summary = await ai_service.chat("You write executive corporate BI reports.", prompt, temp=0.1, max_tokens=600)
            return summary.replace("$", "₹").strip()
        except Exception as e:
            logger.warning(f"LLM summary synthesis error: {e}")
            return (
                f"During the audited period, total business revenue reached {rev_str} across {orders_str} recorded orders "
                f"and {units_str} total units sold. Operations delivered a gross profit of {prof_str}, representing a healthy "
                f"gross profit margin of {margin_str}. Business performance was primarily anchored by the {top_reg} territory "
                f"({top_reg_share} contribution) and the {top_cat} category ({top_cat_share} contribution). "
                f"Management should maintain vigilance on top-tier SKU dependency while scaling distribution into emerging territories."
            )

    @staticmethod
    def _build_metric_definitions(meas: Dict[str, Optional[str]], dims: Dict[str, Optional[str]]) -> List[Dict[str, str]]:
        defs = [
            {"metric": "Total Revenue", "definition": "Sum of all realized sales order transaction values before returns and taxes."},
            {"metric": "Gross Profit", "definition": "Direct revenue minus direct cost of goods sold (COGS)."},
            {"metric": "Gross Profit Margin", "definition": "Ratio of gross profit to revenue, expressed as a percentage: (Profit / Revenue) × 100."},
            {"metric": "Average Order Value (AOV)", "definition": "Mean monetary turnover generated per discrete order record."},
            {"metric": "Average Selling Price (ASP)", "definition": "Mean price realized per physical unit: Total Revenue / Total Units Sold."},
            {"metric": "MoM Growth %", "definition": "Month-over-month relative percentage change in monthly revenue volume."},
            {"metric": "Statistical Outlier (>2σ)", "definition": "Observations exceeding two standard deviations from the dataset column mean."}
        ]
        return defs
