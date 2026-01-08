"""Deep insight models - outputs from RCA and contribution analysis."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import pandas as pd


class Driver(BaseModel):
    """Represents a contributing driver to the change."""
    dimension: str
    member: str
    impact: float  # Absolute impact on total change
    contribution_current: float  # Contribution % in current period
    contribution_baseline: float  # Contribution % in baseline period
    shift: float  # Change in contribution percentage points
    value_current: Optional[float] = None
    value_baseline: Optional[float] = None

    def is_positive_driver(self) -> bool:
        """Check if this is a positive driver (upward impact)."""
        return self.impact > 0

    def is_negative_driver(self) -> bool:
        """Check if this is a negative driver (downward impact)."""
        return self.impact < 0

    def get_impact_percentage(self, total_change: float) -> float:
        """Get impact as percentage of total change."""
        if total_change == 0:
            return 0.0
        return (self.impact / total_change) * 100

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "dimension": self.dimension,
            "member": self.member,
            "impact": self.impact,
            "contribution_current": self.contribution_current,
            "contribution_baseline": self.contribution_baseline,
            "shift": self.shift,
            "value_current": self.value_current,
            "value_baseline": self.value_baseline,
        }


class DeepInsight(BaseModel):
    """
    Deep root-cause analysis result.

    This is only generated when detection is triggered.
    """
    top_drivers: List[Driver]
    explainability_score: float = Field(ge=0.0, le=100.0)  # 0-100 scale
    evidence: Dict[str, Any] = Field(default_factory=dict)

    # Summary statistics
    total_positive_impact: float = 0.0
    total_negative_impact: float = 0.0
    net_impact: float = 0.0

    class Config:
        arbitrary_types_allowed = True

    def get_positive_drivers(self) -> List[Driver]:
        """Get only positive drivers."""
        return [d for d in self.top_drivers if d.is_positive_driver()]

    def get_negative_drivers(self) -> List[Driver]:
        """Get only negative drivers."""
        return [d for d in self.top_drivers if d.is_negative_driver()]

    def get_top_n_drivers(self, n: int = 5) -> List[Driver]:
        """Get top N drivers by absolute impact."""
        return sorted(
            self.top_drivers,
            key=lambda d: abs(d.impact),
            reverse=True
        )[:n]

    def get_drivers_by_dimension(self, dimension: str) -> List[Driver]:
        """Get drivers for a specific dimension."""
        return [d for d in self.top_drivers if d.dimension == dimension]

    def calculate_coverage(self, total_change: float) -> float:
        """
        Calculate what % of total change is explained by top drivers.

        Args:
            total_change: Total change in the metric

        Returns:
            Coverage percentage (0-100)
        """
        if total_change == 0:
            return 0.0

        explained_change = sum(abs(d.impact) for d in self.top_drivers)
        coverage = min((explained_change / abs(total_change)) * 100, 100.0)
        return coverage

    def is_high_confidence(self, threshold: float = 70.0) -> bool:
        """Check if insight has high confidence."""
        return self.explainability_score >= threshold

    def get_primary_driver(self) -> Optional[Driver]:
        """Get the single most impactful driver."""
        if not self.top_drivers:
            return None
        return max(self.top_drivers, key=lambda d: abs(d.impact))

    def to_summary_dict(self) -> dict:
        """Convert to summary dictionary for API response."""
        return {
            "explainability_score": self.explainability_score,
            "driver_count": len(self.top_drivers),
            "positive_drivers": len(self.get_positive_drivers()),
            "negative_drivers": len(self.get_negative_drivers()),
            "total_positive_impact": self.total_positive_impact,
            "total_negative_impact": self.total_negative_impact,
            "net_impact": self.net_impact,
            "primary_driver": self.get_primary_driver().to_dict() if self.get_primary_driver() else None,
        }
