from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    dataset_id: Optional[str] = None
    session_id: Optional[str] = None
    conversation_history: Optional[List[Dict[str, str]]] = Field(default_factory=list)


class KPICardSchema(BaseModel):
    label: str
    value: str
    trend: Optional[str] = None
    trend_direction: Optional[str] = "neutral"


class ChartConfigSchema(BaseModel):
    type: str
    title: str
    x_axis: str
    y_axis: str
    data: List[Dict[str, Any]] = Field(default_factory=list)
    series: Optional[Any] = None
    highlight: Optional[Any] = None


class QueryResponse(BaseModel):
    kpi_cards: List[KPICardSchema] = Field(default_factory=list)
    main_chart: Optional[ChartConfigSchema] = None
    secondary_chart: Optional[ChartConfigSchema] = None
    narrative: str = ""
    suggested_followups: List[str] = Field(default_factory=list)
    sql_query: Optional[str] = None
    error: Optional[str] = None
    suggestion: Optional[str] = None
    available_columns: Optional[List[str]] = None
    data_quality: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
