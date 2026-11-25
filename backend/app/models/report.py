import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    report_format = Column(String(20), nullable=False)  # pdf, excel, csv
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    parameters_json = Column(Text, nullable=True)  # JSON filters, executive summary, query data
    recipients = Column(String(500), nullable=True)  # Comma-separated emails if emailed
    email_subject = Column(String(255), nullable=True)
    status = Column(String(50), default="generated")  # generated, sent, failed
    gmail_message_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="reports")
    dataset = relationship("Dataset")


class ScheduledReport(Base):
    __tablename__ = "scheduled_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    report_name = Column(String(255), nullable=False)
    frequency = Column(String(20), nullable=False)  # weekly, monthly
    report_format = Column(String(20), default="pdf")  # pdf, excel, both
    recipients = Column(String(500), nullable=False)  # Comma-separated email addresses
    email_subject = Column(String(255), nullable=False)
    email_body = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    next_run_at = Column(DateTime, nullable=False)
    last_run_at = Column(DateTime, nullable=True)
    last_status = Column(String(50), default="pending")  # pending, success, failed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="scheduled_reports")
    dataset = relationship("Dataset")
