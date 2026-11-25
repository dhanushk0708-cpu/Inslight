from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.repositories.dataset_repository import DatasetRepository
from app.services.dataset_service import DatasetService
from app.schemas.phase3 import ComparisonRequest
from app.services.comparison_service import ComparisonService

router = APIRouter(prefix="/analytics/compare", tags=["Comparative Analytics"])


@router.post("")
def run_comparative_analysis(
    req: ComparisonRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Period-over-period (MoM, QoQ) or dimension benchmark (Region vs Region, Segment vs Segment).
    """
    dataset = DatasetRepository.get_active(db, user_id=user.id)
    if req.dataset_id:
        dataset = DatasetRepository.get_by_id(db, req.dataset_id, user_id=user.id)

    if not dataset:
        raise HTTPException(status_code=400, detail="No active dataset available.")

    conn = DatasetService.get_duckdb_connection(dataset.storage_path, read_only=True)
    try:
        return ComparisonService.compare_periods_or_segments(
            conn=conn,
            table_name=dataset.table_name,
            comparison_mode=req.comparison_mode,
            target_metric=req.target_metric,
            dimension_col=req.dimension_col,
            segment_a=req.segment_a,
            segment_b=req.segment_b
        )
    finally:
        conn.close()
