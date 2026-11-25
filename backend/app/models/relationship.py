import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class DatasetRelationship(Base):
    __tablename__ = "dataset_relationships"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    target_dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    source_column = Column(String(100), nullable=False)
    target_column = Column(String(100), nullable=False)
    relationship_type = Column(String(30), default="many_to_one", nullable=False)  # one_to_one, many_to_one, one_to_many
    cardinality_status = Column(String(50), default="verified", nullable=False)
    metadata_json = Column(Text, nullable=True)  # preview stats, duplicate warnings
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="dataset_relationships")
    source_dataset = relationship("Dataset", foreign_keys=[source_dataset_id])
    target_dataset = relationship("Dataset", foreign_keys=[target_dataset_id])
