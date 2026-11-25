from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class WhatIfRequest(BaseModel):
    price_change: float = 0.0
    discount_change: float = 0.0
    units_change: float = 0.0
    dataset_id: Optional[str] = None


class WhatIfResponse(BaseModel):
    current: Dict[str, Any]
    projected: Dict[str, Any]
    change: Dict[str, Any]
    monthly_comparison: List[Dict[str, Any]] = []
    category_impact: List[Dict[str, Any]] = []
    ai_commentary: str = ""
    error: Optional[str] = None


class DeepDiveResponse(BaseModel):
    top_revenue_drivers: List[Dict[str, Any]] = []
    risk_areas: List[Dict[str, Any]] = []
    root_cause_analysis: str = ""
    recommendations: List[Dict[str, Any]] = []
    monthly_trend: Optional[List[Dict[str, Any]]] = None
    revenue_by_category: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    # Comprehensive 10-Section Research Workspace fields
    dataset_metadata: Optional[Dict[str, Any]] = None
    executive_summary: Optional[Dict[str, Any]] = None
    revenue_analysis: Optional[Dict[str, Any]] = None
    profitability_analysis: Optional[Dict[str, Any]] = None
    product_analysis: Optional[Dict[str, Any]] = None
    category_analysis: Optional[Dict[str, Any]] = None
    regional_analysis: Optional[Dict[str, Any]] = None
    customer_analysis: Optional[Dict[str, Any]] = None
    trend_and_forecast: Optional[Dict[str, Any]] = None
    anomalies_and_risks: Optional[Dict[str, Any]] = None
    opportunities: Optional[List[Dict[str, Any]]] = None
    strategic_action_plan: Optional[Dict[str, Any]] = None
    charts: Optional[Dict[str, Any]] = None
    execution_stages: Optional[List[str]] = None


class AnomalyItemSchema(BaseModel):
    metric: str
    description: str
    severity: str  # high, medium, low
    suggestion: str


class AnomalyResponse(BaseModel):
    anomalies: List[str] = []
    count: int = 0
    ai_analysis: List[AnomalyItemSchema] = []
    error: Optional[str] = None
