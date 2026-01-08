# TQL Services Quick Reference

Quick reference guide for using TQLPlanner, PlanValidator, and TQLAdapter.

## Quick Start

```python
from app.services import TQLPlanner, PlanValidator, TQLAdapter, BVContextBuilder

# 1. Generate plan
plan = TQLPlanner.generate(intent, business_view)

# 2. Validate plan
bv_context = BVContextBuilder.build(business_view)
validated_plan = PlanValidator.validate(plan, bv_context)

# 3. Execute plan
adapter = TQLAdapter()
results = adapter.execute(validated_plan)

# 4. Get values
current = results.get_current_value()
baseline = results.get_baseline_value()
```

## Common Patterns

### Basic Metric Query

```python
intent = ParsedIntent(
    metric="Total Revenue",
    time_range=TimeRange(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31)
    ),
    filters={},
)

plan = TQLPlanner.generate(intent, bv)
```

### Query with Filters

```python
intent = ParsedIntent(
    metric="Total Revenue",
    time_range=TimeRange(...),
    filters={
        "Region": "APAC",              # Single value
        "Segment": ["Enterprise", "SMB"]  # Multiple values
    },
)
```

### Query with Baseline

```python
intent = ParsedIntent(
    metric="Total Revenue",
    time_range=TimeRange(...),
    baseline=BaselineConfig(
        type=BaselineType.PREVIOUS_PERIOD  # or LAST_YEAR
    ),
)
```

### ARIMA Time-Series

```python
intent = ParsedIntent(
    metric="Total Revenue",
    time_range=TimeRange(...),
    feed_type=FeedType.ARIMA,
)

plan = TQLPlanner.generate(intent, bv)
# plan.timeseries_query will be populated
```

### Custom Baseline Dates

```python
baseline = BaselineConfig(
    type=BaselineType.CUSTOM,
    start_date=date(2025, 6, 1),
    end_date=date(2025, 6, 30)
)
```

## Error Handling

### TQLPlanner Errors

```python
try:
    plan = TQLPlanner.generate(intent, bv)
except ValueError as e:
    # Measure not found or invalid dimension
    print(f"Invalid intent: {e}")
```

### PlanValidator Errors

```python
from app.services.plan_validator import ValidationError

try:
    validated_plan = PlanValidator.validate(plan, bv_context)
except ValidationError as e:
    print(f"Validation failed: {e.message}")
    print(f"Query: {e.query_name}")
    print(f"Details: {e.details}")
```

### TQLAdapter Errors

```python
from app.services.tql_adapter import QueryExecutionError

try:
    results = adapter.execute(plan)
except QueryExecutionError as e:
    print(f"Execution failed: {e.message}")
    print(f"Query: {e.query_name}")
    if e.original_error:
        print(f"Original error: {e.original_error}")
```

## Accessing Results

### Scalar Values

```python
# Get aggregated metric values
current = results.get_current_value()    # float
baseline = results.get_baseline_value()  # float or None

# Calculate change
if baseline:
    delta = current - baseline
    pct_change = (delta / baseline) * 100
```

### DataFrames

```python
# Current period aggregation
df_current = results.current_period
# Columns: ['metric_value']

# Time-series data
df_ts = results.timeseries
# Columns: ['date', 'value']

# Dimensional breakdown
df_breakdown = results.dimensional_breakdown
# Columns: ['Region', 'Segment', 'Category', 'metric_value']

# Baseline breakdown
df_baseline_breakdown = results.baseline_dimensional_breakdown
```

### Result Checks

```python
if results.has_baseline():
    # Baseline comparison available
    pass

if results.has_timeseries():
    # Time-series data available
    df = results.timeseries

if results.has_dimensional_breakdown():
    # RCA data available
    df_current = results.dimensional_breakdown
    df_baseline = results.baseline_dimensional_breakdown
```

## Database Operations

### Initialize Database

```python
adapter = TQLAdapter("sqlite:///./my_data.db")

schema = """
CREATE TABLE sales (...);
INSERT INTO sales VALUES (...);
"""

adapter.initialize_database(schema)
```

### Test Connection

```python
if adapter.test_connection():
    print("Database connected")
else:
    print("Connection failed")
```

### Introspection

```python
# List all tables
tables = adapter.list_tables()

# Check if table exists
if adapter.table_exists("sales"):
    # Get row count
    count = adapter.get_row_count("sales")

    # Get schema
    schema = adapter.get_table_info("sales")
```

### Raw Queries

```python
# Execute custom query
df = adapter.execute_raw_query("""
    SELECT region, SUM(revenue) as total
    FROM sales
    GROUP BY region
""")
```

## Query Inspection

### View Generated Queries

```python
plan = TQLPlanner.generate(intent, bv)

# All queries with names
for query_name, query_sql in plan.get_all_queries():
    print(f"\n{query_name}:")
    print(query_sql)
```

### Plan Metadata

```python
metadata = plan.metadata

print(f"Estimated rows: {metadata.estimated_rows}")
print(f"Complexity: {metadata.complexity_score}/10")
print(f"Uses joins: {metadata.uses_joins}")
print(f"Uses aggregation: {metadata.uses_aggregation}")
print(f"Uses window functions: {metadata.uses_window_functions}")
```

### Plan Checks

```python
if plan.requires_baseline():
    # Baseline query present
    pass

if plan.requires_timeseries():
    # Time-series query present
    pass

if plan.requires_dimensional_breakdown():
    # Breakdown queries present
    pass
```

## Configuration

### Environment Variables

```bash
# .env file
DATABASE_URL=sqlite:///./tellius_feed.db
QUERY_TIMEOUT=30
MAX_QUERY_ROWS=1000000
```

### Programmatic Config

```python
from app.core.config import settings

# Override settings
settings.QUERY_TIMEOUT = 60
settings.MAX_QUERY_ROWS = 5000000
```

## Logging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now all services will log detailed information
```

### Structured Logging

```python
from app.core.logging import get_logger

logger = get_logger(__name__)

logger.info("custom_event",
    metric="Total Revenue",
    value=12345.67,
    extra_context="additional info"
)
```

## Testing

### Minimal Test

```python
import pytest
from datetime import date

def test_basic_plan_generation(sample_business_view):
    intent = ParsedIntent(
        metric="Total Revenue",
        time_range=TimeRange(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31)
        ),
        filters={},
    )

    plan = TQLPlanner.generate(intent, sample_business_view)

    assert plan is not None
    assert plan.current_period_query is not None
```

### Integration Test

```python
def test_full_pipeline(sample_business_view, sample_intent, temp_database):
    # Generate
    plan = TQLPlanner.generate(sample_intent, sample_business_view)

    # Validate
    bv_context = BVContextBuilder.build(sample_business_view)
    validated_plan = PlanValidator.validate(plan, bv_context)

    # Execute
    results = temp_database.execute(validated_plan)

    # Assert
    assert results.get_current_value() is not None
```

## Common Issues

### Issue: "Measure not found"

```python
# Solution: Check measure name exactly matches Business View
measure = bv.get_measure("Total Revenue")  # Use exact name
```

### Issue: "Invalid column reference"

```python
# Solution: Use dimension names from Business View
filters = {
    "Region": "APAC",  # Use dimension name, not column name
}
```

### Issue: "Query timeout"

```python
# Solution: Increase timeout or optimize query
settings.QUERY_TIMEOUT = 60  # seconds
```

### Issue: Empty results

```python
# Solution: Check time range and filters
# Debug: Print the generated query
print(plan.current_period_query)
```

## Performance Tips

1. **Reuse BVContext**: Build once, use for all validations

   ```python
   bv_context = BVContextBuilder.build(bv)  # Build once
   for plan in plans:
       PlanValidator.validate(plan, bv_context)  # Reuse
   ```

2. **Limit dimensions**: Only include needed dimensions

   ```python
   # Good: Specific dimensions
   bv = BusinessView(..., dimensions=[region, segment])

   # Avoid: Too many dimensions
   bv = BusinessView(..., dimensions=[50+ dimensions])
   ```

3. **Use appropriate time ranges**: Smaller ranges = faster queries

   ```python
   # Good: 30 days
   TimeRange(start_date=today - 30, end_date=today)

   # Slow: 5 years
   TimeRange(start_date=today - 1825, end_date=today)
   ```

4. **Add filters**: Reduce data scanned
   ```python
   filters={"Region": "APAC"}  # Filters early in WHERE clause
   ```

## API Reference

### TQLPlanner

```python
TQLPlanner.generate(intent: ParsedIntent, business_view: BusinessView) -> TQLPlan
```

### PlanValidator

```python
PlanValidator.validate(plan: TQLPlan, bv_context: BVContext) -> TQLPlan
PlanValidator.validate_query_safety(query: str) -> bool
```

### TQLAdapter

```python
TQLAdapter.__init__(database_url: Optional[str] = None)
TQLAdapter.execute(plan: TQLPlan) -> QueryResults
TQLAdapter.execute_raw_query(query: str) -> pd.DataFrame
TQLAdapter.test_connection() -> bool
TQLAdapter.list_tables() -> List[str]
TQLAdapter.table_exists(table_name: str) -> bool
TQLAdapter.get_table_info(table_name: str) -> Optional[pd.DataFrame]
TQLAdapter.get_row_count(table_name: str) -> Optional[int]
TQLAdapter.initialize_database(schema_sql: str) -> None
```

### QueryResults

```python
QueryResults.get_current_value() -> Optional[float]
QueryResults.get_baseline_value() -> Optional[float]
QueryResults.has_baseline() -> bool
QueryResults.has_timeseries() -> bool
QueryResults.has_dimensional_breakdown() -> bool
QueryResults.to_dict() -> Dict[str, Any]
```

## Resources

- Full Documentation: `docs/TQL_SERVICES.md`
- Implementation Summary: `docs/TQL_SERVICES_SUMMARY.md`
- Example Code: `examples/tql_services_example.py`
- Test Suite: `tests/test_tql_services_integration.py`
- Architecture: `ARCHITECTURE.md`
