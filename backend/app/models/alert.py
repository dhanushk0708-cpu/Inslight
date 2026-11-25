import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False, default="general")  # revenue, profit, regional, product, anomaly
    severity = Column(String(20), nullable=False, default="medium")  # high, medium, low, info
    description = Column(Text, nullable=False)
    evidence_json = Column(Text, nullable=True)  # JSON string of contributing factors/numbers
    metric_name = Column(String(100), nullable=True)
    observed_value = Column(Float, nullable=True)
    threshold_value = Column(Float, nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    is_resolved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="alerts")
    dataset = relationship("Dataset")


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(150), nullable=False)
    metric_name = Column(String(100), nullable=False)  # e.g. revenue_drop_pct, margin_min_pct, anomaly_severity
    condition = Column(String(30), nullable=False)  # less_than, greater_than, drop_pct, spike_pct
    threshold_value = Column(Float, nullable=False)
    category = Column(String(50), default="business_rule")
    severity = Column(String(20), default="high")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="alert_rules")
    dataset = relationship("Dataset")
