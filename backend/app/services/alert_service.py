import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.dataset import Dataset
from app.models.alert import Alert, AlertRule
from app.services.dataset_service import DatasetService
from app.utils.formatters import format_val
from app.core.logging import logger


class AlertService:
    """
    Intelligent Business Alert Engine.
    Evaluates rule-based and statistical triggers against active datasets,
    enforcing deduplication, severity prioritization, and user ownership.
    """

    @classmethod
    def evaluate_and_generate_alerts(
        cls,
        db: Session,
        user: User,
        dataset: Dataset
    ) -> List[Alert]:
        """
        Evaluate dataset metrics against user rules and standard business triggers.
        """
        conn = DatasetService.get_duckdb_connection(dataset.storage_path, read_only=True)
        created_alerts: List[Alert] = []

        try:
            df_cols = conn.execute(f"DESCRIBE {dataset.table_name}").df()
            col_names = list(df_cols["column_name"])
            col_types = {r["column_name"]: str(r["column_type"]).lower() for _, r in df_cols.iterrows()}

            # 1. Fetch active user rules or apply default corporate thresholds
            user_rules = db.query(AlertRule).filter(
                AlertRule.user_id == user.id,
                AlertRule.is_active == True,
                (AlertRule.dataset_id == dataset.id) | (AlertRule.dataset_id == None)
            ).all()

            # Ensure default business rules if user has none configured
            if not user_rules:
                cls.create_default_rules(db, user, dataset.id)
                user_rules = db.query(AlertRule).filter(
                    AlertRule.user_id == user.id,
                    AlertRule.is_active == True
                ).all()

            # 2. Check for Date & Revenue columns
            date_col = next((c for c in col_names if any(d in c.lower() for d in ["date", "timestamp", "created_at", "month"])), None)
            rev_col = next((c for c in col_names if any(r in c.lower() for r in ["revenue", "sales", "total_amount", "amount"])), None)
            profit_col = next((c for c in col_names if any(p in c.lower() for p in ["profit", "margin", "net_amount"])), None)

            # Check 1: Revenue Month-over-Month Drop
            if date_col and rev_col:
                try:
                    df_monthly = conn.execute(f"""
                        SELECT strftime(CAST({date_col} AS DATE), '%Y-%m') AS m,
                               SUM(CAST({rev_col} AS DOUBLE)) AS rev
                        FROM {dataset.table_name}
                        WHERE {date_col} IS NOT NULL
                        GROUP BY m
                        ORDER BY m ASC
                    """).df()
                    if len(df_monthly) >= 2:
                        prev_rev = float(df_monthly["rev"].iloc[-2])
                        curr_rev = float(df_monthly["rev"].iloc[-1])
                        curr_m = str(df_monthly["m"].iloc[-1])
                        prev_m = str(df_monthly["m"].iloc[-2])

                        if prev_rev > 0:
                            drop_pct = round(((prev_rev - curr_rev) / prev_rev) * 100.0, 1)
                            if drop_pct >= 15.0:  # 15% drop trigger
                                alert = cls._create_or_deduplicate_alert(
                                    db=db,
                                    user_id=user.id,
                                    dataset_id=dataset.id,
                                    title=f"Significant Revenue Contraction in {curr_m}",
                                    category="revenue",
                                    severity="high" if drop_pct >= 25.0 else "medium",
                                    description=f"Monthly revenue dropped by {drop_pct}% from {format_val(prev_rev, 'currency')} ({prev_m}) to {format_val(curr_rev, 'currency')} ({curr_m}).",
                                    evidence={
                                        "current_month": curr_m,
                                        "previous_month": prev_m,
                                        "previous_revenue": prev_rev,
                                        "current_revenue": curr_rev,
                                        "drop_pct": drop_pct
                                    },
                                    metric_name="monthly_revenue_drop",
                                    observed_value=drop_pct,
                                    threshold_value=15.0
                                )
                                if alert:
                                    created_alerts.append(alert)
                except Exception as e:
                    logger.warning(f"Revenue drop alert rule failed: {e}")

            # Check 2: Low or Deteriorating Profit Margin
            if rev_col and profit_col:
                try:
                    tot_rev, tot_profit = conn.execute(f"""
                        SELECT SUM(CAST({rev_col} AS DOUBLE)), SUM(CAST({profit_col} AS DOUBLE))
                        FROM {dataset.table_name}
                    """).fetchone()
                    if tot_rev and tot_rev > 0:
                        margin_pct = (tot_profit / tot_rev) * 100.0
                        if margin_pct < 15.0:  # Under 15% margin trigger
                            alert = cls._create_or_deduplicate_alert(
                                db=db,
                                user_id=user.id,
                                dataset_id=dataset.id,
                                title="Gross Profit Margin Below Target Threshold",
                                category="profit",
                                severity="high" if margin_pct < 8.0 else "medium",
                                description=f"Blended gross profit margin stands at {margin_pct:.1f}%, which is below the target minimum operating baseline of 15.0%.",
                                evidence={"total_revenue": tot_rev, "total_profit": tot_profit, "margin_pct": round(margin_pct, 2)},
                                metric_name="gross_margin_pct",
                                observed_value=round(margin_pct, 2),
                                threshold_value=15.0
                            )
                            if alert:
                                created_alerts.append(alert)
                except Exception as e:
                    logger.warning(f"Margin alert rule failed: {e}")

            # Check 3: Regional Sales Asymmetry / Laggard territory
            reg_col = next((c for c in col_names if any(r in c.lower() for r in ["region", "territory", "zone"])), None)
            if reg_col and rev_col:
                try:
                    df_reg = conn.execute(f"""
                        SELECT {reg_col} AS reg, SUM(CAST({rev_col} AS DOUBLE)) AS rev
                        FROM {dataset.table_name}
                        WHERE {reg_col} IS NOT NULL
                        GROUP BY reg
                        ORDER BY rev DESC
                    """).df()
                    if len(df_reg) >= 2:
                        tot_reg_rev = df_reg["rev"].sum()
                        lowest_row = df_reg.iloc[-1]
                        lowest_share = (lowest_row["rev"] / tot_reg_rev) * 100.0
                        if lowest_share < 8.0:
                            alert = cls._create_or_deduplicate_alert(
                                db=db,
                                user_id=user.id,
                                dataset_id=dataset.id,
                                title=f"Territory Underperformance: {lowest_row['reg']}",
                                category="regional",
                                severity="low",
                                description=f"The {lowest_row['reg']} territory generated only {lowest_share:.1f}% ({format_val(lowest_row['rev'], 'currency')}) of total regional sales volume.",
                                evidence={"region": str(lowest_row["reg"]), "revenue": float(lowest_row["rev"]), "share_pct": round(lowest_share, 2)},
                                metric_name="regional_share_min",
                                observed_value=round(lowest_share, 2),
                                threshold_value=8.0
                            )
                            if alert:
                                created_alerts.append(alert)
                except Exception as e:
                    logger.warning(f"Regional alert check failed: {e}")

        finally:
            conn.close()

        db.commit()
        return created_alerts

    @classmethod
    def _create_or_deduplicate_alert(
        cls,
        db: Session,
        user_id: str,
        dataset_id: str,
        title: str,
        category: str,
        severity: str,
        description: str,
        evidence: Dict[str, Any],
        metric_name: str,
        observed_value: float,
        threshold_value: float
    ) -> Optional[Alert]:
        """Prevent generating identical active alerts within a 24-hour deduplication window."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        existing = db.query(Alert).filter(
            Alert.user_id == user_id,
            Alert.dataset_id == dataset_id,
            Alert.metric_name == metric_name,
            Alert.is_resolved == False,
            Alert.created_at >= cutoff
        ).first()

        if existing:
            return None  # Suppress duplicate

        alert = Alert(
            user_id=user_id,
            dataset_id=dataset_id,
            title=title,
            category=category,
            severity=severity,
            description=description,
            evidence_json=json.dumps(evidence),
            metric_name=metric_name,
            observed_value=observed_value,
            threshold_value=threshold_value,
            is_read=False,
            is_resolved=False
        )
        db.add(alert)
        db.flush()
        try:
            from app.services.notification_service import NotificationService
            NotificationService.create_notification(
                db=db,
                user_id=user_id,
                category="alert",
                title=f"Business Alert: {title}",
                message=description,
                resource_type="alert",
                resource_id=alert.id,
                dedup_key=f"alert:{dataset_id}:{metric_name}",
            )
        except Exception:
            pass
        return alert

    @classmethod
    def create_default_rules(cls, db: Session, user: User, dataset_id: Optional[str] = None):
        """Seed baseline corporate alert triggers for new users."""
        default_rules = [
            {"name": "Revenue Drop Alarm", "metric": "monthly_revenue_drop", "cond": "greater_than", "thresh": 15.0, "cat": "revenue", "sev": "high"},
            {"name": "Minimum Margin Guard", "metric": "gross_margin_pct", "cond": "less_than", "thresh": 15.0, "cat": "profit", "sev": "high"},
            {"name": "Territory Lag Warning", "metric": "regional_share_min", "cond": "less_than", "thresh": 8.0, "cat": "regional", "sev": "low"},
        ]
        for r in default_rules:
            rule = AlertRule(
                user_id=user.id,
                dataset_id=dataset_id,
                name=r["name"],
                metric_name=r["metric"],
                condition=r["cond"],
                threshold_value=r["thresh"],
                category=r["cat"],
                severity=r["sev"],
                is_active=True
            )
            db.add(rule)
        db.commit()

    @classmethod
    def list_alerts(
        cls,
        db: Session,
        user_id: str,
        dataset_id: Optional[str] = None,
        is_resolved: Optional[bool] = None,
        severity: Optional[str] = None
    ) -> List[Alert]:
        """Fetch alert feed filtered by user and criteria."""
        q = db.query(Alert).filter(Alert.user_id == user_id)
        if dataset_id:
            q = q.filter(Alert.dataset_id == dataset_id)
        if is_resolved is not None:
            q = q.filter(Alert.is_resolved == is_resolved)
        if severity:
            q = q.filter(Alert.severity == severity.lower())
        return q.order_by(Alert.created_at.desc()).all()

    @classmethod
    def mark_read(cls, db: Session, user_id: str, alert_id: str) -> Optional[Alert]:
        """Mark an alert as read."""
        alert = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == user_id).first()
        if alert:
            alert.is_read = True
            db.commit()
            db.refresh(alert)
        return alert

    @classmethod
    def resolve_alert(cls, db: Session, user_id: str, alert_id: str) -> Optional[Alert]:
        """Mark an alert as resolved."""
        alert = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == user_id).first()
        if alert:
            alert.is_resolved = True
            db.commit()
            db.refresh(alert)
        return alert
