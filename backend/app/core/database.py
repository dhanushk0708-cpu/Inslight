import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

db_url = settings.DATABASE_URL
connect_args = {}

if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

try:
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        pool_pre_ping=True
    )
    # Test connection
    with engine.connect() as conn:
        pass
except Exception as e:
    # If remote/configured DB fails (e.g. postgres bad credentials), fallback gracefully to persistent SQLite
    print(f"[WARN] Failed to connect to primary DATABASE_URL ({db_url}): {e}")
    print("[INFO] Falling back to persistent SQLite at sqlite:///./data/inslight.db")
    fallback_url = "sqlite:///./data/inslight.db"
    engine = create_engine(
        fallback_url,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI Dependency for database session management."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all database tables on startup."""
    from app.models.user import User  # noqa
    from app.models.dataset import Dataset  # noqa
    from app.models.chat import ChatSession, ChatMessage  # noqa
    from app.models.report import Report, ScheduledReport  # noqa
    from app.models.oauth import OAuthCredential  # noqa
    from app.models.alert import Alert, AlertRule  # noqa
    from app.models.dashboard import SavedDashboard  # noqa
    from app.models.relationship import DatasetRelationship  # noqa
    from app.models.notification import Notification  # noqa
    from app.models.audit_log import AuditLog  # noqa
    from app.models.presentation import Presentation  # noqa
    Base.metadata.create_all(bind=engine)
