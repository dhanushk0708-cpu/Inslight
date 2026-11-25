import os
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.dataset import Dataset


class DatasetRepository:
    @staticmethod
    def create(
        db: Session,
        user_id: str,
        original_filename: str,
        table_name: str,
        storage_path: str,
        row_count: int,
        column_count: int,
        schema_metadata: str
    ) -> Dataset:
        dataset = Dataset(
            user_id=user_id,
            original_filename=original_filename,
            table_name=table_name,
            storage_path=storage_path,
            row_count=row_count,
            column_count=column_count,
            schema_metadata=schema_metadata
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        return dataset

    @staticmethod
    def get_by_id(db: Session, dataset_id: str, user_id: Optional[str] = None) -> Optional[Dataset]:
        """Fetch dataset by ID, optionally validating user ownership."""
        query = db.query(Dataset).filter(Dataset.id == dataset_id)
        if user_id:
            query = query.filter(Dataset.user_id == user_id)
        return query.first()

    @staticmethod
    def get_user_datasets(db: Session, user_id: str) -> List[Dataset]:
        return db.query(Dataset).filter(Dataset.user_id == user_id).order_by(Dataset.created_at.desc()).all()

    @staticmethod
    def get_latest_for_user(db: Session, user_id: str) -> Optional[Dataset]:
        return db.query(Dataset).filter(Dataset.user_id == user_id).order_by(Dataset.created_at.desc()).first()

    @staticmethod
    def get_active(db: Session, user_id: str) -> Optional[Dataset]:
        return DatasetRepository.get_latest_for_user(db, user_id=user_id)

    @staticmethod
    def delete(db: Session, dataset_id: str, user_id: str) -> bool:
        """Delete dataset ensuring ownership check."""
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.user_id == user_id).first()
        if not dataset:
            return False

        # Remove physical file if present
        if dataset.storage_path and os.path.exists(dataset.storage_path):
            try:
                os.remove(dataset.storage_path)
            except Exception:
                pass

        db.delete(dataset)
        db.commit()
        return True
