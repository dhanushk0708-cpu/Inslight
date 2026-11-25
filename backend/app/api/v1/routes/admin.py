from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db, engine
from app.api.deps import require_admin
from app.models.user import User
from app.models.dataset import Dataset
from app.models.report import Report
from app.models.notification import Notification
from app.models.audit_log import AuditLog
from app.schemas.phase4 import (
    AdminUserResponse,
    UserRoleUpdateRequest,
    UserStatusUpdateRequest,
    AuditLogPageResponse,
)
from app.services.audit_service import AuditService

router = APIRouter(prefix="/admin", tags=["Admin & RBAC"])


@router.get("/users", response_model=List[AdminUserResponse])
def list_users(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """List all registered user accounts (Admin only)."""
    return db.query(User).order_by(User.created_at.desc()).offset(offset).limit(limit).all()


@router.patch("/users/{user_id}/role", response_model=AdminUserResponse)
def update_user_role(
    user_id: str,
    req: UserRoleUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Assign or update a user's RBAC role (Admin only; prevents self-demotion)."""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")

    if target.id == admin.id and req.role != "admin":
        raise HTTPException(status_code=400, detail="Administrators cannot demote themselves.")

    old_role = target.role
    target.role = req.role
    db.commit()
    db.refresh(target)

    AuditService.log_action(
        db=db,
        user_id=admin.id,
        action="role_change",
        resource_type="user",
        resource_id=target.id,
        status="success",
        metadata={"previous_role": old_role, "new_role": req.role, "target_email": target.email},
    )
    return target


@router.patch("/users/{user_id}/status", response_model=AdminUserResponse)
def update_user_status(
    user_id: str,
    req: UserStatusUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Activate or deactivate a user account (Admin only; prevents self-deactivation)."""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")

    if target.id == admin.id and not req.is_active:
        raise HTTPException(status_code=400, detail="Administrators cannot deactivate their own account.")

    target.is_active = req.is_active
    db.commit()
    db.refresh(target)

    AuditService.log_action(
        db=db,
        user_id=admin.id,
        action="user_status_change",
        resource_type="user",
        resource_id=target.id,
        status="success",
        metadata={"is_active": req.is_active, "target_email": target.email},
    )
    return target


@router.get("/audit-logs", response_model=AuditLogPageResponse)
def get_audit_logs(
    action: Optional[str] = Query(default=None),
    resource_type: Optional[str] = Query(default=None),
    user_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Retrieve paginated security and activity audit logs (Admin only)."""
    total, items = AuditService.list_logs(
        db=db,
        action=action,
        resource_type=resource_type,
        user_id=user_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return AuditLogPageResponse(total=total, limit=limit, offset=offset, items=items)


@router.get("/system-status")
def get_system_status(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Return sanitized system-level operational counts (Admin only; no secrets exposed)."""
    return {
        "status": "operational",
        "database_dialect": engine.dialect.name,
        "counts": {
            "users": db.query(User).count(),
            "datasets": db.query(Dataset).count(),
            "reports": db.query(Report).count(),
            "notifications": db.query(Notification).count(),
            "audit_logs": db.query(AuditLog).count(),
        },
    }
