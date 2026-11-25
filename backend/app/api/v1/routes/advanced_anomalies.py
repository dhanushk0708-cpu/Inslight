from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.repositories.dataset_repository import DatasetRepository
from app.services.dataset_service import DatasetService
from app.schemas.phase3 import AnomalyScanRequest
from app.services.advanced_anomaly_service import AdvancedAnomalyService

router = APIRouter(prefix="/analytics/advanced-anomalies", tags=["Advanced Anomaly Detection"])


@router.post("")
def scan_advanced_anomalies(
    req: AnomalyScanRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Multi-technique anomaly detection (Z-Score, IQR, Isolation Forest).
    """
    dataset = DatasetRepository.get_active(db, user_id=user.id)
    if req.dataset_id:
        dataset = DatasetRepository.get_by_id(db, req.dataset_id, user_id=user.id)

    if not dataset:
        raise HTTPException(status_code=400, detail="No active dataset available.")

    conn = DatasetService.get_duckdb_connection(dataset.storage_path, read_only=True)
    try:
        res = AdvancedAnomalyService.detect_anomalies(
            conn=conn,
            table_name=dataset.table_name,
            methods=req.methods
        )
        return res
    finally:
        conn.close()
