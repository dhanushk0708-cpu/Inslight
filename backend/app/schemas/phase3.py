from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


# ━━━ 1. BI AGENT SCHEMAS ━━━
class BIAgentRequest(BaseModel):
    dataset_id: Optional[str] = None
    question: str
    history: Optional[List[Dict[str, str]]] = None


class OpportunityItem(BaseModel):
    rank: int
    title: str
    is_hypothesis: bool = False
    supporting_metric: str = ""
    actual_value: str = ""
    evidence_source: str = ""
    business_interpretation: str = ""
    impact: str
    recommendation: str


class RiskItem(BaseModel):
    rank: int
    title: str
    severity: str  # critical, warning, info
    supporting_metric: str = ""
    actual_value: str = ""
    evidence_source: str = ""
    business_interpretation: str = ""
    impact: str
    mitigation: str


class BIAgentResponse(BaseModel):
    status: str
    tool_used: str
    answer: str
    summary: Optional[str] = None
    reasoning_steps: List[str] = []
    analytical_steps: Optional[List[str]] = None
    evidence: Optional[Any] = None
    kpi_results: Optional[List[Dict[str, Any]]] = None
    opportunities: Optional[List[OpportunityItem]] = None
    risks: Optional[List[RiskItem]] = None
    charts: Optional[Dict[str, Any]] = None
    supporting_table: Optional[Dict[str, Any]] = None
    dataset_metadata: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    suggested_follow_ups: List[str] = []


# ━━━ 2. ROOT CAUSE SCHEMAS ━━━
class RCARequest(BaseModel):
    dataset_id: Optional[str] = None
    target_metric: Optional[str] = None
    date_col: Optional[str] = None
    dimension_col: Optional[str] = None


# ━━━ 3. FORECASTING SCHEMAS ━━━
class ForecastRequest(BaseModel):
    dataset_id: Optional[str] = None
    target_metric: Optional[str] = None
    date_col: Optional[str] = None
    horizon: int = 30
    method: str = "auto"  # auto, moving_average, exponential_smoothing, linear_regression, random_forest


# ━━━ 4. ANOMALIES SCHEMAS ━━━
class AnomalyScanRequest(BaseModel):
    dataset_id: Optional[str] = None
    methods: Optional[List[str]] = None


# ━━━ 5. ALERTS SCHEMAS ━━━
class AlertResponse(BaseModel):
    id: str
    user_id: str
    dataset_id: Optional[str] = None
    title: str
    category: str
    severity: str
    description: str
    evidence_json: Optional[str] = None
    metric_name: Optional[str] = None
    observed_value: Optional[float] = None
    threshold_value: Optional[float] = None
    is_read: bool
    is_resolved: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertRuleCreateRequest(BaseModel):
    dataset_id: Optional[str] = None
    name: str
    metric_name: str
    condition: str
    threshold_value: float
    category: Optional[str] = "business_rule"
    severity: Optional[str] = "high"


class AlertRuleResponse(BaseModel):
    id: str
    user_id: str
    dataset_id: Optional[str] = None
    name: str
    metric_name: str
    condition: str
    threshold_value: float
    category: str
    severity: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ━━━ 6. DATA QUALITY SCHEMAS ━━━
class DataQualityAuditResponse(BaseModel):
    status: str
    overall_score: int
    quality_grade: str
    total_records_analyzed: int
    total_columns_analyzed: int
    issues_count: int
    issues: List[Dict[str, Any]]
    cleaning_actions: List[Dict[str, Any]]
    governance_summary: str


# ━━━ 7. COMPARISONS SCHEMAS ━━━
class ComparisonRequest(BaseModel):
    dataset_id: Optional[str] = None
    comparison_mode: str = "period"  # "period" or "segment"
    target_metric: Optional[str] = None
    dimension_col: Optional[str] = None
    segment_a: Optional[str] = None
    segment_b: Optional[str] = None


# ━━━ 8. DASHBOARD SCHEMAS ━━━
class DashboardGenerateRequest(BaseModel):
    dataset_id: Optional[str] = None
    prompt: str


class DashboardSaveRequest(BaseModel):
    dataset_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    layout_config: Dict[str, Any]


class DashboardUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    layout_config: Optional[Dict[str, Any]] = None
    is_favorite: Optional[bool] = None


class DashboardResponse(BaseModel):
    id: str
    user_id: str
    dataset_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    layout_config: str
    is_favorite: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ━━━ 9. DATASET RELATIONSHIP SCHEMAS ━━━
class RelationshipCandidatesRequest(BaseModel):
    source_dataset_id: str
    target_dataset_id: str


class RelationshipValidateRequest(BaseModel):
    source_dataset_id: str
    target_dataset_id: str
    source_column: str
    target_column: str


class RelationshipCreateRequest(BaseModel):
    source_dataset_id: str
    target_dataset_id: str
    source_column: str
    target_column: str
    relationship_type: str = "many_to_one"


class RelationshipPreviewRequest(BaseModel):
    source_dataset_id: str
    target_dataset_id: str
    source_column: str
    target_column: str
    limit: int = 10


class RelationshipResponse(BaseModel):
    id: str
    user_id: str
    source_dataset_id: str
    target_dataset_id: str
    source_column: str
    target_column: str
    relationship_type: str
    cardinality_status: str
    source_dataset_name: Optional[str] = None
    target_dataset_name: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
