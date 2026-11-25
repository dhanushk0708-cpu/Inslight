from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class ReportGenerateRequest(BaseModel):
    dataset_id: Optional[str] = None
    title: str = Field(default="Executive Business Performance Report", max_length=200)
    report_format: str = Field(default="pdf", pattern="^(pdf|excel|csv)$")
    report_type: Optional[str] = Field(default="executive", pattern="^(executive|sales|financial|operational|detailed)$")
    include_anomalies: bool = True
    include_kpis: bool = True
    custom_query_data: Optional[Dict[str, Any]] = None


class ReportResponse(BaseModel):
    id: str
    user_id: str
    dataset_id: Optional[str] = None
    name: str
    report_format: str
    file_size: int
    recipients: Optional[str] = None
    email_subject: Optional[str] = None
    status: str
    gmail_message_id: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EmailSendRequest(BaseModel):
    report_id: str
    recipients: List[str]
    cc_recipients: Optional[List[str]] = None
    subject: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1)


class EmailSendResponse(BaseModel):
    status: str
    message: str
    gmail_message_id: Optional[str] = None
    recipients: List[str]
    delivered_at: datetime


class ScheduledReportCreateRequest(BaseModel):
    dataset_id: str
    report_name: str = Field(..., min_length=1, max_length=255)
    frequency: str = Field(default="weekly", pattern="^(weekly|monthly)$")
    report_format: str = Field(default="pdf", pattern="^(pdf|excel|both)$")
    recipients: List[str]
    email_subject: str = Field(..., min_length=1, max_length=255)
    email_body: str = Field(..., min_length=1)
    is_active: bool = True


class ScheduledReportUpdateRequest(BaseModel):
    report_name: Optional[str] = None
    frequency: Optional[str] = Field(None, pattern="^(weekly|monthly)$")
    report_format: Optional[str] = Field(None, pattern="^(pdf|excel|both)$")
    recipients: Optional[List[str]] = None
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    is_active: Optional[bool] = None


class ScheduledReportResponse(BaseModel):
    id: str
    user_id: str
    dataset_id: str
    report_name: str
    frequency: str
    report_format: str
    recipients: str
    email_subject: str
    email_body: str
    is_active: bool
    next_run_at: datetime
    last_run_at: Optional[datetime] = None
    last_status: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class GmailStatusResponse(BaseModel):
    is_connected: bool
    email: Optional[str] = None
    provider: str = "google"
