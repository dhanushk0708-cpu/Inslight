from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.notification import Notification


class NotificationService:
    """User-isolated persistent Notification Center service with 24h deduplication."""

    @staticmethod
    def create_notification(
        db: Session,
        user_id: str,
        category: str,
        title: str,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        dedup_key: Optional[str] = None,
        dedup_hours: int = 24,
    ) -> Notification:
        if dedup_key:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=dedup_hours)
            existing = (
                db.query(Notification)
                .filter(
                    Notification.user_id == user_id,
                    Notification.dedup_key == dedup_key,
                    Notification.created_at >= cutoff,
                )
                .first()
            )
            if existing:
                return existing

        notif = Notification(
            user_id=user_id,
            category=category,
            title=title[:255],
            message=message,
            is_read=False,
            resource_type=resource_type,
            resource_id=resource_id,
            dedup_key=dedup_key,
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return notif

    @staticmethod
    def list_for_user(
        db: Session,
        user_id: str,
        category: Optional[str] = None,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Notification]:
        q = db.query(Notification).filter(Notification.user_id == user_id)
        if category and category != "all":
            q = q.filter(Notification.category == category)
        if unread_only:
            q = q.filter(Notification.is_read.is_(False))
        return q.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def get_unread_count(db: Session, user_id: str) -> int:
        return (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
            .count()
        )

    @staticmethod
    def mark_read(db: Session, notification_id: str, user_id: str) -> Optional[Notification]:
        notif = (
            db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
        )
        if not notif:
            return None
        notif.is_read = True
        db.commit()
        db.refresh(notif)
        return notif

    @staticmethod
    def mark_all_read(db: Session, user_id: str) -> int:
        updated = (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
            .update({"is_read": True}, synchronize_session=False)
        )
        db.commit()
        return updated

    @staticmethod
    def delete_notification(db: Session, notification_id: str, user_id: str) -> bool:
        notif = (
            db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
        )
        if not notif:
            return False
        db.delete(notif)
        db.commit()
        return True
