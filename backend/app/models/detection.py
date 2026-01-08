"""Detection result models - outputs from detection engines."""

from typing import Optional, List, Dict, Any, Union
from datetime import date
from pydantic import BaseModel, Field
from .intent import FeedType


class AnomalyPoint(BaseModel):
    """Represents a detected anomaly in time-series data."""
    date: date
    value: float
    expected_value: Optional[float] = None
    residual: float
    severity: float = Field(ge=0.0, le=1.0)  # 0-1 scale

    def is_severe(self, threshold: float = 0.7) -> bool:
        """Check if anomaly is severe."""
        return self.severity >= threshold


class DetectionResult(BaseModel):
    """
    Result from detection engine (Absolute or ARIMA).

    This determines whether deep insight generation should proceed.
    """
    triggered: bool
    trigger_reason: str
    feed_type: FeedType
    metrics: Dict[str, Any] = Field(default_factory=dict)  # Changed to Any to support various value types

    # For ARIMA detection
    anomaly_points: Optional[List[AnomalyPoint]] = None
    model_params: Optional[Dict[str, Any]] = None

    # For Absolute detection
    current_value: Optional[float] = None
    baseline_value: Optional[float] = None
    absolute_delta: Optional[float] = None
    percent_change: Optional[float] = None
    threshold_used: Optional[Union[float, str]] = None  # Can be float (legacy) or string (new format like "current > 1000000")

    def is_arima(self) -> bool:
        """Check if this is ARIMA detection result."""
        return self.feed_type == FeedType.ARIMA

    def is_absolute(self) -> bool:
        """Check if this is Absolute detection result."""
        return self.feed_type == FeedType.ABSOLUTE

    def get_anomaly_count(self) -> int:
        """Get number of detected anomalies."""
        if not self.anomaly_points:
            return 0
        return len(self.anomaly_points)

    def get_severe_anomaly_count(self) -> int:
        """Get number of severe anomalies."""
        if not self.anomaly_points:
            return 0
        return sum(1 for p in self.anomaly_points if p.is_severe())

    def get_change_direction(self) -> Optional[str]:
        """Get direction of change (increase/decrease/stable)."""
        if self.absolute_delta is None:
            return None

        if abs(self.absolute_delta) < 0.01:  # negligible change
            return "stable"
        elif self.absolute_delta > 0:
            return "increase"
        else:
            return "decrease"

    def get_summary(self) -> str:
        """Get human-readable summary of detection."""
        if not self.triggered:
            return "No significant change detected"

        if self.is_absolute():
            direction = self.get_change_direction()
            return f"Metric {direction}d by {abs(self.percent_change):.1f}%"
        else:
            count = self.get_anomaly_count()
            return f"Detected {count} anomalies in time-series"
