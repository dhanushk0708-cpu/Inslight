import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.rate_limit import limit_ai_requests
from app.api.deps import get_current_user
from app.models.user import User
from app.models.presentation import Presentation
from app.repositories.dataset_repository import DatasetRepository
from app.schemas.phase4 import (
    PresentationOutlineRequest,
    PresentationOutlineResponse,
    PresentationGenerateRequest,
    PresentationResponse,
)
from app.services.presentation_service import PresentationService, SUPPORTED_PRESENTATION_TYPES
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/presentations", tags=["AI PowerPoint Generator"])


@router.get("/types")
def get_presentation_types(user: User = Depends(get_current_user)):
    """List supported AI business presentation types."""
    return {"types": SUPPORTED_PRESENTATION_TYPES}


@router.post("/outline", response_model=PresentationOutlineResponse, dependencies=[Depends(limit_ai_requests)])
async def generate_presentation_outline(
    req: PresentationOutlineRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Analyze the selected dataset and generate an editable slide outline."""
    dataset = (
        DatasetRepository.get_by_id(db, req.dataset_id, user_id=user.id)
        if req.dataset_id
        else DatasetRepository.get_active(db, user_id=user.id)
    )
    if not dataset:
        raise HTTPException(status_code=400, detail="No active dataset loaded. Upload a CSV first.")

    try:
        return await PresentationService.generate_outline(
            dataset=dataset,
            prompt=req.prompt,
            presentation_type=req.presentation_type,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.post("/generate", response_model=PresentationResponse)
def generate_presentation_file(
    req: PresentationGenerateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Build and persist a downloadable .pptx file from the user-approved slide outline."""
    dataset = (
        DatasetRepository.get_by_id(db, req.dataset_id, user_id=user.id)
        if req.dataset_id
        else DatasetRepository.get_active(db, user_id=user.id)
    )
    if not dataset:
        raise HTTPException(status_code=400, detail="No active dataset loaded. Upload a CSV first.")

    record = PresentationService.generate_pptx(
        db=db,
        user=user,
        dataset=dataset,
        title=req.title,
        presentation_type=req.presentation_type,
        slides=[s.model_dump() for s in req.slides],
    )
    AuditService.log_action(
        db=db,
        user_id=user.id,
        action="pptx_generate",
        resource_type="presentation",
        resource_id=record.id,
        status="success",
        metadata={"title": record.title, "slide_count": record.slide_count},
    )
    NotificationService.create_notification(
        db=db,
        user_id=user.id,
        category="report",
        title=f"Presentation Ready: {record.title}",
        message=f"PowerPoint deck '{record.title}' ({record.slide_count} slides) is ready to download.",
        resource_type="presentation",
        resource_id=record.id,
    )
    return record


@router.get("", response_model=List[PresentationResponse])
def list_presentations(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List PowerPoint presentations belonging to the authenticated user."""
    return (
        db.query(Presentation)
        .filter(Presentation.user_id == user.id)
        .order_by(Presentation.created_at.desc())
        .all()
    )


@router.get("/{presentation_id}/download")
def download_presentation(
    presentation_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Download a generated .pptx presentation with strict ownership validation."""
    record = (
        db.query(Presentation)
        .filter(Presentation.id == presentation_id, Presentation.user_id == user.id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Presentation not found or access denied.")
    if not os.path.exists(record.file_path):
        raise HTTPException(status_code=404, detail="Presentation file not found on disk.")

    safe_name = record.title.replace(" ", "_").replace("/", "_")
    return FileResponse(
        path=record.file_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=f"{safe_name}.pptx",
    )


@router.delete("/{presentation_id}")
def delete_presentation(
    presentation_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a presentation from DB and disk (ownership enforced)."""
    record = (
        db.query(Presentation)
        .filter(Presentation.id == presentation_id, Presentation.user_id == user.id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Presentation not found or access denied.")
    if os.path.exists(record.file_path):
        try:
            os.remove(record.file_path)
        except Exception:
            pass
    db.delete(record)
    db.commit()
    return {"status": "success", "message": "Presentation deleted."}
