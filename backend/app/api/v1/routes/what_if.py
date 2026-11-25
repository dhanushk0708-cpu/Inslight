from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.repositories.dataset_repository import DatasetRepository
from app.services.dataset_service import DatasetService
from app.analytics.scenario_engine import ScenarioEngine
from app.schemas.analytics import WhatIfRequest, WhatIfResponse

router = APIRouter(tags=["What-If"])


@router.post("/what-if", response_model=WhatIfResponse)
async def what_if(
    req: WhatIfRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Run what-if price, discount, and volume sensitivity simulation."""
    dataset = None
    if req.dataset_id:
        dataset = DatasetRepository.get_by_id(db, dataset_id=req.dataset_id, user_id=user.id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found or access denied.")
    else:
        dataset = DatasetRepository.get_latest_for_user(db, user_id=user.id)

    if not dataset:
        seed = DatasetService.load_seed_for_user(db, user_id=user.id)
        if seed:
            dataset, _ = seed
        else:
            raise HTTPException(status_code=404, detail="No dataset loaded. Upload a CSV first.")

    res = await ScenarioEngine.simulate(
        dataset=dataset,
        price_change=req.price_change,
        discount_change=req.discount_change,
        units_change=req.units_change
    )
    return WhatIfResponse(**res)
