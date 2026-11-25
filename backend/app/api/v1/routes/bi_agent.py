from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.rate_limit import limit_ai_requests
from app.api.deps import get_current_user
from app.models.user import User
from app.repositories.dataset_repository import DatasetRepository
from app.schemas.phase3 import BIAgentRequest, BIAgentResponse
from app.services.bi_agent_service import BIAgentService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/agent", tags=["AI BI Agent"])


@router.post("/query", response_model=BIAgentResponse, dependencies=[Depends(limit_ai_requests)])
async def query_bi_agent(
    req: BIAgentRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Intelligent BI Agent: evaluates question, selects tool (Strategic, RCA, Forecast, Anomaly, SQL),
    and synthesizes grounded response with reasoning steps.
    """
    dataset = DatasetRepository.get_active(db, user_id=user.id)
    if req.dataset_id:
        dataset = DatasetRepository.get_by_id(db, req.dataset_id, user_id=user.id)

    if not dataset:
        raise HTTPException(status_code=400, detail="No active dataset loaded. Please upload a CSV first.")

    res = await BIAgentService.process_business_inquiry(
        db=db,
        user=user,
        dataset=dataset,
        question=req.question,
        conversation_history=req.history
    )
    AuditService.log_action(
        db=db,
        user_id=user.id,
        action="ai_agent_query",
        resource_type="dataset",
        resource_id=dataset.id,
        status="success" if res.get("status") != "error" else "failure",
        metadata={"tool_used": res.get("tool_used"), "status": res.get("status")},
    )
    return res
