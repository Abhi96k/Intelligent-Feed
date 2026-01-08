"""Parsed intent models - structured representation of user questions."""

from typing import Dict, Optional, Union, List
from datetime import date
from pydantic import BaseModel, Field
from enum import Enum


class FeedType(str, Enum):
    """Type of feed detection to perform."""
    ABSOLUTE = "absolute"
    ARIMA = "arima"


class BaselineType(str, Enum):
    """Type of baseline comparison."""
    PREVIOUS_PERIOD = "previous_period"
    LAST_YEAR = "last_year"
    CUSTOM = "custom"


class TimeRange(BaseModel):
    """Represents a time range for analysis."""
    start_date: date
    end_date: date
    granularity: str = "day"  # "day", "week", "month"

    def days_count(self) -> int:
        """Get number of days in the range."""
        return (self.end_date - self.start_date).days + 1

    def to_sql_condition(self, date_column: str) -> str:
        """Generate SQL WHERE condition for this time range."""
        return f"{date_column} BETWEEN '{self.start_date}' AND '{self.end_date}'"


class BaselineConfig(BaseModel):
    """Configuration for baseline comparison period."""
    type: BaselineType
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    def compute_dates(self, current_range: TimeRange) -> TimeRange:
        """
        Compute baseline date range based on current range and type.

        Args:
            current_range: The current time range

        Returns:
            TimeRange for the baseline period
        """
        if self.type == BaselineType.CUSTOM and self.start_date and self.end_date:
            return TimeRange(
                start_date=self.start_date,
                end_date=self.end_date,
                granularity=current_range.granularity
            )

        days_delta = current_range.days_count()

        if self.type == BaselineType.PREVIOUS_PERIOD:
            # Shift back by the duration of current period
            from datetime import timedelta
            baseline_end = current_range.start_date - timedelta(days=1)
            baseline_start = baseline_end - timedelta(days=days_delta - 1)
            return TimeRange(
                start_date=baseline_start,
                end_date=baseline_end,
                granularity=current_range.granularity
            )

        elif self.type == BaselineType.LAST_YEAR:
            # Shift back by 1 year
            baseline_start = date(
                current_range.start_date.year - 1,
                current_range.start_date.month,
                current_range.start_date.day
            )
            baseline_end = date(
                current_range.end_date.year - 1,
                current_range.end_date.month,
                current_range.end_date.day
            )
            return TimeRange(
                start_date=baseline_start,
                end_date=baseline_end,
                granularity=current_range.granularity
            )

        raise ValueError(f"Invalid baseline configuration: {self.type}")


class ParsedIntent(BaseModel):
    """
    Structured representation of user question.

    This is the output of the Question Parser component.
    """
    metric: str  # measure name from Business View
    time_range: TimeRange
    filters: Dict[str, Union[str, List[str]]] = Field(default_factory=dict)
    baseline: Optional[BaselineConfig] = None
    feed_type: FeedType = FeedType.ABSOLUTE
    threshold: Optional[float] = None  # Override default threshold

    def has_filters(self) -> bool:
        """Check if any filters are specified."""
        return len(self.filters) > 0

    def get_filter_sql(self) -> str:
        """
        Generate SQL WHERE conditions from filters.

        Returns:
            SQL WHERE clause (without the WHERE keyword)
        """
        if not self.has_filters():
            return ""

        conditions = []
        for dimension, values in self.filters.items():
            if isinstance(values, list):
                # Multiple values: use IN clause
                values_str = ", ".join(f"'{v}'" for v in values)
                conditions.append(f"{dimension} IN ({values_str})")
            else:
                # Single value: use =
                conditions.append(f"{dimension} = '{values}'")

        return " AND ".join(conditions)

    def has_baseline(self) -> bool:
        """Check if baseline comparison is requested."""
        return self.baseline is not None

    def get_baseline_range(self) -> Optional[TimeRange]:
        """Get computed baseline time range."""
        if not self.has_baseline():
            return None
        return self.baseline.compute_dates(self.time_range)

    def to_dict(self) -> dict:
        """Convert to dictionary for logging/debugging."""
        return {
            "metric": self.metric,
            "time_range": {
                "start": str(self.time_range.start_date),
                "end": str(self.time_range.end_date),
                "granularity": self.time_range.granularity,
            },
            "filters": self.filters,
            "baseline": self.baseline.type if self.baseline else None,
            "feed_type": self.feed_type.value,
            "threshold": self.threshold,
        }
