import pandas as pd
from typing import Dict, Any, List
from app.models.dataset import Dataset
from app.services.dataset_service import DatasetService
from app.services.ai_service import ai_service
from app.utils.helpers import parse_json
from app.core.logging import logger

ANOMALY_PROMPT = """Analyze these detected statistical anomalies. Return ONLY valid JSON array:
[
  {{"metric": "Metric name", "description": "Plain English summary (amounts in Indian Rupees ₹)", "severity": "high"|"medium"|"low", "suggestion": "Actionable recommendation"}}
]
Express any currency amounts strictly in Indian Rupees (₹), never in dollars ($).

DATA SUMMARY: {summary}
ANOMALIES DETECTED:
{anomalies}"""


class AnomalyDetector:
    @classmethod
    async def detect(cls, dataset: Dataset) -> Dict[str, Any]:
        """Detect statistical outliers (>2 sigma) and trend drop anomalies."""
        try:
            conn = DatasetService.get_duckdb_connection(dataset.storage_path, read_only=True)
            df = conn.execute(f"SELECT * FROM {dataset.table_name}").df()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to load dataset for anomaly detection: {e}")
            return {"error": "Failed to read dataset."}

        found = []

        # Numerical Outlier Detection (2 standard deviations)
        for col in df.select_dtypes(include=["number"]).columns:
            if "sl" in col.lower() and "no" in col.lower():
                continue
            series = df[col].dropna()
            if len(series) < 5:
                continue
            mean = float(series.mean())
            std = float(series.std())
            if std == 0:
                continue

            outliers = df[(df[col] > mean + 2 * std) | (df[col] < mean - 2 * std)]
            if 0 < len(outliers) <= len(df) * 0.2:
                for _, r in outliers.head(3).iterrows():
                    direction = "unusually high" if r[col] > mean else "unusually low"
                    ctx = ""
                    for ctx_col in ["product_category", "category", "product_name", "product_id", "region"]:
                        if ctx_col in df.columns and pd.notna(r.get(ctx_col)):
                            ctx += f" ({r[ctx_col]})"
                            break
                    found.append(f"{col} {direction}: {r[col]:,.0f} vs avg {mean:,.0f}{ctx}")

        # Month-over-month drop detection
        date_col = next((c for c in ["order_date", "date"] if c in df.columns), None)
        rev_col = next((c for c in ["total_revenue", "revenue", "sales"] if c in df.columns), None)
        if date_col and rev_col:
            try:
                df["_m"] = pd.to_datetime(df[date_col], errors="coerce").dt.strftime("%Y-%m")
                mo = df.groupby("_m")[rev_col].sum().reset_index().dropna()
                mo["pct"] = mo[rev_col].pct_change() * 100.0
                for _, r in mo[mo["pct"] < -15].iterrows():
                    found.append(f"Revenue dropped {r['pct']:.1f}% in {r['_m']}")
            except Exception:
                pass

        if not found:
            return {"anomalies": [], "count": 0, "ai_analysis": []}

        summary = f"Dataset: {len(df)} rows. Columns: {list(df.columns)}"
        try:
            raw = await ai_service.chat(
                "You are an anomaly detection auditor.",
                ANOMALY_PROMPT.format(summary=summary, anomalies="\n".join(f"- {a}" for a in found[:6])),
                temp=0.1
            )
            ai_analysis = parse_json(raw)[:5]
        except Exception:
            ai_analysis = [
                {"metric": a[:30], "description": a, "severity": "medium", "suggestion": "Investigate root cause"}
                for a in found[:5]
            ]

        return {
            "anomalies": found[:8],
            "count": len(found),
            "ai_analysis": ai_analysis
        }
