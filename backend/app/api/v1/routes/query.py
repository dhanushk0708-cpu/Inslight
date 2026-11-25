from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.rate_limit import limit_ai_requests
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.query import QueryRequest, QueryResponse
from app.services.query_service import QueryService
from app.services.audit_service import AuditService

router = APIRouter(tags=["Query"])


@router.post("/query", response_model=QueryResponse, dependencies=[Depends(limit_ai_requests)])
async def execute_query(
    req: QueryRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Execute natural-language business intelligence query on user's dataset.
    """
    res = await QueryService.process_user_query(
        db=db,
        user=user,
        question=req.question,
        dataset_id=req.dataset_id,
        session_id=req.session_id,
        conversation_history=req.conversation_history
    )
    AuditService.log_action(
        db=db,
        user_id=user.id,
        action="ai_query",
        resource_type="dataset",
        resource_id=req.dataset_id,
        status="failure" if res.get("error") else "success",
        metadata={"question_length": len(req.question or "")},
    )
    return res
