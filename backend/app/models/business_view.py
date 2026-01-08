"""Business View model - Tellius compatible schema representation."""

from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class ColumnType(str, Enum):
    """Column data types."""
    INTEGER = "integer"
    STRING = "string"
    DATE = "date"
    FLOAT = "float"
    BOOLEAN = "boolean"
    TIMESTAMP = "timestamp"


class JoinType(str, Enum):
    """SQL join types."""
    INNER = "inner"
    LEFT = "left"
    RIGHT = "right"
    FULL = "full"


class Granularity(str, Enum):
    """Time granularity options."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class WeekStart(str, Enum):
    """Week start day options."""
    MONDAY = "monday"
    SUNDAY = "sunday"


class Column(BaseModel):
    """Represents a database column."""
    name: str
    type: ColumnType
    nullable: bool = True
    description: Optional[str] = None


class Table(BaseModel):
    """Represents a database table."""
    name: str
    schema: str = "public"
    columns: List[Column]
    description: Optional[str] = None


class Join(BaseModel):
    """Represents a join relationship between tables."""
    left_table: str
    right_table: str
    left_key: str
    right_key: str
    join_type: JoinType = JoinType.INNER


class Measure(BaseModel):
    """Represents a calculated measure/metric."""
    name: str
    expression: str  # e.g., "SUM(revenue)", "COUNT(DISTINCT user_id)"
    format: str = "number"  # "number", "currency", "percentage"
    description: Optional[str] = None

    @property
    def aggregation_function(self) -> str:
        """Extract aggregation function from expression."""
        if "(" in self.expression:
            return self.expression.split("(")[0].strip().upper()
        return "SUM"

    @property
    def base_column(self) -> str:
        """Extract base column from expression."""
        if "(" in self.expression and ")" in self.expression:
            inner = self.expression.split("(")[1].split(")")[0]
            # Handle DISTINCT and other modifiers
            parts = inner.split()
            return parts[-1].strip()
        return self.expression


class Dimension(BaseModel):
    """Represents a dimension for slicing/filtering."""
    name: str
    column: str
    table: str
    description: Optional[str] = None

    @property
    def full_column_name(self) -> str:
        """Get fully qualified column name."""
        return f"{self.table}.{self.column}"


class TimeDimension(BaseModel):
    """Represents the time dimension for temporal analysis."""
    column: str
    table: str
    granularity: Granularity = Granularity.DAY
    description: Optional[str] = None

    @property
    def full_column_name(self) -> str:
        """Get fully qualified column name."""
        return f"{self.table}.{self.column}"


class CalendarRules(BaseModel):
    """Calendar and fiscal year rules."""
    fiscal_year_start: int = Field(default=1, ge=1, le=12)  # month (1-12)
    week_start: WeekStart = WeekStart.MONDAY

    def is_fiscal_year(self) -> bool:
        """Check if using fiscal year (not calendar year)."""
        return self.fiscal_year_start != 1


class BusinessView(BaseModel):
    """
    Tellius Business View model.

    This is the core metadata object that defines the schema,
    relationships, and semantics for data analysis.
    """
    id: str
    name: str
    tables: List[Table]
    joins: List[Join]
    measures: List[Measure]
    dimensions: List[Dimension]
    time_dimension: TimeDimension
    calendar_rules: CalendarRules = Field(default_factory=CalendarRules)
    description: Optional[str] = None

    def get_table(self, table_name: str) -> Optional[Table]:
        """Get table by name."""
        for table in self.tables:
            if table.name == table_name:
                return table
        return None

    def get_measure(self, measure_name: str) -> Optional[Measure]:
        """Get measure by name."""
        for measure in self.measures:
            if measure.name == measure_name:
                return measure
        return None

    def get_dimension(self, dimension_name: str) -> Optional[Dimension]:
        """Get dimension by name."""
        for dimension in self.dimensions:
            if dimension.name == dimension_name:
                return dimension
        return None

    def get_all_columns(self) -> List[str]:
        """Get all fully qualified column names."""
        columns = []
        for table in self.tables:
            for column in table.columns:
                columns.append(f"{table.name}.{column.name}")
        return columns

    def get_measure_names(self) -> List[str]:
        """Get all measure names."""
        return [m.name for m in self.measures]

    def get_dimension_names(self) -> List[str]:
        """Get all dimension names."""
        return [d.name for d in self.dimensions]
