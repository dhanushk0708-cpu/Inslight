from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.repositories.dataset_repository import DatasetRepository
from app.services.dataset_service import DatasetService
from app.services.audit_service import AuditService
from app.analytics.insights import DeepDiveEngine
from app.schemas.analytics import DeepDiveResponse

router = APIRouter(tags=["Deep Dive"])


@router.post("/deep-dive", response_model=DeepDiveResponse)
async def deep_dive(
    refresh: bool = Query(default=False),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Run comprehensive 10-section deep dive analysis on active dataset."""
    dataset = DatasetRepository.get_latest_for_user(db, user_id=user.id)
    if not dataset:
        seed = DatasetService.load_seed_for_user(db, user_id=user.id)
        if seed:
            dataset, _ = seed
        else:
            raise HTTPException(status_code=404, detail="No dataset loaded. Upload a CSV first.")

    res = await DeepDiveEngine.analyze_dataset(dataset, refresh=refresh)
    AuditService.log_action(
        db=db,
        user_id=user.id,
        action="deep_dive_analysis",
        resource_type="dataset",
        resource_id=dataset.id,
        status="failure" if res.get("error") else "success",
        metadata={"refresh": refresh, "filename": dataset.original_filename},
    )
    return DeepDiveResponse(**res)
