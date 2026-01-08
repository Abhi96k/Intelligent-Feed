"""TQL Plan models - SQL query plans for execution."""

from typing import Optional
from pydantic import BaseModel


class PlanMetadata(BaseModel):
    """Metadata about the query plan."""
    estimated_rows: int = 0
    complexity_score: int = 1  # 1-10 scale
    uses_joins: bool = False
    uses_aggregation: bool = True
    uses_window_functions: bool = False


class TQLPlan(BaseModel):
    """
    Collection of SQL queries to execute for insight generation.

    Different queries serve different purposes:
    - current_period_query: Main metric for current time range
    - baseline_period_query: Same metric for comparison period
    - timeseries_query: Time-series data for ARIMA detection
    - dimensional_breakdown_query: Dimensional analysis for RCA
    """

    # Main queries
    current_period_query: str
    baseline_period_query: Optional[str] = None
    timeseries_query: Optional[str] = None
    dimensional_breakdown_query: Optional[str] = None

    # Baseline dimensional breakdown for contribution shift analysis
    baseline_dimensional_breakdown_query: Optional[str] = None

    # Metadata
    metadata: PlanMetadata = PlanMetadata()

    def get_all_queries(self) -> list[tuple[str, str]]:
        """
        Get all non-null queries with their names.

        Returns:
            List of (query_name, query_sql) tuples
        """
        queries = [("current_period", self.current_period_query)]

        if self.baseline_period_query:
            queries.append(("baseline_period", self.baseline_period_query))

        if self.timeseries_query:
            queries.append(("timeseries", self.timeseries_query))

        if self.dimensional_breakdown_query:
            queries.append(("dimensional_breakdown", self.dimensional_breakdown_query))

        if self.baseline_dimensional_breakdown_query:
            queries.append(("baseline_dimensional_breakdown", self.baseline_dimensional_breakdown_query))

        return queries

    def requires_baseline(self) -> bool:
        """Check if baseline comparison is included."""
        return self.baseline_period_query is not None

    def requires_timeseries(self) -> bool:
        """Check if time-series analysis is included."""
        return self.timeseries_query is not None

    def requires_dimensional_breakdown(self) -> bool:
        """Check if dimensional breakdown is included."""
        return self.dimensional_breakdown_query is not None
