import pandas as pd
from typing import Dict, Any
from app.models.dataset import Dataset
from app.services.dataset_service import DatasetService
from app.services.ai_service import ai_service
from app.utils.formatters import format_val
from app.core.logging import logger

WHATIF_PROMPT = """Analyze this scenario simulation in 2-3 concise business sentences:
Current Revenue: ₹{current_revenue:,.0f}, Units: {current_units:,.0f}
Simulated Changes: Price {price_change:+.1f}%, Discount {discount_change:+.1f}%, Volume {units_change:+.1f}%
Projected Revenue: ₹{new_revenue:,.0f} (Net Impact: {revenue_pct_change:+.1f}%)

Express all monetary amounts in Indian Rupees (₹, Lakhs, Crores, or INR), never in dollars ($).
Return ONLY clear executive summary text."""


class ScenarioEngine:
    @classmethod
    async def simulate(
        cls,
        dataset: Dataset,
        price_change: float = 0.0,
        discount_change: float = 0.0,
        units_change: float = 0.0
    ) -> Dict[str, Any]:
        """Calculates what-if scenario sensitivity and projections."""
        try:
            conn = DatasetService.get_duckdb_connection(dataset.storage_path, read_only=True)
            df = conn.execute(f"SELECT * FROM {dataset.table_name}").df()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to load dataset for scenario simulation: {e}")
            return {"error": "Failed to read dataset."}

        cols = list(df.columns)
        rev_col = next((c for c in ["total_revenue", "revenue", "amount", "sales"] if c in cols), None)
        qty_col = next((c for c in ["quantity_sold", "quantity", "units_sold", "units"] if c in cols), None)
        date_col = next((c for c in ["order_date", "date"] if c in cols), None)
        cat_col = next((c for c in ["product_category", "category"] if c in cols), None)

        current_revenue = float(df[rev_col].sum()) if rev_col else 0.0
        current_units = float(df[qty_col].sum()) if qty_col else 0.0

        pm = 1.0 + price_change / 100.0
        um = 1.0 + units_change / 100.0
        new_revenue = current_revenue * pm * um
        discount_impact = current_revenue * (discount_change / 100.0) * 0.5
        new_revenue -= discount_impact
        revenue_diff = new_revenue - current_revenue
        pct = (revenue_diff / current_revenue * 100.0) if current_revenue else 0.0

        monthly = []
        if date_col and rev_col:
            try:
                df2 = df.copy()
                df2["_m"] = pd.to_datetime(df2[date_col], errors="coerce").dt.strftime("%Y-%m")
                mg = df2.groupby("_m")[rev_col].sum().reset_index().dropna()
                for _, r in mg.iterrows():
                    ar = float(r[rev_col])
                    pr = ar * pm * um - ar * (discount_change / 100.0) * 0.5
                    monthly.append({"month": r["_m"], "actual_revenue": round(ar), "projected_revenue": round(pr)})
            except Exception:
                pass

        cat_impact = []
        if cat_col and rev_col:
            try:
                cg = df.groupby(cat_col)[rev_col].sum().reset_index()
                for _, r in cg.iterrows():
                    cr = float(r[rev_col])
                    pr = cr * pm * um - cr * (discount_change / 100.0) * 0.5
                    cat_impact.append({
                        "category": r[cat_col],
                        "current_revenue": round(cr),
                        "projected_revenue": round(pr),
                        "change_pct": round((pr - cr) / cr * 100.0, 1) if cr else 0.0
                    })
            except Exception:
                pass

        try:
            ai_text = await ai_service.chat(
                "You are an executive financial modeler.",
                WHATIF_PROMPT.format(
                    current_revenue=current_revenue,
                    current_units=current_units,
                    price_change=price_change,
                    discount_change=discount_change,
                    units_change=units_change,
                    new_revenue=new_revenue,
                    revenue_pct_change=pct
                ),
                temp=0.3
            )
        except Exception:
            ai_text = f"Projected revenue change: {format_val(revenue_diff, 'currency')} ({pct:+.1f}%)"

        return {
            "current": {"revenue": round(current_revenue), "units": round(current_units)},
            "projected": {"revenue": round(new_revenue)},
            "change": {"revenue_diff": round(revenue_diff), "revenue_pct_change": round(pct, 1)},
            "monthly_comparison": monthly,
            "category_impact": cat_impact,
            "ai_commentary": ai_text
        }
