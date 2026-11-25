from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


# ━━━ NOTIFICATIONS ━━━
class NotificationResponse(BaseModel):
    id: str
    user_id: str
    category: str
    title: str
    message: str
    is_read: bool
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UnreadCountResponse(BaseModel):
    unread_count: int


# ━━━ AUDIT LOGS ━━━
class AuditLogResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    status: str
    request_id: Optional[str] = None
    metadata_json: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogPageResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[AuditLogResponse]


# ━━━ RBAC / ADMIN ━━━
class AdminUserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserRoleUpdateRequest(BaseModel):
    role: str = Field(..., pattern="^(admin|analyst)$")


class UserStatusUpdateRequest(BaseModel):
    is_active: bool


# ━━━ AI POWERPOINT GENERATOR ━━━
class SlideOutlineItem(BaseModel):
    slide_number: int
    title: str = Field(..., min_length=1, max_length=200)
    layout: str = "bullets"  # title, kpis, chart_bar, chart_pie, chart_line, bullets, opportunities, risks, conclusion
    bullets: List[str] = []
    metric_highlight: Optional[str] = None
    notes: Optional[str] = None


class PresentationOutlineRequest(BaseModel):
    dataset_id: Optional[str] = None
    prompt: str = Field(default="Create an executive business review presentation", min_length=3, max_length=500)
    presentation_type: str = Field(default="Executive Business Review")


class PresentationOutlineResponse(BaseModel):
    status: str
    dataset_id: str
    dataset_name: str
    title: str
    presentation_type: str
    slides: List[SlideOutlineItem]
    analytics_snapshot: Optional[Dict[str, Any]] = None


class PresentationGenerateRequest(BaseModel):
    dataset_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=200)
    presentation_type: str = "Executive Business Review"
    slides: List[SlideOutlineItem]


class PresentationResponse(BaseModel):
    id: str
    user_id: str
    dataset_id: Optional[str] = None
    title: str
    presentation_type: str
    slide_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
