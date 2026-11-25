from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.alert import AlertRule
from app.repositories.dataset_repository import DatasetRepository
from app.schemas.phase3 import AlertResponse, AlertRuleCreateRequest, AlertRuleResponse
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["Intelligent Business Alerts"])


@router.get("", response_model=List[AlertResponse])
def get_alerts(
    dataset_id: Optional[str] = None,
    is_resolved: Optional[bool] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Retrieve user alert feed."""
    return AlertService.list_alerts(db, user_id=user.id, dataset_id=dataset_id, is_resolved=is_resolved, severity=severity)


@router.post("/scan", response_model=List[AlertResponse])
def trigger_alert_scan(
    dataset_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Scan dataset against active rules and generate alerts."""
    dataset = DatasetRepository.get_active(db, user_id=user.id)
    if dataset_id:
        dataset = DatasetRepository.get_by_id(db, dataset_id, user_id=user.id)

    if not dataset:
        raise HTTPException(status_code=400, detail="No active dataset available.")

    return AlertService.evaluate_and_generate_alerts(db=db, user=user, dataset=dataset)


@router.patch("/{alert_id}/read", response_model=AlertResponse)
def mark_alert_read(
    alert_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    alert = AlertService.mark_read(db, user_id=user.id, alert_id=alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    return alert


@router.patch("/{alert_id}/resolve", response_model=AlertResponse)
def mark_alert_resolved(
    alert_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    alert = AlertService.resolve_alert(db, user_id=user.id, alert_id=alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    return alert


@router.get("/rules", response_model=List[AlertRuleResponse])
def get_rules(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return db.query(AlertRule).filter(AlertRule.user_id == user.id).all()


@router.post("/rules", response_model=AlertRuleResponse)
def create_rule(
    req: AlertRuleCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    rule = AlertRule(
        user_id=user.id,
        dataset_id=req.dataset_id,
        name=req.name,
        metric_name=req.metric_name,
        condition=req.condition,
        threshold_value=req.threshold_value,
        category=req.category or "business_rule",
        severity=req.severity or "high",
        is_active=True
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/rules/{rule_id}")
def delete_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    rule = db.query(AlertRule).filter(AlertRule.id == rule_id, AlertRule.user_id == user.id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found.")
    db.delete(rule)
    db.commit()
    return {"status": "success", "message": "Alert rule deleted."}
