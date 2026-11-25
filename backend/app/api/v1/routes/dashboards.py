from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.repositories.dataset_repository import DatasetRepository
from app.services.dataset_service import DatasetService
from app.schemas.phase3 import (
    DashboardGenerateRequest,
    DashboardSaveRequest,
    DashboardUpdateRequest,
    DashboardResponse,
)
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboards", tags=["Dashboard Studio & Saved Dashboards"])


@router.post("/generate")
async def generate_dashboard(
    req: DashboardGenerateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Synthesize an interactive business dashboard from natural language with live queries.
    """
    dataset = DatasetRepository.get_active(db, user_id=user.id)
    if req.dataset_id:
        dataset = DatasetRepository.get_by_id(db, req.dataset_id, user_id=user.id)

    if not dataset:
        raise HTTPException(status_code=400, detail="No active dataset available.")

    conn = DatasetService.get_duckdb_connection(dataset.storage_path, read_only=True)
    try:
        return await DashboardService.build_dashboard_from_prompt(
            conn=conn,
            table_name=dataset.table_name,
            user_prompt=req.prompt,
            dataset_name=dataset.original_filename
        )
    finally:
        conn.close()


@router.get("", response_model=List[DashboardResponse])
def list_dashboards(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List all saved dashboards owned by user."""
    return DashboardService.list_dashboards(db, user_id=user.id)


@router.post("", response_model=DashboardResponse)
def save_dashboard(
    req: DashboardSaveRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Save dashboard configuration."""
    return DashboardService.save_dashboard(
        db=db,
        user_id=user.id,
        title=req.title,
        description=req.description,
        layout_config=req.layout_config,
        dataset_id=req.dataset_id
    )


@router.get("/{dashboard_id}", response_model=DashboardResponse)
def get_dashboard(
    dashboard_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    dash = DashboardService.get_dashboard(db, user_id=user.id, dashboard_id=dashboard_id)
    if not dash:
        raise HTTPException(status_code=404, detail="Dashboard not found or access denied.")
    return dash


@router.put("/{dashboard_id}", response_model=DashboardResponse)
def update_dashboard(
    dashboard_id: str,
    req: DashboardUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    dash = DashboardService.update_dashboard(
        db=db,
        user_id=user.id,
        dashboard_id=dashboard_id,
        title=req.title,
        description=req.description,
        layout_config=req.layout_config,
        is_favorite=req.is_favorite
    )
    if not dash:
        raise HTTPException(status_code=404, detail="Dashboard not found.")
    return dash


@router.post("/{dashboard_id}/duplicate", response_model=DashboardResponse)
def duplicate_dashboard(
    dashboard_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    dash = DashboardService.duplicate_dashboard(db, user_id=user.id, dashboard_id=dashboard_id)
    if not dash:
        raise HTTPException(status_code=404, detail="Dashboard not found.")
    return dash


@router.delete("/{dashboard_id}")
def delete_dashboard(
    dashboard_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    success = DashboardService.delete_dashboard(db, user_id=user.id, dashboard_id=dashboard_id)
    if not success:
        raise HTTPException(status_code=404, detail="Dashboard not found.")
    return {"status": "success", "message": "Dashboard deleted."}
