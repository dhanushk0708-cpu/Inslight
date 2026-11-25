import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="analyst", server_default="analyst")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    datasets = relationship("Dataset", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    scheduled_reports = relationship("ScheduledReport", back_populates="user", cascade="all, delete-orphan")
    oauth_credential = relationship("OAuthCredential", back_populates="user", uselist=False, cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    alert_rules = relationship("AlertRule", back_populates="user", cascade="all, delete-orphan")
    saved_dashboards = relationship("SavedDashboard", back_populates="user", cascade="all, delete-orphan")
    dataset_relationships = relationship("DatasetRelationship", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    presentations = relationship("Presentation", back_populates="user", cascade="all, delete-orphan")
