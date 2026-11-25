from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.repositories.dataset_repository import DatasetRepository
from app.services.dataset_service import DatasetService
from app.schemas.phase3 import DataQualityAuditResponse
from app.services.data_quality_service import DataQualityService

router = APIRouter(prefix="/datasets", tags=["Data Quality Assistant"])


@router.post("/{dataset_id}/quality", response_model=DataQualityAuditResponse)
def audit_dataset_quality(
    dataset_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Diagnose tabular hygiene (missing values, duplicates, format issues, casing, outliers).
    """
    dataset = DatasetRepository.get_by_id(db, dataset_id, user_id=user.id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found or access denied.")

    conn = DatasetService.get_duckdb_connection(dataset.storage_path, read_only=True)
    try:
        return DataQualityService.audit_dataset_quality(conn, dataset.table_name)
    finally:
        conn.close()


@router.get("/{dataset_id}/quality/preview")
def preview_cleaned_dataset(
    dataset_id: str,
    limit: int = 15,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Non-destructive preview of sanitized records without altering original data on disk.
    """
    dataset = DatasetRepository.get_by_id(db, dataset_id, user_id=user.id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    conn = DatasetService.get_duckdb_connection(dataset.storage_path, read_only=True)
    try:
        return DataQualityService.generate_cleaned_preview(conn, dataset.table_name, limit=limit)
    finally:
        conn.close()
