import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.repositories.dataset_repository import DatasetRepository
from app.services.dataset_service import DatasetService

router = APIRouter(tags=["Profile"])


@router.get("/profile")
def get_profile(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Fetch profile of currently active user dataset."""
    dataset = DatasetRepository.get_latest_for_user(db, user_id=user.id)
    if not dataset:
        seed = DatasetService.load_seed_for_user(db, user_id=user.id)
        if seed:
            dataset, profile = seed
            return profile
        raise HTTPException(status_code=404, detail="No dataset loaded. Upload a CSV first.")

    profile = json.loads(dataset.schema_metadata) if dataset.schema_metadata else {}
    profile["id"] = dataset.id
    return profile
