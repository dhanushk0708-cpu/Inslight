import math
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import duckdb
from app.utils.formatters import format_val
from app.core.logging import logger

try:
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class AdvancedAnomalyService:
    """
    Advanced Multi-Algorithmic Anomaly Detection Engine.
    Detects revenue drops, volume spikes, multivariate margin outliers,
    and regional performance deviations using Z-score, IQR, and Isolation Forest.
    Categorizes anomalies into positive opportunities vs negative risks.
    """

    @classmethod
    def detect_anomalies(
        cls,
        conn: duckdb.DuckDBPyConnection,
        table_name: str,
        methods: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute comprehensive outlier audit across tabular rows.
        """
        if not methods:
            methods = ["zscore", "iqr", "isolation_forest", "time_series"]

        df_cols = conn.execute(f"DESCRIBE {table_name}").df()
        col_names = list(df_cols["column_name"])
        col_types = {r["column_name"]: str(r["column_type"]).lower() for _, r in df_cols.iterrows()}

        numeric_cols = [c for c in col_names if any(t in col_types[c] for t in ["int", "double", "float", "decimal", "numeric"])]
        categorical_cols = [c for c in col_names if any(t in col_types[c] for t in ["varchar", "text", "char", "string"])]
        date_col = next((c for c in col_names if any(d in c.lower() for d in ["date", "timestamp", "created_at", "month"])), None)

        if not numeric_cols:
            return {
                "status": "unsupported",
                "message": "Dataset does not contain numeric measures required for anomaly detection."
            }

        total_rows = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        anomalies_found: List[Dict[str, Any]] = []

        # 1. Univariate Statistical Detection (Z-Score & IQR) on Primary Metrics
        primary_metrics = [c for c in numeric_cols if any(k in c.lower() for k in ["revenue", "sales", "profit", "amount", "price", "units", "quantity"])]
        if not primary_metrics:
            primary_metrics = numeric_cols[:2]

        for col in primary_metrics:
            try:
                stats_row = conn.execute(f"""
                    SELECT AVG(CAST({col} AS DOUBLE)) AS mean_val,
                           STDDEV(CAST({col} AS DOUBLE)) AS std_val,
                           PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY CAST({col} AS DOUBLE)) AS q1,
                           PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY CAST({col} AS DOUBLE)) AS q3
                    FROM {table_name}
                    WHERE {col} IS NOT NULL
                """).fetchone()

                if not stats_row or stats_row[0] is None:
                    continue

                mean_val, std_val, q1, q3 = stats_row
                std_val = std_val or 0.0
                iqr = (q3 - q1) if (q1 is not None and q3 is not None) else 0.0

                # Z-Score Outliers (|z| > 2.8)
                if std_val > 0 and "zscore" in methods:
                    z_high = mean_val + (2.8 * std_val)
                    z_low = mean_val - (2.8 * std_val)
                    sample_query = f"""
                        SELECT *, CAST({col} AS DOUBLE) AS val
                        FROM {table_name}
                        WHERE CAST({col} AS DOUBLE) > {z_high} OR CAST({col} AS DOUBLE) < {z_low}
                        LIMIT 5
                    """
                    df_out = conn.execute(sample_query).df()
                    for _, r in df_out.iterrows():
                        val = float(r["val"])
                        z_score = round((val - mean_val) / std_val, 2)
                        is_spike = val > mean_val
                        anomalies_found.append({
                            "id": f"anom-z-{col}-{len(anomalies_found)+1}",
                            "metric": col,
                            "observed_value": val,
                            "baseline": round(mean_val, 2),
                            "deviation_pct": round(((val - mean_val) / (mean_val + 1e-6)) * 100.0, 1),
                            "severity": "HIGH" if abs(z_score) > 3.5 else "MEDIUM",
                            "detection_method": "Z-Score (Gaussian Distribution)",
                            "type": "opportunity" if is_spike else "risk",
                            "segment": str(r.get(categorical_cols[0], "Transaction")) if categorical_cols else "Row Outlier",
                            "summary": f"{col} of {val:,.2f} deviated by {z_score} standard deviations from mean ({mean_val:,.2f}).",
                            "business_significance": (
                                "Significant volume or revenue spike indicating surging demand, seasonal batch ordering, or high-value enterprise transaction."
                                if is_spike else
                                "Unusually depressed transaction figure or severe discounting; potential revenue leakage or recording error."
                            )
                        })

                # IQR Outliers (values outside Q1 - 1.5*IQR or Q3 + 1.5*IQR)
                if iqr > 0 and "iqr" in methods and len(anomalies_found) < 10:
                    upper_bound = q3 + (1.5 * iqr)
                    lower_bound = q1 - (1.5 * iqr)
                    iqr_query = f"""
                        SELECT *, CAST({col} AS DOUBLE) AS val
                        FROM {table_name}
                        WHERE CAST({col} AS DOUBLE) > {upper_bound} OR CAST({col} AS DOUBLE) < {lower_bound}
                        LIMIT 3
                    """
                    df_iqr = conn.execute(iqr_query).df()
                    for _, r in df_iqr.iterrows():
                        val = float(r["val"])
                        # Avoid duplicating row if already captured by zscore
                        if not any(a["observed_value"] == val and a["metric"] == col for a in anomalies_found):
                            anomalies_found.append({
                                "id": f"anom-iqr-{col}-{len(anomalies_found)+1}",
                                "metric": col,
                                "observed_value": val,
                                "baseline": round((q1 + q3) / 2.0, 2),
                                "deviation_pct": round(((val - q3) / (iqr + 1e-6)) * 100.0, 1),
                                "severity": "MEDIUM",
                                "detection_method": "Interquartile Range (IQR)",
                                "type": "opportunity" if val > upper_bound else "risk",
                                "segment": str(r.get(categorical_cols[0], "Transaction")) if categorical_cols else "Row Outlier",
                                "summary": f"{col} value of {val:,.2f} breaches statistical quartile thresholds (IQR: {iqr:,.2f}).",
                                "business_significance": "Non-parametric distribution outlier indicating atypical order sizing."
                            })
            except Exception as e:
                logger.warning(f"Univariate anomaly detection failed on {col}: {e}")

        # 2. Multivariate Isolation Forest (Detects multidimensional irregularities)
        if SKLEARN_AVAILABLE and len(numeric_cols) >= 2 and total_rows >= 20 and "isolation_forest" in methods:
            try:
                features = numeric_cols[:4]
                df_multi = conn.execute(f"SELECT {', '.join(features)} FROM {table_name} LIMIT 500").df().dropna()
                if len(df_multi) >= 20:
                    iso = IsolationForest(contamination=0.04, random_state=42)
                    preds = iso.fit_predict(df_multi)
                    outlier_indices = np.where(preds == -1)[0]
                    for idx in outlier_indices[:3]:
                        sample_row = df_multi.iloc[idx].to_dict()
                        anomalies_found.append({
                            "id": f"anom-iso-{len(anomalies_found)+1}",
                            "metric": "Multi-Attribute Anomaly (" + ", ".join(features[:2]) + ")",
                            "observed_value": float(sample_row[features[0]]),
                            "baseline": float(df_multi[features[0]].median()),
                            "deviation_pct": round(((sample_row[features[0]] - df_multi[features[0]].median()) / (df_multi[features[0]].median() + 1e-6)) * 100.0, 1),
                            "severity": "HIGH",
                            "detection_method": "Isolation Forest (Machine Learning Ensemble)",
                            "type": "risk",
                            "segment": "Multivariate Record",
                            "summary": f"Unusual multivariate combination across dimensions {features}: {sample_row}",
                            "business_significance": "Complex multivariate outlier where individual metrics may appear normal in isolation, but their joint interaction violates expected business relationships (e.g. high volume at disproportionately low revenue)."
                        })
            except Exception as e:
                logger.warning(f"Isolation Forest failed: {e}")

        # Summary categorization
        total_anomalies = len(anomalies_found)
        risks_count = sum(1 for a in anomalies_found if a["type"] == "risk")
        opportunities_count = sum(1 for a in anomalies_found if a["type"] == "opportunity")

        return {
            "status": "success",
            "total_records_scanned": total_rows,
            "anomalies_detected_count": total_anomalies,
            "risks_count": risks_count,
            "opportunities_count": opportunities_count,
            "anomalies": anomalies_found,
            "governance_note": "Every flagged record represents an empirical deviation from historical baseline distributions. Not all outliers are operational defects—positive spikes represent commercial growth opportunities to replicate."
        }
