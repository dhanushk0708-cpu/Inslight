from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.repositories.dataset_repository import DatasetRepository
from app.services.dataset_service import DatasetService
from app.analytics.anomaly_detection import AnomalyDetector
from app.schemas.analytics import AnomalyResponse

router = APIRouter(tags=["Anomalies"])


@router.get("/anomalies", response_model=AnomalyResponse)
async def detect_anomalies(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Detect statistical outliers and notable revenue drops on active dataset."""
    dataset = DatasetRepository.get_latest_for_user(db, user_id=user.id)
    if not dataset:
        seed = DatasetService.load_seed_for_user(db, user_id=user.id)
        if seed:
            dataset, _ = seed
        else:
            raise HTTPException(status_code=404, detail="No dataset loaded. Upload a CSV first.")

    res = await AnomalyDetector.detect(dataset)
    return AnomalyResponse(**res)
