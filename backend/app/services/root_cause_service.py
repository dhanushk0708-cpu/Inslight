import json
from typing import Dict, Any, List, Optional
import duckdb
from app.utils.formatters import format_val
from app.core.logging import logger


class RootCauseService:
    """
    Root Cause Analysis (RCA) Engine.
    Decomposes business performance shifts into dimensional contributions
    and price-volume effects, distinguishing correlation from causation.
    """

    @classmethod
    def analyze_root_cause(
        cls,
        conn: duckdb.DuckDBPyConnection,
        table_name: str,
        target_metric: Optional[str] = None,
        date_col: Optional[str] = None,
        dimension_col: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Conduct systematic investigation into metric changes across historical periods.
        """
        # 1. Discover schema columns & types
        df_cols = conn.execute(f"DESCRIBE {table_name}").df()
        col_names = list(df_cols["column_name"])
        col_types = {r["column_name"]: str(r["column_type"]).lower() for _, r in df_cols.iterrows()}

        # 2. Identify target metric column
        if not target_metric:
            for cand in ["revenue", "sales", "total_amount", "amount", "profit"]:
                match = next((c for c in col_names if c.lower() == cand), None)
                if match:
                    target_metric = match
                    break
        if not target_metric:
            # Fallback to first numeric column
            target_metric = next((c for c in col_names if any(t in col_types[c] for t in ["int", "double", "float", "decimal", "numeric"])), None)

        if not target_metric:
            return {
                "status": "unsupported",
                "message": "No numeric metric column found in dataset for root cause analysis."
            }

        # 3. Identify date column for temporal period comparison
        if not date_col:
            for cand in ["date", "order_date", "timestamp", "created_at", "month"]:
                match = next((c for c in col_names if c.lower() == cand), None)
                if match:
                    date_col = match
                    break

        # 4. Identify categorical dimensions (Region, Category, Product, Channel)
        dimension_candidates = []
        for cand in ["region", "territory", "category", "product", "sku", "channel", "department"]:
            matches = [c for c in col_names if cand in c.lower()]
            dimension_candidates.extend(matches)
        dimension_candidates = list(dict.fromkeys(dimension_candidates))

        # 5. Temporal Period Comparison (if date exists)
        periods_data = None
        has_temporal_periods = False
        if date_col:
            try:
                trend_query = f"""
                    SELECT strftime(CAST({date_col} AS DATE), '%Y-%m') AS period,
                           SUM(CAST({target_metric} AS DOUBLE)) AS total_val,
                           COUNT(*) AS transaction_count
                    FROM {table_name}
                    WHERE {date_col} IS NOT NULL
                    GROUP BY period
                    ORDER BY period ASC
                """
                df_periods = conn.execute(trend_query).df()
                if len(df_periods) >= 2:
                    has_temporal_periods = True
                    periods_data = df_periods.to_dict(orient="records")
            except Exception as e:
                logger.warning(f"Temporal grouping failed: {e}")

        # Determine Baseline vs Comparison period
        if has_temporal_periods and periods_data and len(periods_data) >= 2:
            prev_period = periods_data[-2]
            curr_period = periods_data[-1]
            period_label = f"{curr_period['period']} vs {prev_period['period']}"
            val_baseline = float(prev_period["total_val"] or 0)
            val_current = float(curr_period["total_val"] or 0)
            period_filter_curr = f"strftime(CAST({date_col} AS DATE), '%Y-%m') = '{curr_period['period']}'"
            period_filter_prev = f"strftime(CAST({date_col} AS DATE), '%Y-%m') = '{prev_period['period']}'"
        else:
            # Fallback: Split dataset into halves to compare earlier vs later records
            total_rows = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            half = total_rows // 2
            period_label = "Second Half vs First Half of Dataset"
            val_baseline = float(conn.execute(f"SELECT SUM(CAST({target_metric} AS DOUBLE)) FROM (SELECT {target_metric} FROM {table_name} LIMIT {half})").fetchone()[0] or 0)
            val_current = float(conn.execute(f"SELECT SUM(CAST({target_metric} AS DOUBLE)) FROM (SELECT {target_metric} FROM {table_name} OFFSET {half})").fetchone()[0] or 0)
            period_filter_prev = f"rowid <= {half}"
            period_filter_curr = f"rowid > {half}"

        abs_change = val_current - val_baseline
        pct_change = (abs_change / val_baseline * 100.0) if val_baseline != 0 else (100.0 if val_current > 0 else 0.0)
        direction = "decline" if abs_change < 0 else "increase"

        # 6. Decompose Contributions across Available Dimensions
        segment_contributions = []
        for dim in dimension_candidates[:3]:
            try:
                # Query performance in both periods
                dim_query = f"""
                    WITH prev AS (
                        SELECT {dim} AS segment, SUM(CAST({target_metric} AS DOUBLE)) AS prev_val
                        FROM {table_name}
                        WHERE {period_filter_prev} AND {dim} IS NOT NULL
                        GROUP BY {dim}
                    ),
                    curr AS (
                        SELECT {dim} AS segment, SUM(CAST({target_metric} AS DOUBLE)) AS curr_val
                        FROM {table_name}
                        WHERE {period_filter_curr} AND {dim} IS NOT NULL
                        GROUP BY {dim}
                    )
                    SELECT COALESCE(curr.segment, prev.segment) AS segment,
                           COALESCE(prev.prev_val, 0) AS baseline_val,
                           COALESCE(curr.curr_val, 0) AS current_val,
                           (COALESCE(curr.curr_val, 0) - COALESCE(prev.prev_val, 0)) AS delta
                    FROM curr
                    FULL OUTER JOIN prev ON curr.segment = prev.segment
                    ORDER BY ABS(COALESCE(curr.curr_val, 0) - COALESCE(prev.prev_val, 0)) DESC
                    LIMIT 8
                """
                df_dim = conn.execute(dim_query).df()
                for _, row in df_dim.iterrows():
                    delta = float(row["delta"])
                    contrib_share = round((delta / abs_change * 100.0), 1) if abs_change != 0 else 0.0
                    segment_contributions.append({
                        "dimension": dim.capitalize(),
                        "segment": str(row["segment"]),
                        "baseline_val": float(row["baseline_val"]),
                        "current_val": float(row["current_val"]),
                        "delta": delta,
                        "contribution_pct": contrib_share,
                        "formatted_delta": format_val(delta, "currency" if "revenue" in target_metric.lower() or "profit" in target_metric.lower() else "number")
                    })
            except Exception as e:
                logger.warning(f"Dimension contribution failed for {dim}: {e}")

        # Sort segments by impact
        segment_contributions.sort(key=lambda s: abs(s["delta"]), reverse=True)
        top_contributors = segment_contributions[:5]

        # 7. Price vs Volume Decomposition (if quantity and price/revenue exist)
        price_volume_decomp = None
        qty_col = next((c for c in col_names if any(q in c.lower() for q in ["quantity", "units", "volume", "order_qty"])), None)
        if qty_col and abs_change != 0:
            try:
                decomp_query = f"""
                    WITH prev AS (
                        SELECT SUM(CAST({qty_col} AS DOUBLE)) AS prev_q,
                               SUM(CAST({target_metric} AS DOUBLE)) AS prev_rev
                        FROM {table_name} WHERE {period_filter_prev}
                    ),
                    curr AS (
                        SELECT SUM(CAST({qty_col} AS DOUBLE)) AS curr_q,
                               SUM(CAST({target_metric} AS DOUBLE)) AS curr_rev
                        FROM {table_name} WHERE {period_filter_curr}
                    )
                    SELECT prev_q, prev_rev, curr_q, curr_rev FROM prev, curr
                """
                decomp_row = conn.execute(decomp_query).fetchone()
                if decomp_row and all(v is not None for v in decomp_row):
                    p_q, p_rev, c_q, c_rev = decomp_row
                    if p_q > 0 and c_q > 0:
                        p_asp = p_rev / p_q
                        c_asp = c_rev / c_q
                        delta_q = c_q - p_q
                        delta_p = c_asp - p_asp
                        # Volume Effect = delta_q * p_asp
                        # Price Effect = delta_p * c_q
                        volume_effect = delta_q * p_asp
                        price_effect = delta_p * c_q

                        vol_share = round((volume_effect / abs_change) * 100.0, 1)
                        price_share = round((price_effect / abs_change) * 100.0, 1)

                        primary_driver = "Volume Contraction" if volume_effect < 0 and abs(volume_effect) > abs(price_effect) else (
                            "Price/Discount Erosion" if price_effect < 0 else "Balanced Shift"
                        )
                        price_volume_decomp = {
                            "volume_effect": round(volume_effect, 2),
                            "volume_effect_share_pct": vol_share,
                            "price_effect": round(price_effect, 2),
                            "price_effect_share_pct": price_share,
                            "baseline_asp": round(p_asp, 2),
                            "current_asp": round(c_asp, 2),
                            "baseline_volume": int(p_q),
                            "current_volume": int(c_q),
                            "primary_driver": primary_driver
                        }
            except Exception as e:
                logger.warning(f"Price-volume decomposition failed: {e}")

        # 8. Potential Explanations & Evidence-Backed Hypotheses
        hypotheses = []
        if top_contributors:
            lead_seg = top_contributors[0]
            hypotheses.append({
                "factor": f"Segment Concentration in {lead_seg['dimension']} '{lead_seg['segment']}'",
                "evidence": f"Contributed {abs(lead_seg['contribution_pct'])}% of the total {direction} ({lead_seg['formatted_delta']}).",
                "relationship": "Potential primary contributing factor (observed correlation with major shift).",
                "confidence": "HIGH" if abs(lead_seg['contribution_pct']) >= 40 else "MEDIUM"
            })
        if price_volume_decomp:
            hypotheses.append({
                "factor": f"Structural Driver: {price_volume_decomp['primary_driver']}",
                "evidence": f"Volume shift accounted for {price_volume_decomp['volume_effect_share_pct']}% of change, while ASP shift accounted for {price_volume_decomp['price_effect_share_pct']}%.",
                "relationship": "Underlying mathematical driver of aggregate revenue shift.",
                "confidence": "HIGH"
            })
        if not hypotheses:
            hypotheses.append({
                "factor": "Uniform Baseline Variance",
                "evidence": f"Metric shifted by {pct_change:.1f}% across distributed segments without single-point concentration.",
                "relationship": "Generalized macro trend across observed transaction volume.",
                "confidence": "LOW"
            })

        # 9. Recommended Investigations
        recommendations = [
            f"Review order logs and discount structures for {top_contributors[0]['dimension']} '{top_contributors[0]['segment']}'." if top_contributors else "Inspect operational transactions for baseline shifts.",
            "Verify whether seasonal replenishment cycles or localized stock-outs contributed to volume variance.",
            "Conduct elasticity checks before introducing corrective promotional markdowns."
        ]

        return {
            "status": "success",
            "metric": target_metric,
            "period_label": period_label,
            "baseline_value": val_baseline,
            "current_value": val_current,
            "absolute_change": abs_change,
            "percentage_change": round(pct_change, 2),
            "direction": direction,
            "formatted_baseline": format_val(val_baseline, "currency"),
            "formatted_current": format_val(val_current, "currency"),
            "formatted_change": format_val(abs_change, "currency"),
            "top_contributors": top_contributors,
            "price_volume_decomposition": price_volume_decomp,
            "hypotheses": hypotheses,
            "recommended_investigations": recommendations
        }
