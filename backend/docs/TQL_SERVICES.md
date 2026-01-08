# TQL Services Documentation

This document describes the three critical backend services for the Intelligent Feed system that handle SQL/TQL query generation, validation, and execution.

## Overview

The TQL services form the data layer of the Intelligent Feed system, bridging the gap between parsed user intent and actual data retrieval:

```
ParsedIntent → TQLPlanner → TQLPlan → PlanValidator → ValidatedPlan → TQLAdapter → QueryResults
```

## Services

### 1. TQLPlanner

**Location**: `app/services/tql_planner.py`

**Purpose**: Generate SQL/TQL execution plans from parsed user intent.

#### Key Features

- Generates multiple specialized queries from a single intent
- Handles proper JOIN logic based on Business View relationships
- Supports time range filtering and baseline comparisons
- Creates dimensional breakdowns for root cause analysis
- Respects Tellius time semantics and calendar rules

#### API

```python
from app.services.tql_planner import TQLPlanner

# Generate a plan
plan = TQLPlanner.generate(intent, business_view)
```

#### Generated Queries

The planner generates up to 5 different queries:

1. **current_period_query**: Aggregated metric for current time range
   ```sql
   SELECT SUM(revenue) AS metric_value
   FROM sales
   LEFT JOIN customers ON sales.customer_id = customers.customer_id
   WHERE sales.sale_date BETWEEN '2026-01-01' AND '2026-01-31'
     AND customers.region = 'APAC'
   ```

2. **baseline_period_query**: Same metric for comparison period
   ```sql
   SELECT SUM(revenue) AS metric_value
   FROM sales
   LEFT JOIN customers ON sales.customer_id = customers.customer_id
   WHERE sales.sale_date BETWEEN '2025-12-01' AND '2025-12-31'
     AND customers.region = 'APAC'
   ```

3. **timeseries_query**: Time-series data for ARIMA detection
   ```sql
   SELECT sales.sale_date AS date, SUM(revenue) AS value
   FROM sales
   LEFT JOIN customers ON sales.customer_id = customers.customer_id
   WHERE sales.sale_date BETWEEN '2026-01-01' AND '2026-01-31'
     AND customers.region = 'APAC'
   GROUP BY sales.sale_date
   ORDER BY sales.sale_date
   ```

4. **dimensional_breakdown_query**: Dimensional analysis for current period
   ```sql
   SELECT customers.region AS Region,
          customers.segment AS Segment,
          products.category AS Category,
          SUM(revenue) AS metric_value
   FROM sales
   LEFT JOIN customers ON sales.customer_id = customers.customer_id
   LEFT JOIN products ON sales.product_id = products.product_id
   WHERE sales.sale_date BETWEEN '2026-01-01' AND '2026-01-31'
   GROUP BY customers.region, customers.segment, products.category
   ```

5. **baseline_dimensional_breakdown_query**: Same for baseline period

#### Implementation Details

**Table Resolution**:
- Determines which tables are needed based on metric, dimensions, and filters
- Uses `BVContextBuilder.get_table_for_measure()` to find measure's source table
- Includes all dimension tables for comprehensive breakdown

**JOIN Construction**:
- Uses `BVContextBuilder.get_required_joins()` to find necessary joins
- Builds JOIN clauses in correct order
- Supports INNER, LEFT, RIGHT, and FULL joins

**Filter Application**:
- Converts dimension filters to SQL WHERE conditions
- Handles single values (`region = 'APAC'`) and multiple values (`region IN ('APAC', 'EMEA')`)
- Properly quotes string values

**Time Range Handling**:
- Uses `TimeRange.to_sql_condition()` for date filtering
- Computes baseline dates using `BaselineConfig.compute_dates()`
- Respects fiscal year and week start rules

**Complexity Scoring**:
- Calculates 1-10 complexity score based on:
  - Number of tables (2 points each)
  - Number of filters (1 point each)
  - ARIMA detection (2 points)
  - Baseline comparison (1 point)

---

### 2. PlanValidator

**Location**: `app/services/plan_validator.py`

**Purpose**: Validate SQL plans for security and Tellius compatibility.

#### Key Features

- SQL injection prevention
- Dangerous keyword detection
- Column whitelist validation
- Query structure verification
- Aggregation usage validation

#### API

```python
from app.services.plan_validator import PlanValidator, ValidationError

# Validate a plan
try:
    validated_plan = PlanValidator.validate(plan, bv_context)
except ValidationError as e:
    print(f"Validation failed: {e.message}")
    print(f"Query: {e.query_name}")
    print(f"Details: {e.details}")
```

#### Security Checks

**1. Dangerous Keywords**

Blocks queries containing:
- `DROP`, `DELETE`, `TRUNCATE` (data destruction)
- `ALTER`, `CREATE` (schema modification)
- `INSERT`, `UPDATE` (data modification)
- `EXEC`, `EXECUTE` (code execution)
- `GRANT`, `REVOKE` (permission changes)

```python
# This will raise ValidationError
query = "SELECT * FROM sales; DROP TABLE sales;"
```

**2. SQL Injection Patterns**

Detects:
- Multiple statements (semicolons)
- Comment-based injection (`--`, `/**/`)
- UNION attacks
- Subqueries (restricted for security)

```python
# These will raise ValidationError
"SELECT * FROM sales WHERE region = 'APAC' OR 1=1 --"
"SELECT * FROM sales UNION SELECT * FROM users"
```

**3. Column Whitelist**

- Validates all column references against Business View
- Prevents access to unauthorized columns
- Uses regex-based column extraction (simplified approach)

**4. Query Structure**

- Must start with `SELECT`
- Must contain `FROM` clause
- Balanced parentheses
- Proper aggregation usage

#### Validation Process

```python
def validate(plan: TQLPlan, bv_context: BVContext) -> TQLPlan:
    for query_name, query_sql in plan.get_all_queries():
        _check_dangerous_keywords(query_sql, query_name)
        _check_sql_injection(query_sql, query_name)
        _validate_column_references(query_sql, query_name, bv_context)
        _validate_query_structure(query_sql, query_name)
        _validate_aggregation(query_sql, query_name)
    return plan
```

#### Error Handling

All validation errors raise `ValidationError` with:
- `message`: Human-readable error description
- `query_name`: Which query failed validation
- `details`: Additional context about the error

---

### 3. TQLAdapter

**Location**: `app/services/tql_adapter.py`

**Purpose**: Execute TQL plans against SQLite database and return results.

#### Key Features

- SQLite database connectivity
- Query execution with pandas DataFrames
- Connection pooling and management
- Error handling with detailed logging
- Database introspection utilities

#### API

```python
from app.services.tql_adapter import TQLAdapter, QueryResults

# Initialize adapter
adapter = TQLAdapter("sqlite:///./tellius_feed.db")

# Test connection
if adapter.test_connection():
    # Execute plan
    results = adapter.execute(plan)

    # Access results
    current_value = results.get_current_value()
    baseline_value = results.get_baseline_value()
    timeseries_df = results.timeseries
    breakdown_df = results.dimensional_breakdown
```

#### QueryResults Object

Container for all query execution results:

```python
class QueryResults:
    current_period: Optional[pd.DataFrame]
    baseline_period: Optional[pd.DataFrame]
    timeseries: Optional[pd.DataFrame]
    dimensional_breakdown: Optional[pd.DataFrame]
    baseline_dimensional_breakdown: Optional[pd.DataFrame]

    def get_current_value() -> Optional[float]
    def get_baseline_value() -> Optional[float]
    def has_baseline() -> bool
    def has_timeseries() -> bool
    def has_dimensional_breakdown() -> bool
```

#### Database Operations

**Execute Plan**:
```python
results = adapter.execute(plan)
```

**Execute Raw Query**:
```python
df = adapter.execute_raw_query("SELECT COUNT(*) FROM sales")
```

**Initialize Database**:
```python
schema_sql = """
CREATE TABLE sales (
    sale_id INTEGER PRIMARY KEY,
    sale_date DATE,
    revenue REAL
);
"""
adapter.initialize_database(schema_sql)
```

**Database Introspection**:
```python
# List tables
tables = adapter.list_tables()

# Check if table exists
exists = adapter.table_exists("sales")

# Get table schema
schema_df = adapter.get_table_info("sales")

# Get row count
count = adapter.get_row_count("sales")
```

#### Configuration

Uses settings from `app/core/config.py`:

```python
DATABASE_URL = "sqlite:///./tellius_feed.db"
QUERY_TIMEOUT = 30  # seconds
MAX_QUERY_ROWS = 1000000
```

#### Error Handling

Raises `QueryExecutionError` with:
- `message`: Error description
- `query_name`: Which query failed
- `original_error`: Original exception for debugging

Common errors:
- Connection failure
- SQL syntax error
- Table not found
- Query timeout
- Row limit exceeded

#### Connection Management

Uses context manager for safe connection handling:

```python
with self._get_connection() as conn:
    # Execute queries
    # Connection automatically closed on exit
```

Features:
- Automatic connection cleanup
- Foreign key enforcement
- Row factory for dict-like results
- Configurable timeout

---

## Integration Example

Complete workflow using all three services:

```python
from app.services.bv_context_builder import BVContextBuilder
from app.services.tql_planner import TQLPlanner
from app.services.plan_validator import PlanValidator
from app.services.tql_adapter import TQLAdapter

# 1. Build BV context
bv_context = BVContextBuilder.build(business_view)

# 2. Generate plan
plan = TQLPlanner.generate(intent, business_view)

# 3. Validate plan
validated_plan = PlanValidator.validate(plan, bv_context)

# 4. Execute plan
adapter = TQLAdapter()
results = adapter.execute(validated_plan)

# 5. Use results
current = results.get_current_value()
baseline = results.get_baseline_value()

if baseline:
    change = current - baseline
    pct_change = (change / baseline) * 100
    print(f"Metric changed by {pct_change:+.1f}%")
```

## Testing

Comprehensive test suite in `tests/test_tql_services_integration.py`:

```bash
# Run all TQL service tests
pytest tests/test_tql_services_integration.py -v

# Run specific test class
pytest tests/test_tql_services_integration.py::TestTQLPlanner -v

# Run with coverage
pytest tests/test_tql_services_integration.py --cov=app.services
```

Test coverage includes:
- ✓ Basic plan generation
- ✓ Filter application
- ✓ Baseline comparison
- ✓ Time-series queries
- ✓ Dimensional breakdown
- ✓ Security validation
- ✓ SQL injection detection
- ✓ Database execution
- ✓ Error handling
- ✓ Full integration pipeline

## Example Usage

See `examples/tql_services_example.py` for a complete working example:

```bash
cd backend
python -m examples.tql_services_example
```

## Performance Considerations

**TQLPlanner**:
- Complexity: O(n) where n = number of dimensions
- Typical execution: < 10ms
- No external dependencies

**PlanValidator**:
- Complexity: O(m) where m = total query length
- Typical execution: < 5ms
- Regex-based validation (room for optimization with SQL parser)

**TQLAdapter**:
- Complexity: Depends on query complexity and data volume
- Typical execution: < 1s for simple aggregations
- Configurable timeout (default 30s)
- Row limit enforced (default 1M rows)

## Security Best Practices

1. **Always validate plans** before execution
2. **Never bypass** the validation layer
3. **Use parameterized queries** when adding user input (though current implementation uses pre-built queries)
4. **Limit query complexity** through complexity scoring
5. **Enforce timeouts** to prevent runaway queries
6. **Log all queries** for audit trail
7. **Restrict database permissions** to SELECT only

## Production Deployment

For production use:

1. **Replace SQLite** with production database (PostgreSQL, etc.)
2. **Implement connection pooling** for better performance
3. **Add query caching** for repeated queries
4. **Use SQL parser** instead of regex for validation
5. **Implement query plan caching** to avoid regeneration
6. **Add monitoring** for query performance
7. **Set up alerting** for validation failures

## Future Enhancements

- [ ] Support for more complex subqueries
- [ ] CTEs (Common Table Expressions) support
- [ ] Query optimization hints
- [ ] Parallel query execution
- [ ] Query result caching
- [ ] Support for window functions
- [ ] Advanced time zone handling
- [ ] Query plan visualization
- [ ] Performance profiling
- [ ] Database-agnostic dialect support

## Troubleshooting

### Common Issues

**1. "Measure not found" error**
- Verify measure name matches Business View exactly (case-sensitive)
- Check that Business View is properly initialized

**2. "Validation failed: Invalid column"**
- Column references must match Business View whitelist
- Use fully qualified names (table.column)

**3. "Query execution failed: no such table"**
- Database not initialized with proper schema
- Table names in queries don't match database

**4. "Query timeout"**
- Increase `QUERY_TIMEOUT` setting
- Optimize query or add indexes
- Reduce time range or add filters

**5. Empty results**
- Check time range matches data
- Verify filters are not too restrictive
- Check JOIN conditions

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This will show:
- Generated SQL queries
- Validation steps
- Query execution details
- Connection information
- Error stack traces

## Support

For issues or questions:
1. Check ARCHITECTURE.md for system design
2. Review test cases for examples
3. Enable debug logging for diagnostics
4. Check generated SQL queries for correctness
