from typing import Dict, Any, List, Optional
import duckdb
from app.utils.formatters import format_val
from app.core.logging import logger


class ComparisonService:
    """
    Comparative Business Analytics Engine.
    Executes period-over-period (MoM, QoQ, YoY) and dimension-over-dimension
    (Region vs Region, Category vs Category) evaluations with absolute difference,
    percentage change, contribution to overall variance, and safe zero-denominator handling.
    """

    @classmethod
    def compare_periods_or_segments(
        cls,
        conn: duckdb.DuckDBPyConnection,
        table_name: str,
        comparison_mode: str = "period",  # "period" or "segment"
        target_metric: Optional[str] = None,
        dimension_col: Optional[str] = None,
        segment_a: Optional[str] = None,
        segment_b: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute comparative analytics.
        """
        df_cols = conn.execute(f"DESCRIBE {table_name}").df()
        col_names = list(df_cols["column_name"])
        col_types = {r["column_name"]: str(r["column_type"]).lower() for _, r in df_cols.iterrows()}

        # 1. Discover target metric
        if not target_metric:
            for cand in ["revenue", "sales", "total_amount", "amount", "profit", "units"]:
                match = next((c for c in col_names if c.lower() == cand), None)
                if match:
                    target_metric = match
                    break
        if not target_metric:
            target_metric = next((c for c in col_names if any(t in col_types[c] for t in ["int", "double", "float", "decimal", "numeric"])), None)

        if not target_metric:
            return {
                "status": "error",
                "message": "No numeric metric found for comparative analysis."
            }

        # 2. Period Comparison (MoM / Temporal)
        if comparison_mode == "period":
            date_col = next((c for c in col_names if any(d in c.lower() for d in ["date", "timestamp", "created_at", "month"])), None)
            if not date_col:
                return {
                    "status": "unsupported",
                    "message": "Dataset lacks a date column for temporal period comparison."
                }

            try:
                trend_query = f"""
                    SELECT strftime(CAST({date_col} AS DATE), '%Y-%m') AS period,
                           SUM(CAST({target_metric} AS DOUBLE)) AS metric_val,
                           COUNT(*) AS transaction_count
                    FROM {table_name}
                    WHERE {date_col} IS NOT NULL
                    GROUP BY period
                    ORDER BY period ASC
                """
                df_periods = conn.execute(trend_query).df()
                if len(df_periods) < 2:
                    return {
                        "status": "insufficient_data",
                        "message": "Requires at least 2 distinct periods to conduct comparative analysis."
                    }

                comparison_rows: List[Dict[str, Any]] = []
                for i in range(1, len(df_periods)):
                    p_prev = str(df_periods["period"].iloc[i - 1])
                    p_curr = str(df_periods["period"].iloc[i])
                    v_prev = float(df_periods["metric_val"].iloc[i - 1] or 0)
                    v_curr = float(df_periods["metric_val"].iloc[i] or 0)

                    abs_diff = v_curr - v_prev
                    # Safe zero denominator
                    if v_prev != 0:
                        pct_diff = round((abs_diff / v_prev) * 100.0, 1)
                        pct_label = f"{'+' if pct_diff > 0 else ''}{pct_diff}%"
                    else:
                        pct_diff = 100.0 if v_curr > 0 else 0.0
                        pct_label = "+100% (New Period)" if v_curr > 0 else "0.0%"

                    comparison_rows.append({
                        "period_label": f"{p_curr} vs {p_prev}",
                        "current_period": p_curr,
                        "baseline_period": p_prev,
                        "current_value": round(v_curr, 2),
                        "baseline_value": round(v_prev, 2),
                        "absolute_difference": round(abs_diff, 2),
                        "percentage_change": pct_diff,
                        "formatted_change": pct_label,
                        "trend": "up" if abs_diff > 0 else ("down" if abs_diff < 0 else "flat")
                    })

                latest = comparison_rows[-1]
                return {
                    "status": "success",
                    "comparison_type": "Period-over-Period (MoM)",
                    "metric": target_metric,
                    "latest_comparison": latest,
                    "timeline": comparison_rows
                }
            except Exception as e:
                logger.error(f"Period comparison failed: {e}")
                return {"status": "error", "message": f"Period comparison failed: {str(e)}"}

        # 3. Segment vs Segment Comparison (e.g. North vs South, or Electronics vs Furniture)
        else:
            if not dimension_col:
                for cand in ["region", "territory", "category", "channel", "department"]:
                    match = next((c for c in col_names if cand in c.lower()), None)
                    if match:
                        dimension_col = match
                        break

            if not dimension_col:
                return {
                    "status": "unsupported",
                    "message": "No categorical dimension found for segment comparison."
                }

            try:
                seg_df = conn.execute(f"""
                    SELECT {dimension_col} AS seg,
                           SUM(CAST({target_metric} AS DOUBLE)) AS val,
                           COUNT(*) AS count
                    FROM {table_name}
                    WHERE {dimension_col} IS NOT NULL
                    GROUP BY seg
                    ORDER BY val DESC
                """).df()

                if len(seg_df) < 2:
                    return {
                        "status": "insufficient_data",
                        "message": f"Dimension '{dimension_col}' contains fewer than 2 segments to compare."
                    }

                seg_a_row = seg_df.iloc[0] if not segment_a else seg_df[seg_df["seg"] == segment_a].iloc[0]
                seg_b_row = seg_df.iloc[1] if not segment_b else seg_df[seg_df["seg"] == segment_b].iloc[0]

                name_a = str(seg_a_row["seg"])
                name_b = str(seg_b_row["seg"])
                val_a = float(seg_a_row["val"] or 0)
                val_b = float(seg_b_row["val"] or 0)

                abs_diff = val_a - val_b
                pct_diff = round(((val_a - val_b) / (val_b + 1e-6)) * 100.0, 1)

                return {
                    "status": "success",
                    "comparison_type": f"Segment Benchmark: {name_a} vs {name_b}",
                    "dimension": dimension_col,
                    "metric": target_metric,
                    "segment_a": {"name": name_a, "value": round(val_a, 2), "transactions": int(seg_a_row["count"])},
                    "segment_b": {"name": name_b, "value": round(val_b, 2), "transactions": int(seg_b_row["count"])},
                    "absolute_difference": round(abs_diff, 2),
                    "percentage_difference": pct_diff,
                    "higher_segment": name_a if val_a >= val_b else name_b,
                    "formatted_difference": format_val(abs_diff, "currency" if "rev" in target_metric.lower() else "number"),
                    "all_segments": seg_df.to_dict(orient="records")
                }
            except Exception as e:
                logger.error(f"Segment comparison failed: {e}")
                return {"status": "error", "message": f"Segment comparison failed: {str(e)}"}
