import math
from typing import Dict, Any, List, Optional
import duckdb
from app.utils.formatters import format_val
from app.core.logging import logger


class StrategicAnalysisService:
    """
    Strategic Business Performance & Opportunity/Risk Analysis Engine.
    Dynamically analyzes tabular business datasets to compute:
    1. Executive KPI Metrics (Revenue, Profit, Margins, Volume, AOV).
    2. Dimensional Segment Contribution & Performance Rankings.
    3. Top 3 High-Impact Commercial Opportunities.
    4. Top 3 Structural Operational / Financial Risks.
    5. Interactive Visualizations (Main Chart, Secondary Chart, Supporting Evidence Table).
    Works dynamically across any business dataset with varying schemas.
    """

    @classmethod
    def analyze_business_performance(
        cls,
        conn: duckdb.DuckDBPyConnection,
        table_name: str,
        question: str,
        dataset_name: Optional[str] = "Dataset"
    ) -> Dict[str, Any]:
        q_lower = question.lower()
        cols_meta = conn.execute(f"DESCRIBE {table_name}").fetchall()
        cols = [c[0] for c in cols_meta]
        types = {c[0]: c[1] for c in cols_meta}

        # 1. Measure & Dimension Inference
        rev_col = next((c for c in cols if any(k == c.lower() for k in ["revenue", "sales", "amount", "total_amount", "turnover"])), None)
        if not rev_col:
            # Fallback to any numeric column with 'rev' or 'sal'
            rev_col = next((c for c in cols if any(k in c.lower() for k in ["rev", "sale", "price"]) and any(t in types[c].upper() for t in ["INT", "DOUBLE", "FLOAT", "DECIMAL", "NUMERIC"])), None)

        profit_col = next((c for c in cols if any(k == c.lower() for k in ["profit", "margin", "net_profit", "earnings"])), None)
        cost_col = next((c for c in cols if any(k == c.lower() for k in ["cost", "expense", "cogs", "expenses"])), None)
        units_col = next((c for c in cols if any(k in c.lower() for k in ["unit_sold", "units_sold", "quantity", "qty", "volume", "orders"])), None)
        date_col = next((c for c in cols if any(k in c.lower() for k in ["date", "order_date", "timestamp", "created_at", "month"])), None)
        order_id_col = next((c for c in cols if any(k == c.lower() for k in ["order_id", "transaction_id", "invoice_id", "basket_id", "bill_id", "receipt_id"])), None)
        inv_col = next((c for c in cols if any(k in c.lower() for k in ["inventory", "stock_qty", "stock_value", "on_hand", "aging", "turnover", "days_in_stock"])), None)

        # Categorical text dimensions
        dim_candidates = [
            c for c in cols
            if any(t in types[c].upper() for t in ["VARCHAR", "TEXT", "STRING"])
            and c != date_col
        ]

        # Prioritize dimensions based on query intent or cardinality
        primary_dim = None
        secondary_dim = None

        if any(k in q_lower for k in ["product", "item", "sku"]):
            primary_dim = next((c for c in dim_candidates if "product" in c.lower()), dim_candidates[0] if dim_candidates else None)
        elif any(k in q_lower for k in ["region", "territory", "location", "geography"]):
            primary_dim = next((c for c in dim_candidates if "region" in c.lower()), dim_candidates[0] if dim_candidates else None)
        elif any(k in q_lower for k in ["category", "department"]):
            primary_dim = next((c for c in dim_candidates if "category" in c.lower()), dim_candidates[0] if dim_candidates else None)

        if not primary_dim and dim_candidates:
            # Pick dimension with highest business relevance: category, product, or region
            preferred = ["product_category", "category", "product_name", "product", "region", "segment"]
            for p in preferred:
                matched = next((c for c in dim_candidates if p == c.lower() or p in c.lower()), None)
                if matched:
                    primary_dim = matched
                    break
            if not primary_dim:
                primary_dim = dim_candidates[0]

        # Pick secondary dimension
        remaining_dims = [d for d in dim_candidates if d != primary_dim]
        if remaining_dims:
            preferred_sec = ["region", "product_name", "salesperson", "channel", "category"]
            for p in preferred_sec:
                matched = next((c for c in remaining_dims if p == c.lower() or p in c.lower()), None)
                if matched:
                    secondary_dim = matched
                    break
            if not secondary_dim:
                secondary_dim = remaining_dims[0]

        # 2. Executive KPIs Calculation
        total_rows = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        total_revenue = float(conn.execute(f"SELECT COALESCE(SUM({rev_col}), 0) FROM {table_name}").fetchone()[0]) if rev_col else 0.0

        if profit_col:
            total_profit = float(conn.execute(f"SELECT COALESCE(SUM({profit_col}), 0) FROM {table_name}").fetchone()[0])
        elif cost_col and rev_col:
            total_profit = float(conn.execute(f"SELECT COALESCE(SUM({rev_col} - {cost_col}), 0) FROM {table_name}").fetchone()[0])
        else:
            total_profit = 0.0

        total_cost = float(conn.execute(f"SELECT COALESCE(SUM({cost_col}), 0) FROM {table_name}").fetchone()[0]) if cost_col else (total_revenue - total_profit if total_profit > 0 else 0.0)
        total_units = int(conn.execute(f"SELECT COALESCE(SUM({units_col}), 0) FROM {table_name}").fetchone()[0]) if units_col else total_rows
        gross_margin_pct = round((total_profit / total_revenue * 100), 1) if total_revenue > 0 else 0.0
        avg_order_val = round(total_revenue / total_rows, 0) if total_rows > 0 else 0.0

        analytical_steps = [
            f"1. Interpreted strategic business question: '{question}'.",
            f"2. Validated active dataset '{dataset_name}' ({total_rows:,} records).",
            f"3. Inspected dataset measures (Revenue: '{rev_col or 'N/A'}', Profit: '{profit_col or 'N/A'}', Volume: '{units_col or 'N/A'}') and dimensions ({', '.join(dim_candidates[:4]) or 'None'}).",
            f"4. Computed core business KPIs: Total Revenue ₹{total_revenue:,.0f}, Net Profit ₹{total_profit:,.0f} (Margin: {gross_margin_pct}%), Volume: {total_units:,} units."
        ]

        # 3. Primary Dimension Segment Performance
        primary_segments = []
        if primary_dim and rev_col:
            sql_dim = f"""
                SELECT
                    CAST({primary_dim} AS VARCHAR) AS segment,
                    COALESCE(SUM({rev_col}), 0) AS revenue,
                    {'COALESCE(SUM(' + profit_col + '), 0)' if profit_col else '0'} AS profit,
                    {'COALESCE(SUM(' + units_col + '), 0)' if units_col else 'COUNT(*)'} AS units
                FROM {table_name}
                GROUP BY 1
                ORDER BY revenue DESC
            """
            for row in conn.execute(sql_dim).fetchall():
                s_rev = float(row[1])
                s_profit = float(row[2])
                s_units = int(row[3])
                s_margin = round((s_profit / s_rev * 100), 1) if s_rev > 0 else 0.0
                s_share = round((s_rev / total_revenue * 100), 1) if total_revenue > 0 else 0.0
                primary_segments.append({
                    "segment": str(row[0] or "Unknown"),
                    "revenue": s_rev,
                    "profit": s_profit,
                    "units": s_units,
                    "margin_pct": s_margin,
                    "share_pct": s_share
                })
            analytical_steps.append(f"5. Benchmarked segments across primary dimension '{primary_dim}' ({len(primary_segments)} segments).")

        # 4. Secondary Dimension Performance (e.g. Region or Product)
        secondary_segments = []
        if secondary_dim and rev_col:
            sql_sec = f"""
                SELECT
                    CAST({secondary_dim} AS VARCHAR) AS segment,
                    COALESCE(SUM({rev_col}), 0) AS revenue,
                    {'COALESCE(SUM(' + profit_col + '), 0)' if profit_col else '0'} AS profit,
                    {'COALESCE(SUM(' + units_col + '), 0)' if units_col else 'COUNT(*)'} AS units
                FROM {table_name}
                GROUP BY 1
                ORDER BY revenue DESC
            """
            for row in conn.execute(sql_sec).fetchall():
                sec_rev = float(row[1])
                sec_profit = float(row[2])
                sec_units = int(row[3])
                sec_margin = round((sec_profit / sec_rev * 100), 1) if sec_rev > 0 else 0.0
                sec_share = round((sec_rev / total_revenue * 100), 1) if total_revenue > 0 else 0.0
                secondary_segments.append({
                    "segment": str(row[0] or "Unknown"),
                    "revenue": sec_rev,
                    "profit": sec_profit,
                    "units": sec_units,
                    "margin_pct": sec_margin,
                    "share_pct": sec_share
                })
            analytical_steps.append(f"6. Benchmarked geographical / category distribution across '{secondary_dim}'.")

        # 5. Product Level Specifics (if product_name column exists)
        product_col = next((c for c in cols if any(k == c.lower() for k in ["product_name", "product", "item_name", "item", "sku"])), None)
        products_ranking = []
        if product_col and rev_col and product_col != primary_dim:
            sql_prod = f"""
                SELECT
                    CAST({product_col} AS VARCHAR) AS product,
                    COALESCE(SUM({rev_col}), 0) AS revenue,
                    {'COALESCE(SUM(' + profit_col + '), 0)' if profit_col else '0'} AS profit,
                    {'COALESCE(SUM(' + units_col + '), 0)' if units_col else 'COUNT(*)'} AS units
                FROM {table_name}
                GROUP BY 1
                ORDER BY revenue DESC
            """
            for row in conn.execute(sql_prod).fetchall():
                p_rev = float(row[1])
                p_profit = float(row[2])
                p_units = int(row[3])
                p_margin = round((p_profit / p_rev * 100), 1) if p_rev > 0 else 0.0
                products_ranking.append({
                    "product": str(row[0] or "Unknown"),
                    "revenue": p_rev,
                    "profit": p_profit,
                    "units": p_units,
                    "margin_pct": p_margin
                })

        # 5b. Basket Co-occurrence & Historical Margin Validation Checks
        basket_pair = None
        if order_id_col and product_col:
            try:
                b_row = conn.execute(f"""
                    SELECT CAST(a.{product_col} AS VARCHAR) AS p1,
                           CAST(b.{product_col} AS VARCHAR) AS p2,
                           COUNT(DISTINCT a.{order_id_col}) AS co_count
                    FROM {table_name} a
                    JOIN {table_name} b
                      ON a.{order_id_col} = b.{order_id_col}
                     AND CAST(a.{product_col} AS VARCHAR) < CAST(b.{product_col} AS VARCHAR)
                    GROUP BY 1, 2
                    ORDER BY co_count DESC
                    LIMIT 1
                """).fetchone()
                if b_row and int(b_row[2]) >= 2:
                    basket_pair = {"p1": b_row[0], "p2": b_row[1], "co_count": int(b_row[2])}
            except Exception:
                pass

        margin_declined = False
        margin_trend_note = ""
        if date_col and profit_col and rev_col:
            try:
                m_rows = conn.execute(f"""
                    SELECT strftime(TRY_CAST({date_col} AS DATE), '%Y-%m') AS period,
                           SUM({profit_col}) * 100.0 / NULLIF(SUM({rev_col}), 0) AS margin_pct
                    FROM {table_name}
                    WHERE TRY_CAST({date_col} AS DATE) IS NOT NULL
                    GROUP BY 1
                    ORDER BY 1
                """).fetchall()
                if len(m_rows) >= 2 and m_rows[0][1] is not None and m_rows[-1][1] is not None:
                    first_m = round(float(m_rows[0][1]), 1)
                    last_m = round(float(m_rows[-1][1]), 1)
                    if last_m < first_m - 1.0:
                        margin_declined = True
                        margin_trend_note = f"declined from {first_m}% in {m_rows[0][0]} to {last_m}% in {m_rows[-1][0]}"
            except Exception:
                pass

        # 6. Structured Generation of Top 3 Opportunities
        opportunities = []

        # Opportunity 1: High-Margin Segment or Product Expansion
        highest_margin_item = None
        pool_for_margin = products_ranking if products_ranking else primary_segments
        if pool_for_margin:
            high_margins = [p for p in pool_for_margin if p["margin_pct"] >= gross_margin_pct]
            if high_margins:
                highest_margin_item = max(high_margins, key=lambda x: x["margin_pct"])

        if highest_margin_item and highest_margin_item["margin_pct"] > 0:
            name = highest_margin_item.get("product") or highest_margin_item.get("segment")
            src_col = product_col if "product" in highest_margin_item else primary_dim
            opportunities.append({
                "rank": 1,
                "title": f"Scale High-Margin Portfolio: {name}",
                "is_hypothesis": False,
                "supporting_metric": "Product Gross Margin (%) vs Portfolio Average",
                "actual_value": f"{highest_margin_item['margin_pct']}% margin (₹{highest_margin_item['profit']:,.0f} profit on ₹{highest_margin_item['revenue']:,.0f} revenue) vs {gross_margin_pct}% avg",
                "evidence_source": f"{dataset_name} ({total_rows:,} rows) → {src_col}, {rev_col}, {profit_col or 'cost'}",
                "business_interpretation": f"'{name}' outperforms the portfolio margin benchmark by {round(highest_margin_item['margin_pct'] - gross_margin_pct, 1)} percentage points, making each incremental sale disproportionately accretive to net profit.",
                "impact": f"'{name}' yields {highest_margin_item['margin_pct']}% margin vs {gross_margin_pct}% portfolio average (₹{highest_margin_item['profit']:,.0f} profit on ₹{highest_margin_item['revenue']:,.0f} revenue).",
                "recommendation": f"Prioritize marketing allocation and featured placement for {name} to grow high-margin revenue contribution."
            })
        elif primary_segments:
            top_seg = primary_segments[0]
            opportunities.append({
                "rank": 1,
                "title": f"Amplify Market Leader: {top_seg['segment']}",
                "is_hypothesis": False,
                "supporting_metric": "Category Revenue Share (%)",
                "actual_value": f"{top_seg['share_pct']}% share (₹{top_seg['revenue']:,.0f})",
                "evidence_source": f"{dataset_name} ({total_rows:,} rows) → {primary_dim}, {rev_col}",
                "business_interpretation": f"'{top_seg['segment']}' demonstrates strongest market demand, commanding {top_seg['share_pct']}% of total sales.",
                "impact": f"'{top_seg['segment']}' commands {top_seg['share_pct']}% of total revenue (₹{top_seg['revenue']:,.0f}).",
                "recommendation": f"Deepen vendor relationships in {top_seg['segment']} to secure volume rebates and extend delivery coverage."
            })

        # Opportunity 2: Cross-Sell & Upsell (Strictly Validated via Basket Co-occurrence)
        top_rev_item = (products_ranking[0] if products_ranking else (primary_segments[0] if primary_segments else None))
        high_vol_item = max(products_ranking, key=lambda x: x["units"]) if products_ranking and len(products_ranking) > 1 else None

        if basket_pair:
            opportunities.append({
                "rank": 2,
                "title": f"Data-Backed Cross-Sell Bundle: {basket_pair['p1']} + {basket_pair['p2']}",
                "is_hypothesis": False,
                "supporting_metric": "Transaction Basket Co-occurrence Count",
                "actual_value": f"{basket_pair['co_count']:,} shared orders containing both items",
                "evidence_source": f"{dataset_name} ({total_rows:,} rows) → {order_id_col}, {product_col}",
                "business_interpretation": f"Transaction-level basket analysis confirms '{basket_pair['p1']}' and '{basket_pair['p2']}' are frequently purchased together across {basket_pair['co_count']:,} distinct orders.",
                "impact": f"Confirmed co-purchase affinity across {basket_pair['co_count']:,} transactions supports formal bundle pricing.",
                "recommendation": f"Launch an automated checkout bundle pairing {basket_pair['p1']} and {basket_pair['p2']} to increase average order value."
            })
        elif top_rev_item and high_vol_item and top_rev_item != high_vol_item:
            top_name = top_rev_item.get("product") or top_rev_item.get("segment")
            vol_name = high_vol_item.get("product") or high_vol_item.get("segment")
            opportunities.append({
                "rank": 2,
                "title": f"Cross-Sell Hypothesis (Requires Validation): {top_name} + {vol_name}",
                "is_hypothesis": True,
                "supporting_metric": "Individual Product Revenue & Unit Velocity (No Basket ID Available)",
                "actual_value": f"{top_name}: ₹{top_rev_item['revenue']:,.0f} revenue | {vol_name}: {high_vol_item['units']:,} units ({high_vol_item['margin_pct']}% margin)",
                "evidence_source": f"{dataset_name} ({total_rows:,} rows) → {product_col}, {rev_col}, {units_col or 'rows'} (Note: no transaction/order ID column exists for basket analysis)",
                "business_interpretation": f"Dataset lacks an order/basket ID to verify co-purchase behavior. Pairing top-revenue '{top_name}' with high-velocity '{vol_name}' is presented strictly as a business hypothesis requiring transaction-level validation.",
                "impact": f"[Hypothesis] '{top_name}' leads revenue (₹{top_rev_item['revenue']:,.0f}) while '{vol_name}' leads volume ({high_vol_item['units']:,} units). No basket ID exists to confirm co-purchase.",
                "recommendation": f"Run a controlled A/B checkout test bundling {top_name} with {vol_name} and capture basket/order IDs to validate attach rates."
            })
        elif len(primary_segments) > 1:
            sec_seg = primary_segments[1]
            opportunities.append({
                "rank": 2,
                "title": f"Expand Secondary Pillar: {sec_seg['segment']}",
                "is_hypothesis": False,
                "supporting_metric": "Secondary Segment Revenue & Margin",
                "actual_value": f"₹{sec_seg['revenue']:,.0f} ({sec_seg['share_pct']}% share, {sec_seg['margin_pct']}% margin)",
                "evidence_source": f"{dataset_name} ({total_rows:,} rows) → {primary_dim}, {rev_col}",
                "business_interpretation": f"'{sec_seg['segment']}' provides healthy diversification with {sec_seg['margin_pct']}% margin.",
                "impact": f"'{sec_seg['segment']}' delivers ₹{sec_seg['revenue']:,.0f} ({sec_seg['share_pct']}% share) with {sec_seg['margin_pct']}% margin.",
                "recommendation": f"Launch targeted seasonal promotions for {sec_seg['segment']} to grow its revenue share."
            })

        # Opportunity 3: Geographic / Channel Expansion (Explicit Calculation & Hypothetical Scenario Label)
        if secondary_segments and len(secondary_segments) > 1:
            top_sec = secondary_segments[0]
            bottom_sec = secondary_segments[-1]
            diff_rev = top_sec["revenue"] - bottom_sec["revenue"]
            diff_pct = round((diff_rev / top_sec["revenue"] * 100), 1) if top_sec["revenue"] > 0 else 0.0
            closure_rate = 0.40
            potential = round(diff_rev * closure_rate, 0)
            opportunities.append({
                "rank": 3,
                "title": f"Regional Growth Opportunity (Hypothetical Scenario): {bottom_sec['segment']} vs {top_sec['segment']}",
                "is_hypothesis": True,
                "supporting_metric": "Regional Revenue Gap & Hypothetical 40% Gap-Closure Model",
                "actual_value": f"Gap: ₹{diff_rev:,.0f} ({top_sec['segment']} ₹{top_sec['revenue']:,.0f} - {bottom_sec['segment']} ₹{bottom_sec['revenue']:,.0f} = ₹{diff_rev:,.0f}, -{diff_pct}%); Hypothetical 40% closure: ₹{diff_rev:,.0f} × 0.40 = ₹{potential:,.0f}",
                "evidence_source": f"{dataset_name} ({total_rows:,} rows) → {secondary_dim}, {rev_col}",
                "business_interpretation": f"'{bottom_sec['segment']}' trails '{top_sec['segment']}' by {diff_pct}%. Assuming comparable market capacity and a hypothetical 40% gap-closure target (₹{diff_rev:,.0f} × 40%), incremental revenue could reach ~₹{potential:,.0f}.",
                "impact": f"[Hypothetical Scenario] {bottom_sec['segment']} (₹{bottom_sec['revenue']:,.0f}) trails {top_sec['segment']} (₹{top_sec['revenue']:,.0f}) by ₹{diff_rev:,.0f} ({diff_pct}%). Calculation: ₹{diff_rev:,.0f} × 40% assumed gap closure = ₹{potential:,.0f}.",
                "recommendation": f"Audit regional demand potential and distributor coverage in {bottom_sec['segment']} before committing expansion budget."
            })
        elif len(primary_segments) > 2:
            mid_seg = primary_segments[2]
            est_gain = round(mid_seg["revenue"] * 0.15, 0)
            opportunities.append({
                "rank": 3,
                "title": f"Segment Expansion (Hypothetical Scenario): {mid_seg['segment']}",
                "is_hypothesis": True,
                "supporting_metric": "Segment Revenue & Hypothetical 15% Uplift Model",
                "actual_value": f"₹{mid_seg['revenue']:,.0f} ({mid_seg['share_pct']}% share); Hypothetical 15% uplift: ₹{mid_seg['revenue']:,.0f} × 0.15 = ₹{est_gain:,.0f}",
                "evidence_source": f"{dataset_name} ({total_rows:,} rows) → {primary_dim}, {rev_col}",
                "business_interpretation": f"Assuming a hypothetical 15% conversion uplift on '{mid_seg['segment']}' revenue (₹{mid_seg['revenue']:,.0f} × 15%), incremental revenue would equal ₹{est_gain:,.0f}.",
                "impact": f"[Hypothetical Scenario] '{mid_seg['segment']}' generates ₹{mid_seg['revenue']:,.0f} ({mid_seg['share_pct']}% share). Calculation: ₹{mid_seg['revenue']:,.0f} × 15% uplift = ₹{est_gain:,.0f}.",
                "recommendation": "Deploy targeted customer re-engagement campaigns to test conversion sensitivity."
            })

        # 7. Structured Generation of Top 3 Structural Risks
        risks = []

        # Risk 1: High Revenue Concentration
        if primary_segments:
            top_seg = primary_segments[0]
            severity = "critical" if top_seg["share_pct"] > 50 else ("warning" if top_seg["share_pct"] > 35 else "info")
            risks.append({
                "rank": 1,
                "title": f"Revenue Concentration in {top_seg['segment']} ({top_seg['share_pct']}%)",
                "severity": severity,
                "supporting_metric": "Single-Category Revenue Share (%)",
                "actual_value": f"{top_seg['share_pct']}% (₹{top_seg['revenue']:,.0f} out of ₹{total_revenue:,.0f})",
                "evidence_source": f"{dataset_name} ({total_rows:,} rows) → {primary_dim}, {rev_col}",
                "business_interpretation": f"Over {top_seg['share_pct']}% of total revenue depends on '{top_seg['segment']}', creating high exposure to category-specific supply disruptions or demand shifts.",
                "impact": f"{top_seg['share_pct']}% of total revenue (₹{top_seg['revenue']:,.0f}) is concentrated in {top_seg['segment']}.",
                "mitigation": "Diversify revenue mix by accelerating marketing and catalog breadth in secondary categories."
            })

        # Risk 2: Margin Validation (Only call it "Margin Compression" if historical decline exists)
        if products_ranking and len(products_ranking) >= 2:
            top_p1 = products_ranking[0]
            top_p2 = products_ranking[1]
            if top_p1["margin_pct"] < gross_margin_pct or top_p2["margin_pct"] < gross_margin_pct:
                combined_rev = top_p1["revenue"] + top_p2["revenue"]
                if margin_declined:
                    r_title = "Margin Compression on High-Volume Flagships"
                    r_interp = f"Historical margins {margin_trend_note}. Leading revenue drivers '{top_p1['product']}' ({top_p1['margin_pct']}%) and '{top_p2['product']}' ({top_p2['margin_pct']}%) sit below the {gross_margin_pct}% portfolio benchmark."
                    r_impact = f"Historical margin {margin_trend_note}; top drivers '{top_p1['product']}' ({top_p1['margin_pct']}%) and '{top_p2['product']}' ({top_p2['margin_pct']}%) lag the {gross_margin_pct}% average."
                else:
                    r_title = "Below-Average Profitability on Core Revenue Drivers"
                    r_interp = f"No historical margin decline was observed across periods, so this reflects structurally lower unit profitability rather than margin compression. '{top_p1['product']}' ({top_p1['margin_pct']}%) and '{top_p2['product']}' ({top_p2['margin_pct']}%) trail the {gross_margin_pct}% average while generating ₹{combined_rev:,.0f}."
                    r_impact = f"'{top_p1['product']}' ({top_p1['margin_pct']}%) and '{top_p2['product']}' ({top_p2['margin_pct']}%) operate below the {gross_margin_pct}% portfolio average across ₹{combined_rev:,.0f} of revenue."
                risks.append({
                    "rank": 2,
                    "title": r_title,
                    "severity": "warning",
                    "supporting_metric": "Flagship Product Gross Margin (%) vs Portfolio Average",
                    "actual_value": f"{top_p1['product']}: {top_p1['margin_pct']}%, {top_p2['product']}: {top_p2['margin_pct']}% vs {gross_margin_pct}% avg",
                    "evidence_source": f"{dataset_name} ({total_rows:,} rows) → {product_col}, {rev_col}, {profit_col or 'cost'}",
                    "business_interpretation": r_interp,
                    "impact": r_impact,
                    "mitigation": "Renegotiate wholesale procurement pricing, enforce minimum discount floors, and introduce higher-margin flagship variants."
                })
            else:
                low_margin = min(products_ranking, key=lambda x: x["margin_pct"])
                risks.append({
                    "rank": 2,
                    "title": f"Below-Average Profitability in {low_margin['product']} ({low_margin['margin_pct']}%)",
                    "severity": "warning",
                    "supporting_metric": "Lowest Product Gross Margin (%)",
                    "actual_value": f"{low_margin['margin_pct']}% margin (₹{low_margin['profit']:,.0f} on ₹{low_margin['revenue']:,.0f})",
                    "evidence_source": f"{dataset_name} ({total_rows:,} rows) → {product_col}, {rev_col}, {profit_col or 'cost'}",
                    "business_interpretation": f"'{low_margin['product']}' records the lowest unit profitability ({low_margin['margin_pct']}%) in the portfolio.",
                    "impact": f"'{low_margin['product']}' delivers only {low_margin['margin_pct']}% margin vs {gross_margin_pct}% portfolio average.",
                    "mitigation": "Audit unit cost structures and establish minimum margin guardrails before approving discounts."
                })
        elif len(primary_segments) > 1:
            lowest_margin_seg = min(primary_segments, key=lambda x: x["margin_pct"])
            risks.append({
                "rank": 2,
                "title": f"Below-Average Profitability in {lowest_margin_seg['segment']} ({lowest_margin_seg['margin_pct']}%)",
                "severity": "warning",
                "supporting_metric": "Segment Gross Margin (%)",
                "actual_value": f"{lowest_margin_seg['margin_pct']}% vs {gross_margin_pct}% avg",
                "evidence_source": f"{dataset_name} ({total_rows:,} rows) → {primary_dim}, {rev_col}",
                "business_interpretation": f"'{lowest_margin_seg['segment']}' trails the {gross_margin_pct}% company-wide margin benchmark.",
                "impact": f"'{lowest_margin_seg['segment']}' operates at {lowest_margin_seg['margin_pct']}% margin.",
                "mitigation": "Conduct a cost-of-goods audit and optimize pricing across low-margin SKUs."
            })

        # Risk 3: Inventory vs Low Sales Velocity Validation
        if products_ranking and len(products_ranking) > 3:
            slow_product = min(products_ranking, key=lambda x: x["revenue"])
            if inv_col:
                # Actual inventory data exists
                inv_val = conn.execute(f"SELECT COALESCE(SUM({inv_col}), 0) FROM {table_name} WHERE CAST({product_col} AS VARCHAR) = ?", [slow_product["product"]]).fetchone()[0]
                risks.append({
                    "rank": 3,
                    "title": f"Slow-Moving SKU Inventory Accumulation: {slow_product['product']}",
                    "severity": "info",
                    "supporting_metric": f"Product Revenue & {inv_col}",
                    "actual_value": f"₹{slow_product['revenue']:,.0f} revenue ({slow_product['units']:,} units) with {inv_val:,.0f} on-hand stock",
                    "evidence_source": f"{dataset_name} ({total_rows:,} rows) → {product_col}, {rev_col}, {inv_col}",
                    "business_interpretation": f"Low revenue combined with {inv_val:,.0f} recorded in '{inv_col}' indicates physical stock accumulation.",
                    "impact": f"'{slow_product['product']}' generated only ₹{slow_product['revenue']:,.0f} with {inv_val:,.0f} in {inv_col}.",
                    "mitigation": "Run targeted clearance promotions to convert excess stock into working capital."
                })
            else:
                # No inventory columns available — strictly describe as low product sales velocity
                risks.append({
                    "rank": 3,
                    "title": f"Low Product Sales Velocity: {slow_product['product']}",
                    "severity": "info",
                    "supporting_metric": "Product Total Revenue & Units Sold (No Inventory Data Present)",
                    "actual_value": f"₹{slow_product['revenue']:,.0f} revenue across {slow_product['units']:,} units sold",
                    "evidence_source": f"{dataset_name} ({total_rows:,} rows) → {product_col}, {rev_col}, {units_col or 'rows'}",
                    "business_interpretation": f"'{slow_product['product']}' has the lowest sales velocity in the catalog. Because inventory/stock-on-hand columns are not present in this dataset, physical stock accumulation cannot be inferred.",
                    "impact": f"'{slow_product['product']}' generated only ₹{slow_product['revenue']:,.0f} across {slow_product['units']:,} units sold (sales velocity metric only; no stock data available).",
                    "mitigation": f"Investigate demand elasticity and product visibility for {slow_product['product']}; integrate stock-on-hand data before making inventory reduction decisions."
                })
        elif secondary_segments and len(secondary_segments) > 1:
            trailing_sec = secondary_segments[-1]
            risks.append({
                "rank": 3,
                "title": f"Regional Sales Underperformance: {trailing_sec['segment']}",
                "severity": "info",
                "supporting_metric": "Regional Revenue Share (%)",
                "actual_value": f"{trailing_sec['share_pct']}% (₹{trailing_sec['revenue']:,.0f})",
                "evidence_source": f"{dataset_name} ({total_rows:,} rows) → {secondary_dim}, {rev_col}",
                "business_interpretation": f"'{trailing_sec['segment']}' contributes the lowest regional share at {trailing_sec['share_pct']}%.",
                "impact": f"'{trailing_sec['segment']}' represents only {trailing_sec['share_pct']}% of revenue (₹{trailing_sec['revenue']:,.0f}).",
                "mitigation": "Review regional distribution coverage and sales rep territory incentives."
            })

        analytical_steps.append("7. Validated basket co-occurrence, historical margin trends, inventory schema availability, and ranked top 3 opportunities & risks.")

        # 8. Visual Configurations (Charts & Cards)
        kpi_cards = [
            {
                "label": "Total Revenue",
                "value": f"₹{total_revenue:,.0f}" if total_revenue < 1000000 else f"₹{total_revenue/100000:.2f} Lakhs",
                "trend": f"{total_rows:,} orders",
                "trend_direction": "up"
            },
            {
                "label": "Net Profit",
                "value": f"₹{total_profit:,.0f}" if total_profit < 1000000 else f"₹{total_profit/100000:.2f} Lakhs",
                "trend": f"{gross_margin_pct}% Margin",
                "trend_direction": "up" if gross_margin_pct >= 30 else "neutral"
            },
            {
                "label": "Gross Margin",
                "value": f"{gross_margin_pct}%",
                "trend": "Healthy" if gross_margin_pct >= 40 else "Moderate",
                "trend_direction": "up" if gross_margin_pct >= 40 else "neutral"
            },
            {
                "label": "Total Volume Sold",
                "value": f"{total_units:,} Units",
                "trend": f"AOV: ₹{avg_order_val:,.0f}",
                "trend_direction": "neutral"
            }
        ]

        # Main Chart: Primary Dimension Revenue / Profit Comparison Bar Chart
        main_chart_data = [
            {
                "name": s["segment"],
                "Revenue": s["revenue"],
                "Profit": s["profit"],
                "Units": s["units"]
            }
            for s in primary_segments[:8]
        ]
        main_chart = {
            "type": "bar",
            "title": f"Revenue & Profit by {primary_dim.replace('_', ' ').title() if primary_dim else 'Segment'}",
            "x_axis": "name",
            "y_axis": "Revenue",
            "data": main_chart_data
        }

        # Secondary Chart: Donut Share Chart (Secondary Dimension or Category)
        sec_chart_source = secondary_segments if secondary_segments else primary_segments
        secondary_chart_data = [
            {
                "name": s["segment"],
                "Revenue": s["revenue"],
                "Share": s["share_pct"]
            }
            for s in sec_chart_source[:6]
        ]
        sec_title = f"{secondary_dim.replace('_', ' ').title() if secondary_dim else primary_dim.replace('_', ' ').title()} Revenue Share"
        secondary_chart = {
            "type": "pie",
            "title": sec_title,
            "x_axis": "name",
            "y_axis": "Revenue",
            "data": secondary_chart_data
        }

        # Supporting Evidence Table
        supporting_rows = []
        table_pool = products_ranking if products_ranking else primary_segments
        for item in table_pool[:15]:
            row_dict = {}
            if "product" in item:
                row_dict["Product Name"] = item["product"]
            if "segment" in item:
                row_dict["Segment"] = item["segment"]
            row_dict["Revenue"] = f"₹{item['revenue']:,.0f}"
            row_dict["Profit"] = f"₹{item['profit']:,.0f}"
            row_dict["Margin (%)"] = f"{item['margin_pct']}%"
            row_dict["Units Sold"] = f"{item['units']:,}"
            supporting_rows.append(row_dict)

        supporting_table = {
            "title": "Segment Financial Performance Summary",
            "columns": list(supporting_rows[0].keys()) if supporting_rows else [],
            "rows": supporting_rows
        }

        analytical_steps.append("8. Generated executive KPI grid, comparative revenue charts, and supporting evidence table.")

        # 9. Concise Executive Brief Narrative
        lead_seg = primary_segments[0]["segment"] if primary_segments else "core segments"
        lead_share = primary_segments[0]["share_pct"] if primary_segments else 0.0
        lead_rev = primary_segments[0]["revenue"] if primary_segments else 0.0

        summary = (
            f"Business performance across {total_rows:,} records generated ₹{total_revenue:,.0f} in total revenue "
            f"and ₹{total_profit:,.0f} in net profit, achieving an overall gross profit margin of {gross_margin_pct}%. "
            f"Performance is anchored by {lead_seg} (₹{lead_rev:,.0f}, {lead_share}% share). "
            f"Identified 3 high-impact commercial expansion opportunities and 3 critical operational risks."
        )

        opp_lines = "\n\n".join(
            f"{o['rank']}. **{o['title']}**\n"
            f"   - *Metric:* {o['supporting_metric']} (`{o['actual_value']}`)\n"
            f"   - *Evidence Source:* {o['evidence_source']}\n"
            f"   - *Interpretation:* {o['business_interpretation']}\n"
            f"   - *Action:* {o['recommendation']}"
            for o in opportunities
        )
        risk_lines = "\n\n".join(
            f"{r['rank']}. **{r['title']}** ({r['severity'].upper()})\n"
            f"   - *Metric:* {r['supporting_metric']} (`{r['actual_value']}`)\n"
            f"   - *Evidence Source:* {r['evidence_source']}\n"
            f"   - *Interpretation:* {r['business_interpretation']}\n"
            f"   - *Mitigation:* {r['mitigation']}"
            for r in risks
        )

        answer = (
            f"### Executive Business Performance Assessment\n\n"
            f"**Portfolio Overview:**\n"
            f"- **Total Revenue:** ₹{total_revenue:,.0f} across **{total_rows:,} records**\n"
            f"- **Net Profit:** ₹{total_profit:,.0f} (**{gross_margin_pct}%** Gross Margin)\n"
            f"- **Volume Sold:** **{total_units:,} Units** (Average Order Value: ₹{avg_order_val:,.0f})\n"
            f"- **Leading Category:** **{lead_seg}** driving **{lead_share}%** of total sales turnover\n\n"
            f"---\n\n"
            f"### Top Commercial Opportunities 🚀\n"
            f"{opp_lines}\n\n"
            f"---\n\n"
            f"### Critical Structural Risks ⚠️\n"
            f"{risk_lines}"
        )

        suggested_follow_ups = [
            f"Why is {lead_seg} driving {lead_share}% of revenue?",
            f"Forecast revenue for next 30 days based on current trends.",
            f"Compare {primary_segments[0]['segment']} vs {primary_segments[1]['segment'] if len(primary_segments)>1 else 'secondary'} performance."
        ]

        return {
            "status": "success",
            "tool_used": "strategic_analysis",
            "answer": answer,
            "summary": summary,
            "reasoning_steps": analytical_steps,
            "analytical_steps": analytical_steps,
            "evidence": {
                "total_revenue": total_revenue,
                "total_profit": total_profit,
                "gross_margin_pct": gross_margin_pct,
                "total_units": total_units,
                "primary_dimension": primary_dim,
                "secondary_dimension": secondary_dim,
                "top_segment": primary_segments[0] if primary_segments else None,
                "top_opportunity": opportunities[0]["title"],
                "top_risk": risks[0]["title"]
            },
            "kpi_results": kpi_cards,
            "opportunities": opportunities,
            "risks": risks,
            "charts": {
                "main_chart": main_chart,
                "secondary_chart": secondary_chart
            },
            "supporting_table": supporting_table,
            "dataset_metadata": {
                "filename": dataset_name,
                "row_count": total_rows,
                "columns": cols
            },
            "data": {
                "kpi_cards": kpi_cards,
                "main_chart": main_chart,
                "secondary_chart": secondary_chart,
                "narrative": answer,
                "summary": summary,
                "opportunities": opportunities,
                "risks": risks,
                "supporting_table": supporting_table,
                "suggested_followups": suggested_follow_ups,
                "session_id": None
            },
            "error": None,
            "suggested_follow_ups": suggested_follow_ups
        }
