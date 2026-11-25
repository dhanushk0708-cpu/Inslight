import json
from typing import Any, Dict, Optional, Tuple, List
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.core.logging import request_id_ctx, logger

SENSITIVE_KEYS = {
    "password", "hashed_password", "token", "access_token", "refresh_token",
    "secret", "api_key", "authorization", "client_secret", "jwt"
}


def _sanitize_metadata(data: Any) -> Any:
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            if any(s in str(k).lower() for s in SENSITIVE_KEYS):
                cleaned[k] = "[REDACTED]"
            else:
                cleaned[k] = _sanitize_metadata(v)
        return cleaned
    if isinstance(data, list):
        return [_sanitize_metadata(item) for item in data[:20]]
    if isinstance(data, str) and len(data) > 500:
        return data[:500] + "..."
    return data


class AuditService:
    """Append-only security & activity audit log service."""

    @staticmethod
    def log_action(
        db: Session,
        action: str,
        resource_type: str,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        status: str = "success",
        metadata: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> Optional[AuditLog]:
        try:
            req_id = request_id or request_id_ctx.get("-")
            safe_meta = _sanitize_metadata(metadata) if metadata else None
            entry = AuditLog(
                user_id=user_id,
                action=action[:100],
                resource_type=resource_type[:50],
                resource_id=str(resource_id)[:64] if resource_id else None,
                status=status[:20],
                request_id=req_id[:64] if req_id else None,
                metadata_json=json.dumps(safe_meta, default=str) if safe_meta else None,
            )
            db.add(entry)
            db.commit()
            db.refresh(entry)
            return entry
        except Exception as e:
            logger.warning(f"Audit log write skipped: {e}")
            try:
                db.rollback()
            except Exception:
                pass
            return None

    @staticmethod
    def list_logs(
        db: Session,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[int, List[AuditLog]]:
        q = db.query(AuditLog)
        if action:
            q = q.filter(AuditLog.action == action)
        if resource_type:
            q = q.filter(AuditLog.resource_type == resource_type)
        if user_id:
            q = q.filter(AuditLog.user_id == user_id)
        if status:
            q = q.filter(AuditLog.status == status)
        total = q.count()
        items = q.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
        return total, items
