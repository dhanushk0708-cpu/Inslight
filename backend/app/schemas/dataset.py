from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict


class ColumnInfoSchema(BaseModel):
    name: str
    dtype: str
    semantic_type: str
    unique_count: int
    sample_values: List[str]
    null_count: int
    stats: Optional[Dict[str, float]] = None


class DatasetProfileResponse(BaseModel):
    id: Optional[str] = None
    filename: str
    rows: int
    columns: int
    column_info: List[ColumnInfoSchema]
    data_quality_score: float
    missing_values: Dict[str, int]
    suggested_questions: List[str]
    preview: List[Dict[str, Any]]


class DatasetResponse(BaseModel):
    id: str
    user_id: str
    original_filename: str
    table_name: str
    row_count: int
    column_count: int
    created_at: Optional[datetime] = None
    columns: Optional[List[str]] = None
    profile: Optional[DatasetProfileResponse] = None

    model_config = ConfigDict(from_attributes=True)
