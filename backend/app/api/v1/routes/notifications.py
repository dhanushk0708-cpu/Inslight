from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.phase4 import NotificationResponse, UnreadCountResponse
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=List[NotificationResponse])
def list_notifications(
    category: Optional[str] = Query(default=None),
    unread_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List notifications belonging to the authenticated user."""
    return NotificationService.list_for_user(
        db=db,
        user_id=user.id,
        category=category,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return unread notification count for the authenticated user."""
    return UnreadCountResponse(unread_count=NotificationService.get_unread_count(db, user.id))


@router.patch("/read-all")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Mark all notifications as read for the authenticated user."""
    updated = NotificationService.mark_all_read(db, user.id)
    return {"status": "success", "updated_count": updated}


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Mark a single notification as read (ownership enforced)."""
    notif = NotificationService.mark_read(db, notification_id=notification_id, user_id=user.id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found or access denied.")
    return notif


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a single notification (ownership enforced)."""
    ok = NotificationService.delete_notification(db, notification_id=notification_id, user_id=user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="Notification not found or access denied.")
    return {"status": "success", "message": "Notification deleted."}
