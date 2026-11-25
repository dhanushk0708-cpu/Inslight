from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import duckdb
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.repositories.dataset_repository import DatasetRepository
from app.services.dataset_service import DatasetService
from app.schemas.phase3 import RCARequest
from app.services.root_cause_service import RootCauseService

router = APIRouter(prefix="/analytics/rca", tags=["Root Cause Analysis"])


@router.post("")
def run_root_cause_analysis(
    req: RCARequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Investigate why a business metric changed across periods and segments.
    """
    dataset = DatasetRepository.get_active(db, user_id=user.id)
    if req.dataset_id:
        dataset = DatasetRepository.get_by_id(db, req.dataset_id, user_id=user.id)

    if not dataset:
        raise HTTPException(status_code=400, detail="No active dataset available.")

    conn = DatasetService.get_duckdb_connection(dataset.storage_path, read_only=True)
    try:
        res = RootCauseService.analyze_root_cause(
            conn=conn,
            table_name=dataset.table_name,
            target_metric=req.target_metric,
            date_col=req.date_col,
            dimension_col=req.dimension_col
        )
        return res
    finally:
        conn.close()
