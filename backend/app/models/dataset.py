import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    table_name = Column(String(100), nullable=False)
    storage_path = Column(String(500), nullable=False)
    row_count = Column(Integer, default=0)
    column_count = Column(Integer, default=0)
    schema_metadata = Column(Text, nullable=True)  # JSON-encoded column and profile details
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="datasets")
    chat_sessions = relationship("ChatSession", back_populates="dataset")
