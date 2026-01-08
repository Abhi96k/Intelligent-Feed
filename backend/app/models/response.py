"""API response models."""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from .chart import ChartSpec
from .insight import Driver


class InsightResponseTriggered(BaseModel):
    """Response when insight is triggered (alert-worthy)."""
    triggered: bool = True
    trigger_reason: str
    what_happened: str
    why_happened: str
    charts: List[ChartSpec]
    confidence: float = Field(ge=0.0, le=100.0)
    evidence: Dict[str, Any]

    # Additional metadata
    metric: str
    time_range: Dict[str, str]
    filters: Dict[str, Any] = Field(default_factory=dict)


class InsightResponseNotTriggered(BaseModel):
    """Response when insight is not triggered (not alert-worthy)."""
    triggered: bool = False
    explanation: str
    suggestion: str

    # Context for user
    metric: str
    time_range: Dict[str, str]
    filters: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, float] = Field(default_factory=dict)


# Union type for API response
InsightResponse = Union[InsightResponseTriggered, InsightResponseNotTriggered]


class InsightRequest(BaseModel):
    """Request model for insight generation."""
    user_question: str = Field(..., min_length=1, max_length=1000)

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "user_question": "Why did revenue in APAC drop in the last 8 weeks vs previous period?"
                },
                {
                    "user_question": "Show me anomalies in user signups for Q4 2024"
                },
                {
                    "user_question": "What caused the sales spike in Enterprise segment last month?"
                }
            ]
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    components: Dict[str, str]


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
